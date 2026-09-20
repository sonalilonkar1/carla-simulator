#!/usr/bin/env python3
"""CMPE 281 CARLA practice: approach a stopped vehicle and brake safely.

The scenario is deterministic, records RGB frames and telemetry, monitors
collisions, and writes machine-readable results for grading or debugging.
"""

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


def find_forward_transform(world_map, start_transform, distance_m):
    """Place an obstacle on the ego vehicle's straight-line forward axis.

    This introductory scenario deliberately uses a straight controller with no
    steering. Following a curved waypoint would put the obstacle on a different
    trajectory, so the geometric forward vector is the correct reference.
    """
    del world_map  # Kept in the signature for future lane-following scenarios.
    forward = start_transform.get_forward_vector()
    start = start_transform.location
    return carla.Transform(
        carla.Location(
            x=start.x + forward.x * distance_m,
            y=start.y + forward.y * distance_m,
            z=start.z + 0.35,
        ),
        start_transform.rotation,
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
        requested_map = config["map"]
        if current_map != requested_map:
            raise RuntimeError(
                f"Server is on {current_map}, but config requests {requested_map}."
            )

        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = float(config["fixed_delta_seconds"])
        settings.no_rendering_mode = False
        world.apply_settings(settings)

        blueprint_library = world.get_blueprint_library()
        spawn_points = world.get_map().get_spawn_points()
        spawn_index = int(config["spawn_index"])
        if not 0 <= spawn_index < len(spawn_points):
            raise ValueError(f"spawn_index must be between 0 and {len(spawn_points) - 1}")

        ego_transform = spawn_points[spawn_index]
        ego_bp = blueprint_library.find("vehicle.tesla.model3")
        ego = world.try_spawn_actor(ego_bp, ego_transform)
        if ego is None:
            raise RuntimeError(f"Could not spawn ego vehicle at index {spawn_index}")
        actors.append(ego)

        obstacle_transform = find_forward_transform(
            world.get_map(), ego_transform, float(config["obstacle_distance_m"])
        )
        obstacle_bp = blueprint_library.find("vehicle.audi.tt")
        obstacle = world.try_spawn_actor(obstacle_bp, obstacle_transform)
        if obstacle is None:
            raise RuntimeError("Could not spawn the stopped obstacle vehicle")
        actors.append(obstacle)
        obstacle.apply_control(carla.VehicleControl(hand_brake=True))

        camera_bp = blueprint_library.find("sensor.camera.rgb")
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

        collision_bp = blueprint_library.find("sensor.other.collision")
        collision = world.spawn_actor(collision_bp, carla.Transform(), attach_to=ego)
        actors.append(collision)
        collision.listen(lambda event: collisions.append(event))

        # Newly spawned actors can temporarily report their uninitialized
        # origin (0, 0, 0). Advance the synchronous world while holding both
        # vehicles stationary before collecting safety metrics.
        ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        obstacle.apply_control(carla.VehicleControl(hand_brake=True))
        for _ in range(10):
            world.tick()
        while True:
            try:
                camera_queue.get_nowait()
            except queue.Empty:
                break

        tick_count = int(
            float(config["simulation_seconds"]) / float(config["fixed_delta_seconds"])
        )
        capture_every = max(
            1,
            round((1.0 / float(config["camera_fps"])) / float(config["fixed_delta_seconds"])),
        )
        brake_triggered = False
        minimum_distance = float("inf")
        saved_frames = 0
        last_image_frame = None
        consecutive_camera_timeouts = 0

        print(f"Scenario: {config['scenario_name']}", flush=True)
        print(f"Map: {current_map}; spawn index: {spawn_index}", flush=True)
        print(f"Ego actor: {ego.id}; obstacle actor: {obstacle.id}", flush=True)
        initialized_distance = distance(ego.get_location(), obstacle.get_location())
        print(
            "Initialized positions: "
            f"ego=({ego.get_location().x:.2f}, {ego.get_location().y:.2f}), "
            f"obstacle=({obstacle.get_location().x:.2f}, {obstacle.get_location().y:.2f}), "
            f"distance={initialized_distance:.2f} m",
            flush=True,
        )

        for tick in range(tick_count):
            ego_location = ego.get_location()
            obstacle_location = obstacle.get_location()
            separation = distance(ego_location, obstacle_location)
            velocity = speed_kmh(ego)
            minimum_distance = min(minimum_distance, separation)

            # Emergency braking is latched. Once the hazard is detected, the
            # controller must not resume throttle if distance later increases.
            if brake_triggered or separation <= float(config["brake_trigger_distance_m"]):
                ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
                brake_triggered = True
                action = "BRAKE"
            else:
                ego.apply_control(
                    carla.VehicleControl(throttle=float(config["initial_throttle"]), brake=0.0)
                )
                action = "DRIVE"

            frame = world.tick()
            telemetry.append(
                {
                    "tick": tick,
                    "frame": frame,
                    "sim_time_s": round(tick * float(config["fixed_delta_seconds"]), 3),
                    "distance_m": round(separation, 3),
                    "speed_kmh": round(velocity, 3),
                    "action": action,
                }
            )

            if tick % capture_every == 0:
                try:
                    # The first rendered frame can be slow on an HPC P100 while
                    # Unreal Engine initializes its rendering pipeline.
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
                            "RGB camera failed to deliver frames after three "
                            "consecutive capture attempts"
                        ) from exc
                    continue
                consecutive_camera_timeouts = 0
                if image.frame == last_image_frame:
                    continue
                last_image_frame = image.frame
                saved_frames += 1
                image.save_to_disk(str(frames_dir / f"frame-{saved_frames:06d}.png"))

        ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        world.tick()
        final_speed = speed_kmh(ego)
        collision_count = len(collisions)
        passed = (
            brake_triggered
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
                "obstacle_actor_id": obstacle.id,
                "initial_distance_m": round(initialized_distance, 3),
                "brake_triggered": brake_triggered,
                "collisions": collision_count,
                "minimum_distance_m": round(minimum_distance, 3),
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
        print(f"PRACTICE RESULT: {result['status']}", flush=True)
        if not passed:
            raise RuntimeError("Scenario did not satisfy the configured pass conditions")
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
