#!/usr/bin/env python3
"""CMPE 281 CARLA Lab 4: BasicAgent route navigation with RGB and LiDAR."""

import argparse
import csv
import json
import math
import queue
import shutil
from pathlib import Path

import carla
from agents.navigation.basic_agent import BasicAgent


TOWN03_LAYERS = (
    "Ground", "Buildings", "Walls", "Props", "StreetLights", "Decals",
    "ParkedVehicles", "Foliage", "Particles",
)


def speed_kmh(actor):
    v = actor.get_velocity()
    return 3.6 * math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def distance(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)


def load_requested_world(client, requested_map):
    current = client.get_world()
    current_map = current.get_map().name.split("/")[-1]
    if current_map == requested_map:
        return current
    if requested_map != "Town03_Opt":
        return client.load_world(requested_map)
    print("Loading Town03_Opt with MapLayer.NONE", flush=True)
    client.set_timeout(180.0)
    world = client.load_world("Town03_Opt", True, carla.MapLayer.NONE)
    for layer_name in TOWN03_LAYERS:
        print(f"Loading Town03 layer: {layer_name}", flush=True)
        world.load_map_layer(getattr(carla.MapLayer, layer_name))
    client.set_timeout(60.0)
    print("Town03 staged loading completed", flush=True)
    return world


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    config = json.loads(Path(args.config).read_text())
    output = Path(args.output_dir)
    frames = output / "frames"
    lidar_dir = output / "lidar"
    frames.mkdir(parents=True, exist_ok=True)
    lidar_dir.mkdir(parents=True, exist_ok=True)

    client = carla.Client(args.host, args.port)
    client.set_timeout(60.0)
    world = None
    original_settings = None
    actors = []
    images = queue.Queue()
    collisions = []
    telemetry = []
    saved_frames = 0
    saved_lidar = 0
    last_image_frame = None

    try:
        world = load_requested_world(client, config["map"])
        original_settings = world.get_settings()
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = float(config["fixed_delta_seconds"])
        settings.no_rendering_mode = False
        world.apply_settings(settings)

        current_map = world.get_map().name.split("/")[-1]
        if current_map != config["map"]:
            raise RuntimeError(f"Expected {config['map']}, but CARLA is on {current_map}")

        blueprints = world.get_blueprint_library()
        spawn_points = world.get_map().get_spawn_points()
        spawn_index = int(config["spawn_index"])
        destination_index = int(config["destination_index"])
        if not 0 <= spawn_index < len(spawn_points):
            raise ValueError(f"spawn_index must be between 0 and {len(spawn_points)-1}")
        if not 0 <= destination_index < len(spawn_points):
            raise ValueError(
                f"destination_index must be between 0 and {len(spawn_points)-1}"
            )
        if spawn_index == destination_index:
            raise ValueError("spawn_index and destination_index must differ")

        start_transform = spawn_points[spawn_index]
        destination = spawn_points[destination_index]
        ego = world.try_spawn_actor(
            blueprints.find("vehicle.tesla.model3"), start_transform
        )
        if ego is None:
            raise RuntimeError("Could not spawn the navigation vehicle")
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

        lidar_bp = blueprints.find("sensor.lidar.ray_cast")
        lidar_bp.set_attribute("range", str(config["lidar_range_m"]))
        lidar_bp.set_attribute("channels", str(config["lidar_channels"]))
        lidar_bp.set_attribute("points_per_second", str(config["lidar_points_per_second"]))
        lidar_bp.set_attribute("rotation_frequency", str(config["lidar_fps"]))
        lidar_bp.set_attribute("upper_fov", "10.0")
        lidar_bp.set_attribute("lower_fov", "-30.0")
        lidar_bp.set_attribute("sensor_tick", str(1.0 / float(config["lidar_fps"])))
        lidar = world.spawn_actor(
            lidar_bp,
            carla.Transform(carla.Location(z=2.2)),
            attach_to=ego,
        )
        actors.append(lidar)

        def save_lidar(measurement):
            nonlocal saved_lidar
            if saved_lidar >= int(config["max_lidar_scans"]):
                return
            measurement.save_to_disk(
                str(lidar_dir / f"scan-{saved_lidar:06d}-frame-{measurement.frame:06d}.ply")
            )
            saved_lidar += 1

        lidar.listen(save_lidar)

        collision_sensor = world.spawn_actor(
            blueprints.find("sensor.other.collision"), carla.Transform(), attach_to=ego
        )
        actors.append(collision_sensor)
        collision_sensor.listen(collisions.append)

        ego.apply_control(carla.VehicleControl(brake=1.0))
        for _ in range(10):
            world.tick()
        while not images.empty():
            images.get_nowait()

        agent = BasicAgent(ego, target_speed=float(config["target_speed_kmh"]))
        agent.set_destination(destination.location)

        dt = float(config["fixed_delta_seconds"])
        total_ticks = int(float(config["simulation_seconds"]) / dt)
        capture_every = max(1, round((1.0 / float(config["camera_fps"])) / dt))
        lidar_every = max(1, round((1.0 / float(config["lidar_fps"])) / dt))
        start_location = ego.get_location()
        closest_goal_distance = distance(start_location, destination.location)
        print(f"Scenario: {config['scenario_name']}", flush=True)
        print(f"Map: {current_map}; spawn index: {spawn_index}", flush=True)
        print(f"Destination index: {destination_index}", flush=True)
        print(f"Ego actor: {ego.id}; goal distance: {closest_goal_distance:.2f} m", flush=True)

        goal_reached = False
        for tick in range(total_ticks):
            if agent.done():
                goal_reached = True
                ego.apply_control(carla.VehicleControl(brake=1.0))
                phase = "GOAL_REACHED"
            else:
                control = agent.run_step()
                control.manual_gear_shift = False
                ego.apply_control(control)
                phase = "NAVIGATING"

            frame = world.tick()
            current_location = ego.get_location()
            goal_distance = distance(current_location, destination.location)
            closest_goal_distance = min(closest_goal_distance, goal_distance)
            telemetry.append({
                "tick": tick,
                "frame": frame,
                "sim_time_s": round(tick * dt, 3),
                "phase": phase,
                "goal_distance_m": round(goal_distance, 3),
                "speed_kmh": round(speed_kmh(ego), 3),
                "collision_count": len(collisions),
            })

            if tick % capture_every == 0:
                try:
                    image = images.get(timeout=30.0 if saved_frames == 0 else 5.0)
                    if image.frame != last_image_frame:
                        image.save_to_disk(str(frames / f"frame-{saved_frames:06d}.png"))
                        saved_frames += 1
                        last_image_frame = image.frame
                except queue.Empty:
                    print(f"WARNING: RGB camera timeout after frame {frame}", flush=True)

            if goal_reached:
                break

        # Continue braking after reaching the goal so the final
        # evaluation measures a stopped vehicle, not a moving vehicle.
        for _ in range(60):
            ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
            world.tick()

        final_distance = distance(ego.get_location(), destination.location)
        final_speed = speed_kmh(ego)
        progress = distance(start_location, ego.get_location())
        collision_count = len(collisions)
        goal_within_tolerance = final_distance <= float(config["goal_tolerance_m"])
        passed = (
            goal_reached
            and goal_within_tolerance
            and progress >= float(config["minimum_route_progress_m"])
            and collision_count == 0
            and final_speed <= 2.0
            and saved_frames > 0
            and saved_lidar > 0
        )
        result = {
            "scenario": config["scenario_name"],
            "status": "PASS" if passed else "FAIL",
            "map": current_map,
            "spawn_index": spawn_index,
            "destination_index": destination_index,
            "ego_actor_id": ego.id,
            "goal_reached": goal_reached,
            "goal_distance_m": round(final_distance, 3),
            "route_progress_m": round(progress, 3),
            "collisions": collision_count,
            "final_speed_kmh": round(final_speed, 3),
            "frames_saved": saved_frames,
            "lidar_scans_saved": saved_lidar,
        }
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        with (output / "telemetry.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=telemetry[0].keys())
            writer.writeheader()
            writer.writerows(telemetry)
        if saved_frames:
            shutil.copy2(sorted(frames.glob("frame-*.png"))[saved_frames // 2], output / "preview.png")
        print(json.dumps(result, indent=2), flush=True)
        print(f"LAB 4 RESULT: {result['status']}", flush=True)
        if not passed:
            raise RuntimeError("AI navigation did not reach the configured destination")
    finally:
        for actor in reversed(actors):
            try:
                if actor.type_id.startswith("sensor."):
                    actor.stop()
                actor.destroy()
            except RuntimeError:
                pass
        if world is not None and original_settings is not None:
            world.apply_settings(original_settings)
        print("Actors and world settings restored", flush=True)


if __name__ == "__main__":
    main()
