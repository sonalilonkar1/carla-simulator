#!/usr/bin/env python3
"""CMPE 281 CARLA Lab 2B: pedestrian crossing and emergency braking."""

import argparse
import csv
import json
import math
import queue
import shutil
from pathlib import Path

import carla


TOWN03_LAYERS = (
    "Ground",
    "Buildings",
    "Walls",
    "Props",
    "StreetLights",
    "Decals",
    "ParkedVehicles",
    "Foliage",
    "Particles",
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def speed_kmh(actor):
    velocity = actor.get_velocity()
    return 3.6 * math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def dot_2d(vector, axis):
    return vector.x * axis.x + vector.y * axis.y


def offset_location(origin, forward, right, longitudinal_m, lateral_m, z_offset=0.0):
    return carla.Location(
        x=origin.x + forward.x * longitudinal_m + right.x * lateral_m,
        y=origin.y + forward.y * longitudinal_m + right.y * lateral_m,
        z=origin.z + z_offset,
    )


def load_requested_world(client, requested_map):
    """Load Town03_Opt in stages to avoid CARLA's bulk-layer render crash."""
    current_world = client.get_world()
    current_map = current_world.get_map().name.split("/")[-1]
    if current_map == requested_map:
        return current_world

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


def main():
    args = parse_args()
    config = json.loads(Path(args.config).read_text())
    output_dir = Path(args.output_dir)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    client = carla.Client(args.host, args.port)
    client.set_timeout(60.0)
    world = client.get_world()
    original_settings = None
    actors = []
    camera_queue = queue.Queue()
    collisions = []
    telemetry = []
    result = {"scenario": config["scenario_name"], "status": "FAIL"}

    try:
        world = load_requested_world(client, config["map"])
        original_settings = world.get_settings()
        current_map = world.get_map().name.split("/")[-1]
        if current_map != config["map"]:
            raise RuntimeError(
                f"Server is on {current_map}, but config requests {config['map']}."
            )

        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = float(config["fixed_delta_seconds"])
        settings.no_rendering_mode = False
        world.apply_settings(settings)

        blueprints = world.get_blueprint_library()
        spawn_points = world.get_map().get_spawn_points()
        spawn_index = int(config["spawn_index"])
        if not 0 <= spawn_index < len(spawn_points):
            raise ValueError(f"spawn_index must be between 0 and {len(spawn_points) - 1}")

        ego_transform = spawn_points[spawn_index]
        forward = ego_transform.get_forward_vector()
        right = ego_transform.get_right_vector()
        ego_start = ego_transform.location

        ego = world.try_spawn_actor(
            blueprints.find("vehicle.tesla.model3"), ego_transform
        )
        if ego is None:
            raise RuntimeError(f"Could not spawn ego vehicle at index {spawn_index}")
        actors.append(ego)

        walker_candidates = blueprints.filter("walker.pedestrian.*")
        if not walker_candidates:
            raise RuntimeError("No pedestrian blueprints are available")
        walker_bp = walker_candidates[int(config["walker_blueprint_index"]) % len(walker_candidates)]
        if walker_bp.has_attribute("is_invincible"):
            walker_bp.set_attribute("is_invincible", "false")
        walker_location = offset_location(
            ego_start,
            forward,
            right,
            float(config["pedestrian_longitudinal_m"]),
            float(config["pedestrian_start_lateral_m"]),
            float(config["pedestrian_z_offset_m"]),
        )
        walker_transform = carla.Transform(walker_location, ego_transform.rotation)
        walker = world.try_spawn_actor(walker_bp, walker_transform)
        if walker is None:
            raise RuntimeError("Could not spawn pedestrian at the configured location")
        actors.append(walker)

        camera_bp = blueprints.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", str(config["image_width"]))
        camera_bp.set_attribute("image_size_y", str(config["image_height"]))
        camera_bp.set_attribute("fov", str(config["camera_fov"]))
        camera_bp.set_attribute("sensor_tick", str(1.0 / float(config["camera_fps"])))
        camera = world.spawn_actor(
            camera_bp,
            carla.Transform(
                carla.Location(x=-6.0, z=3.0),
                carla.Rotation(pitch=-12.0),
            ),
            attach_to=ego,
        )
        actors.append(camera)
        camera.listen(camera_queue.put)

        collision = world.spawn_actor(
            blueprints.find("sensor.other.collision"), carla.Transform(), attach_to=ego
        )
        actors.append(collision)
        collision.listen(lambda event: collisions.append(event))

        ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        walker.apply_control(carla.WalkerControl(direction=carla.Vector3D(), speed=0.0))
        for _ in range(10):
            world.tick()
        while True:
            try:
                camera_queue.get_nowait()
            except queue.Empty:
                break

        initial_distance = distance(ego.get_location(), walker.get_location())
        tick_count = int(
            float(config["simulation_seconds"]) / float(config["fixed_delta_seconds"])
        )
        capture_every = max(
            1,
            round((1.0 / float(config["camera_fps"])) / float(config["fixed_delta_seconds"])),
        )
        crossing_direction = carla.Vector3D(x=-right.x, y=-right.y, z=0.0)
        hazard_detected = False
        minimum_distance = float("inf")
        minimum_abs_lateral = float("inf")
        minimum_path_lateral = float("inf")
        saved_frames = 0
        last_image_frame = None
        consecutive_camera_timeouts = 0

        print(f"Scenario: {config['scenario_name']}", flush=True)
        print(f"Map: {current_map}; spawn index: {spawn_index}", flush=True)
        print(f"Ego actor: {ego.id}; pedestrian actor: {walker.id}", flush=True)
        print(
            f"Initial ego-pedestrian distance: {initial_distance:.2f} m; "
            f"pedestrian lateral offset: {config['pedestrian_start_lateral_m']} m",
            flush=True,
        )

        for tick in range(tick_count):
            walker.apply_control(
                carla.WalkerControl(
                    direction=crossing_direction,
                    speed=float(config["pedestrian_speed_mps"]),
                )
            )

            ego_location = ego.get_location()
            walker_location = walker.get_location()
            relative = walker_location - ego_location
            relative_to_path = walker_location - ego_start
            longitudinal = dot_2d(relative, forward)
            lateral = dot_2d(relative, right)
            path_lateral = dot_2d(relative_to_path, right)
            separation = distance(ego_location, walker_location)
            velocity = speed_kmh(ego)
            minimum_distance = min(minimum_distance, separation)
            minimum_abs_lateral = min(minimum_abs_lateral, abs(lateral))
            minimum_path_lateral = min(minimum_path_lateral, path_lateral)

            in_hazard_zone = (
                0.0 < longitudinal <= float(config["brake_trigger_longitudinal_m"])
                and abs(lateral) <= float(config["hazard_lateral_half_width_m"])
            )
            if hazard_detected or in_hazard_zone:
                hazard_detected = True
                ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
                action = "BRAKE"
            else:
                ego.apply_control(
                    carla.VehicleControl(
                        throttle=float(config["initial_throttle"]), brake=0.0
                    )
                )
                action = "DRIVE"

            frame = world.tick()
            telemetry.append(
                {
                    "tick": tick,
                    "frame": frame,
                    "sim_time_s": round(tick * float(config["fixed_delta_seconds"]), 3),
                    "distance_m": round(separation, 3),
                    "longitudinal_m": round(longitudinal, 3),
                    "lateral_m": round(lateral, 3),
                    "path_lateral_m": round(path_lateral, 3),
                    "speed_kmh": round(velocity, 3),
                    "action": action,
                }
            )

            if tick % capture_every == 0:
                try:
                    timeout_seconds = 30.0 if saved_frames == 0 else 5.0
                    image = camera_queue.get(timeout=timeout_seconds)
                except queue.Empty as exc:
                    consecutive_camera_timeouts += 1
                    print(
                        "WARNING: RGB camera frame delayed after simulation "
                        f"frame {frame} (timeout {consecutive_camera_timeouts}/3)",
                        flush=True,
                    )
                    if consecutive_camera_timeouts >= 3:
                        raise RuntimeError(
                            "RGB camera failed after three consecutive capture attempts"
                        ) from exc
                    continue
                consecutive_camera_timeouts = 0
                if image.frame == last_image_frame:
                    continue
                last_image_frame = image.frame
                saved_frames += 1
                image.save_to_disk(str(frames_dir / f"frame-{saved_frames:06d}.png"))

        ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        walker.apply_control(carla.WalkerControl(direction=carla.Vector3D(), speed=0.0))
        world.tick()
        final_speed = speed_kmh(ego)
        collision_count = len(collisions)
        pedestrian_crossed = minimum_path_lateral <= float(
            config["crossing_complete_lateral_m"]
        )
        passed = (
            hazard_detected
            and pedestrian_crossed
            and collision_count == 0
            and minimum_distance >= float(config["pass_min_distance_m"])
            and final_speed <= float(config["pass_max_final_speed_kmh"])
            and saved_frames > 0
        )

        result.update(
            {
                "status": "PASS" if passed else "FAIL",
                "map": current_map,
                "spawn_index": spawn_index,
                "ego_actor_id": ego.id,
                "pedestrian_actor_id": walker.id,
                "initial_distance_m": round(initial_distance, 3),
                "hazard_detected": hazard_detected,
                "pedestrian_crossed_path": pedestrian_crossed,
                "collisions": collision_count,
                "minimum_distance_m": round(minimum_distance, 3),
                "minimum_abs_lateral_m": round(minimum_abs_lateral, 3),
                "final_speed_kmh": round(final_speed, 3),
                "frames_saved": saved_frames,
            }
        )

        with (output_dir / "telemetry.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=telemetry[0].keys())
            writer.writeheader()
            writer.writerows(telemetry)
        (output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        if saved_frames:
            shutil.copyfile(frames_dir / "frame-000001.png", output_dir / "preview.png")

        print(json.dumps(result, indent=2), flush=True)
        print(f"LAB 2B RESULT: {result['status']}", flush=True)
        if not passed:
            raise RuntimeError("Pedestrian scenario did not satisfy pass conditions")
    finally:
        for actor in reversed(actors):
            try:
                if hasattr(actor, "stop"):
                    actor.stop()
                actor.destroy()
            except RuntimeError:
                pass
        if original_settings is not None:
            world.apply_settings(original_settings)
        print("Actors destroyed and original world settings restored", flush=True)


if __name__ == "__main__":
    main()
