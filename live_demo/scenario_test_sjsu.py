"""Single-map SJSU live demonstration.

This intentionally does not search for native traffic-light actors. The SJSU
OSM conversion currently has no reliable native signal actors, so the traffic
signal lab uses a visible, deterministic virtual signal zone instead.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import carla

from sjsu_map.carla_common import choose_spawn, connect, destroy_actors, load_sjsu_world
from sjsu_map.virtual_signal import SignalConfig, VirtualSignal


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--xodr", help="SJSU .xodr file; omit if already loaded")
    parser.add_argument("--config", default="sjsu_map/sjsu_config.json")
    parser.add_argument(
        "--scenario",
        choices=["signal", "stopped_vehicle", "pedestrian", "collision", "navigation"],
        default="signal",
    )
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--spawn-index", type=int)
    parser.add_argument("--log-file", default="sjsu-violations.txt")
    return parser.parse_args()


def load_config(path: str):
    with open(path) as handle:
        return json.load(handle)


def spawn_vehicle(world, spawn):
    library = world.get_blueprint_library()
    bp = library.find("vehicle.tesla.model3")
    vehicle = world.try_spawn_actor(bp, spawn)
    if vehicle is None:
        raise RuntimeError("Could not spawn ego vehicle. Try another --spawn-index.")
    return vehicle


def drive_forward(vehicle, throttle=0.35):
    vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=0.0))


def brake(vehicle):
    vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))


def run_signal(world, vehicle, cfg, duration, log_file):
    signal_cfg = SignalConfig(**cfg["signal"])
    signal = VirtualSignal(world, signal_cfg)
    previous_x = vehicle.get_location().x
    violation = False
    with open(log_file, "w") as log:
        print("Virtual signal scenario started")
        end = time.monotonic() + duration
        while time.monotonic() < end:
            signal.draw()
            if signal.crossed_during_red(vehicle, previous_x):
                violation = True
                message = "TRAFFIC SIGNAL VIOLATION: crossed stop line during RED"
                print(message)
                log.write(message + "\n")
                brake(vehicle)
                break
            previous_x = vehicle.get_location().x
            drive_forward(vehicle)
            time.sleep(0.05)
    result = "VIOLATION" if violation else "PASS"
    print(f"TRAFFIC SIGNAL RESULT: {result}")


def run_stopped_vehicle(world, vehicle, duration, log_file):
    library = world.get_blueprint_library()
    points = world.get_map().get_spawn_points()
    if len(points) < 2:
        raise RuntimeError("The map needs at least two spawn points for this scenario.")
    obstacle = world.try_spawn_actor(library.find("vehicle.audi.tt"), points[1])
    if obstacle is None:
        raise RuntimeError("Could not spawn stopped vehicle; choose another spawn index.")
    try:
        with open(log_file, "w") as log:
            print(f"Stopped vehicle spawned with actor ID {obstacle.id}")
            start = time.monotonic()
            while time.monotonic() - start < duration:
                drive_forward(vehicle)
                distance = vehicle.get_location().distance(obstacle.get_location())
                if distance < 12.0:
                    brake(vehicle)
                    message = f"EMERGENCY BRAKING: stopped at {distance:.2f} m"
                    print(message)
                    log.write(message + "\n")
                    break
                time.sleep(0.05)
    finally:
        obstacle.destroy()


def run_pedestrian(world, vehicle, duration, log_file):
    library = world.get_blueprint_library()
    walker_bp = library.filter("walker.pedestrian.*")
    if not walker_bp:
        raise RuntimeError("No pedestrian blueprint is available.")
    loc = vehicle.get_location() + carla.Location(x=8.0, y=3.0, z=0.5)
    walker = world.try_spawn_actor(walker_bp[0], carla.Transform(loc))
    if walker is None:
        raise RuntimeError("Could not spawn pedestrian at the selected location.")
    try:
        with open(log_file, "w") as log:
            print(f"Pedestrian spawned with actor ID {walker.id}")
            start = time.monotonic()
            while time.monotonic() - start < duration:
                distance = vehicle.get_location().distance(walker.get_location())
                if distance < 10.0:
                    brake(vehicle)
                    message = f"PEDESTRIAN SAFETY: braking at {distance:.2f} m"
                    print(message)
                    log.write(message + "\n")
                    break
                drive_forward(vehicle)
                time.sleep(0.05)
    finally:
        walker.destroy()


def main():
    args = parse_args()
    cfg = load_config(args.config)
    client = connect(args.host, args.port)
    world = load_sjsu_world(client, args.xodr)
    spawn = choose_spawn(world, args.spawn_index if args.spawn_index is not None else cfg["spawn_index"])
    ego = spawn_vehicle(world, spawn)
    spectator = world.get_spectator()
    spectator.set_transform(carla.Transform(spawn.location + carla.Location(z=18), spawn.rotation))
    actors = [ego]
    print(f"Spawned SJSU ego vehicle {ego.id}")
    try:
        if args.scenario == "signal":
            run_signal(world, ego, cfg, args.duration, args.log_file)
        elif args.scenario == "stopped_vehicle":
            run_stopped_vehicle(world, ego, args.duration, args.log_file)
        elif args.scenario == "pedestrian":
            run_pedestrian(world, ego, args.duration, args.log_file)
        else:
            print(f"{args.scenario} scaffold selected; add its detector in this file.")
    finally:
        brake(ego)
        time.sleep(0.5)
        destroy_actors(actors)
        print("SJSU scenario finished")


if __name__ == "__main__":
    main()
