"""SJSU single-map live demo.

Use this instead of the old scenario_test.py for the SJSU OpenDRIVE map.
The old script requires native CARLA traffic-light and stop-sign actors,
which are not reliably present in the imported SJSU OSM map.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import carla

from sjsu_map.carla_common import choose_spawn, connect, destroy_actors, load_sjsu_world
from sjsu_map.virtual_signal import SignalConfig, VirtualSignal


def args():
    p = argparse.ArgumentParser(description="Run a scenario on the SJSU CARLA map.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=2000)
    p.add_argument("--xodr", help="Path to maps/sjsu.xodr; omit if already loaded")
    p.add_argument("--config", default="sjsu_map/sjsu_config.json")
    p.add_argument("--spawn-index", type=int, default=None)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--log-file", default="outputs/sjsu-scenario.txt")
    p.add_argument(
        "--scenario",
        choices=("signal", "stopped_vehicle", "pedestrian"),
        default="signal",
    )
    return p.parse_args()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def spawn_ego(world, spawn):
    library = world.get_blueprint_library()
    blueprint = library.find("vehicle.tesla.model3")
    blueprint.set_attribute("role_name", "hero")

    points = [spawn] + world.get_map().get_spawn_points()
    existing = world.get_actors().filter("vehicle.*")

    for transform in points:
        if any(transform.location.distance(v.get_location()) < 5.0 for v in existing):
            continue
        vehicle = world.try_spawn_actor(blueprint, transform)
        if vehicle is not None:
            print(f"Spawned ego vehicle {vehicle.id}")
            return vehicle

    raise RuntimeError("Could not spawn ego vehicle. Try --spawn-index 1 or 2.")


def drive(vehicle, throttle=0.30):
    vehicle.apply_control(carla.VehicleControl(throttle=throttle, steer=0.0))


def brake(vehicle):
    vehicle.apply_control(carla.VehicleControl(brake=1.0, throttle=0.0))


def run_signal(world, vehicle, configuration, duration, log_file):
    signal = VirtualSignal(world, SignalConfig(**configuration["signal"]))
    previous_x = vehicle.get_location().x
    violation = False
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as log:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            signal.draw()
            if signal.crossed_during_red(vehicle, previous_x):
                message = "RED LIGHT VIOLATION: ego crossed during RED"
                print(message)
                log.write(message + "\n")
                violation = True
                brake(vehicle)
                break
            previous_x = vehicle.get_location().x
            drive(vehicle)
            time.sleep(0.05)

    print(f"TRAFFIC SIGNAL RESULT: {'VIOLATION' if violation else 'PASS'}")


def run_stopped_vehicle(world, vehicle, duration, log_file):
    points = world.get_map().get_spawn_points()
    if len(points) < 2:
        raise RuntimeError("At least two spawn points are required.")

    blueprint = world.get_blueprint_library().find("vehicle.audi.tt")
    obstacle = world.try_spawn_actor(blueprint, points[1])
    if obstacle is None:
        raise RuntimeError("Could not spawn stopped vehicle. Try another --spawn-index.")

    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w") as log:
            end = time.monotonic() + duration
            while time.monotonic() < end:
                distance = vehicle.get_location().distance(obstacle.get_location())
                if distance < 12.0:
                    brake(vehicle)
                    message = f"EMERGENCY BRAKING: stopped at {distance:.2f} m"
                    print(message)
                    log.write(message + "\n")
                    return
                drive(vehicle)
                time.sleep(0.05)
    finally:
        obstacle.destroy()


def run_pedestrian(world, vehicle, duration, log_file):
    walker_bp = world.get_blueprint_library().filter("walker.pedestrian.*")[0]
    location = vehicle.get_location() + carla.Location(x=8.0, y=3.0, z=0.5)
    walker = world.try_spawn_actor(walker_bp, carla.Transform(location))
    if walker is None:
        raise RuntimeError("Could not spawn pedestrian. Try another --spawn-index.")

    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w") as log:
            end = time.monotonic() + duration
            while time.monotonic() < end:
                distance = vehicle.get_location().distance(walker.get_location())
                if distance < 10.0:
                    brake(vehicle)
                    message = f"PEDESTRIAN SAFETY: braking at {distance:.2f} m"
                    print(message)
                    log.write(message + "\n")
                    return
                drive(vehicle)
                time.sleep(0.05)
    finally:
        walker.destroy()


def main():
    cli = args()
    configuration = load_json(cli.config)
    client = connect(cli.host, cli.port)
    world = load_sjsu_world(client, cli.xodr)
    index = cli.spawn_index if cli.spawn_index is not None else configuration["spawn_index"]
    spawn = choose_spawn(world, index)
    ego = spawn_ego(world, spawn)
    spectator = world.get_spectator()
    spectator.set_transform(carla.Transform(spawn.location + carla.Location(z=15), spawn.rotation))

    try:
        if cli.scenario == "signal":
            run_signal(world, ego, configuration, cli.duration, cli.log_file)
        elif cli.scenario == "stopped_vehicle":
            run_stopped_vehicle(world, ego, cli.duration, cli.log_file)
        else:
            run_pedestrian(world, ego, cli.duration, cli.log_file)
    finally:
        brake(ego)
        time.sleep(0.5)
        destroy_actors([ego])
        print("SJSU scenario finished")


if __name__ == "__main__":
    main()
