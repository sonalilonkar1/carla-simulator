#!/usr/bin/env python3
"""CMPE 281 CARLA Lab 2C: stop at red, proceed on green."""

import argparse
import csv
import json
import math
import queue
import shutil
from pathlib import Path

import carla

from discover_traffic_lights import TOWN03_LAYERS, approaches, load_world


def speed_kmh(actor):
    v = actor.get_velocity()
    return 3.6 * math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def dot_2d(vector, axis):
    return vector.x * axis.x + vector.y * axis.y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text())
    output = Path(args.output_dir)
    frames = output / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    client = carla.Client(args.host, args.port)
    client.set_timeout(60.0)
    world = None
    original_settings = None
    selected_light = None
    original_light_state = None
    actors = []
    images = queue.Queue()
    collisions = []
    telemetry = []

    try:
        world = load_world(client, config["map"])
        original_settings = world.get_settings()
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = float(config["fixed_delta_seconds"])
        settings.no_rendering_mode = False
        world.apply_settings(settings)

        candidates = approaches(world, float(config["approach_distance_m"]))
        index = int(config["candidate_index"])
        if not candidates:
            raise RuntimeError("No usable traffic-light approaches were found")
        if not 0 <= index < len(candidates):
            raise ValueError(f"candidate_index must be 0..{len(candidates)-1}")
        candidate = candidates[index]
        selected_light = world.get_actor(candidate["traffic_light_id"])
        if selected_light is None:
            raise RuntimeError("Selected traffic light disappeared")
        stop_wp = selected_light.get_stop_waypoints()[candidate["stop_waypoint_number"]]
        previous = stop_wp.previous(float(config["approach_distance_m"]))
        if not previous:
            raise RuntimeError("Could not reconstruct the selected approach waypoint")
        approach_wp = min(
            previous,
            key=lambda wp: 0 if (wp.road_id, wp.lane_id) == (stop_wp.road_id, stop_wp.lane_id) else 1,
        )
        spawn = approach_wp.transform
        spawn.location.z += 0.5
        forward = stop_wp.transform.get_forward_vector()
        stop_location = stop_wp.transform.location

        original_light_state = selected_light.get_state()
        selected_light.set_state(carla.TrafficLightState.Red)
        selected_light.freeze(True)

        blueprints = world.get_blueprint_library()
        ego = world.try_spawn_actor(blueprints.find("vehicle.tesla.model3"), spawn)
        if ego is None:
            raise RuntimeError(f"Could not spawn ego at traffic-light candidate {index}")
        actors.append(ego)

        camera_bp = blueprints.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", str(config["image_width"]))
        camera_bp.set_attribute("image_size_y", str(config["image_height"]))
        camera_bp.set_attribute("fov", str(config["camera_fov"]))
        camera_bp.set_attribute("sensor_tick", str(1.0 / float(config["camera_fps"])))
        camera = world.spawn_actor(
            camera_bp,
            carla.Transform(carla.Location(x=-6.0, z=3.0), carla.Rotation(pitch=-12.0)),
            attach_to=ego,
        )
        actors.append(camera)
        camera.listen(images.put)
        collision = world.spawn_actor(
            blueprints.find("sensor.other.collision"), carla.Transform(), attach_to=ego
        )
        actors.append(collision)
        collision.listen(collisions.append)

        ego.apply_control(carla.VehicleControl(brake=1.0))
        for _ in range(10):
            world.tick()
        while not images.empty():
            images.get_nowait()

        dt = float(config["fixed_delta_seconds"])
        ticks = int(float(config["simulation_seconds"]) / dt)
        capture_every = max(1, round((1.0 / float(config["camera_fps"])) / dt))
        hold_ticks_required = round(float(config["red_hold_seconds"]) / dt)
        phase = "APPROACH_RED"
        stopped_at_red = False
        crossed_on_red = False
        resumed_on_green = False
        passed_line_on_green = False
        red_hold_ticks = 0
        saved = 0
        min_abs_stop_distance = float("inf")
        max_green_speed = 0.0

        print(f"Scenario: {config['scenario_name']}")
        print(f"Map: {world.get_map().name.split('/')[-1]}; candidate: {index}")
        print(f"Traffic light: {selected_light.id}; ego: {ego.id}")
        print(f"Road: {stop_wp.road_id}; lane: {stop_wp.lane_id}")

        for tick in range(ticks):
            location = ego.get_location()
            signed_distance = dot_2d(stop_location - location, forward)
            velocity = speed_kmh(ego)
            min_abs_stop_distance = min(min_abs_stop_distance, abs(signed_distance))

            if phase == "APPROACH_RED":
                if signed_distance <= float(config["brake_trigger_distance_m"]):
                    phase = "STOP_RED"
                    ego.apply_control(carla.VehicleControl(brake=1.0))
                else:
                    ego.apply_control(carla.VehicleControl(throttle=float(config["initial_throttle"])))
            elif phase == "STOP_RED":
                ego.apply_control(carla.VehicleControl(brake=1.0))
                if signed_distance < -float(config["stop_tolerance_m"]):
                    crossed_on_red = True
                if velocity <= float(config["pass_max_stopped_speed_kmh"]):
                    stopped_at_red = True
                    red_hold_ticks += 1
                    if red_hold_ticks >= hold_ticks_required:
                        selected_light.set_state(carla.TrafficLightState.Green)
                        phase = "PROCEED_GREEN"
            else:
                ego.apply_control(carla.VehicleControl(throttle=float(config["initial_throttle"])))
                max_green_speed = max(max_green_speed, velocity)
                if velocity > 2.0:
                    resumed_on_green = True
                if signed_distance < -float(config["pass_distance_m"]):
                    passed_line_on_green = True

            frame = world.tick()
            telemetry.append({
                "tick": tick,
                "frame": frame,
                "sim_time_s": round(tick * dt, 3),
                "phase": phase,
                "light_state": str(selected_light.get_state()),
                "signed_stop_distance_m": round(signed_distance, 3),
                "speed_kmh": round(velocity, 3),
                "collisions": len(collisions),
            })
            if tick % capture_every == 0:
                try:
                    image = images.get(timeout=5.0)
                    image.save_to_disk(str(frames / f"frame-{saved:06d}.png"))
                    saved += 1
                except queue.Empty:
                    print(f"WARNING: camera timeout after frame {frame}", flush=True)

            if passed_line_on_green:
                break

        status = (
            stopped_at_red and not crossed_on_red and resumed_on_green
            and passed_line_on_green and len(collisions) == 0
        )
        result = {
            "scenario": config["scenario_name"],
            "status": "PASS" if status else "FAIL",
            "map": world.get_map().name.split("/")[-1],
            "candidate_index": index,
            "traffic_light_id": selected_light.id,
            "road_id": stop_wp.road_id,
            "lane_id": stop_wp.lane_id,
            "red_light_detected": True,
            "stopped_at_red": stopped_at_red,
            "crossed_on_red": crossed_on_red,
            "resumed_on_green": resumed_on_green,
            "passed_line_on_green": passed_line_on_green,
            "collisions": len(collisions),
            "minimum_abs_stop_distance_m": round(min_abs_stop_distance, 3),
            "maximum_green_speed_kmh": round(max_green_speed, 3),
            "frames_saved": saved,
        }
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        with (output / "telemetry.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=telemetry[0].keys())
            writer.writeheader()
            writer.writerows(telemetry)
        if saved:
            shutil.copy2(sorted(frames.glob("frame-*.png"))[len(list(frames.glob("frame-*.png"))) // 2], output / "preview.png")
        print(json.dumps(result, indent=2))
        print(f"LAB 2C RESULT: {result['status']}")
        if not status:
            raise RuntimeError("Traffic-signal scenario did not satisfy pass conditions")
    finally:
        for actor in reversed(actors):
            try:
                if actor.type_id.startswith("sensor."):
                    actor.stop()
                actor.destroy()
            except RuntimeError:
                pass
        if selected_light is not None:
            try:
                if original_light_state is not None:
                    selected_light.set_state(original_light_state)
                selected_light.freeze(False)
            except RuntimeError:
                pass
        if world is not None and original_settings is not None:
            world.apply_settings(original_settings)
        print("Actors, traffic light, and world settings restored", flush=True)


if __name__ == "__main__":
    main()
