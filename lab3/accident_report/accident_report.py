#!/usr/bin/env python3
"""CMPE 281 CARLA Lab 3: detect a collision and write an incident report."""

import argparse
import csv
import json
import math
import os
import queue
import shutil
from pathlib import Path

import carla


TOWN03_LAYERS = (
    "Ground", "Buildings", "Walls", "Props", "StreetLights", "Decals",
    "ParkedVehicles", "Foliage", "Particles",
)


def speed_kmh(actor):
    velocity = actor.get_velocity()
    return 3.6 * math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)


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
    frames.mkdir(parents=True, exist_ok=True)

    client = carla.Client(args.host, args.port)
    client.set_timeout(60.0)
    world = None
    original_settings = None
    actors = []
    images = queue.Queue()
    collision_events = []
    telemetry = []
    collision_sensor = None
    ego = None

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
        if not 0 <= spawn_index < len(spawn_points):
            raise ValueError(f"spawn_index must be between 0 and {len(spawn_points)-1}")

        ego_transform = spawn_points[spawn_index]
        forward = ego_transform.get_forward_vector()
        start = ego_transform.location
        ego = world.try_spawn_actor(
            blueprints.find("vehicle.tesla.model3"), ego_transform
        )
        if ego is None:
            raise RuntimeError("Could not spawn the ego vehicle")
        actors.append(ego)

        obstacle_location = carla.Location(
            x=start.x + forward.x * float(config["obstacle_distance_m"]),
            y=start.y + forward.y * float(config["obstacle_distance_m"]),
            z=start.z + 0.35,
        )
        obstacle_transform = carla.Transform(obstacle_location, ego_transform.rotation)
        obstacle = world.try_spawn_actor(
            blueprints.find("vehicle.audi.tt"), obstacle_transform
        )
        if obstacle is None:
            raise RuntimeError("Could not spawn the stopped vehicle")
        actors.append(obstacle)

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

        collision_sensor = world.spawn_actor(
            blueprints.find("sensor.other.collision"), carla.Transform(), attach_to=ego
        )
        actors.append(collision_sensor)

        def on_collision(event):
            other = event.other_actor
            impulse = event.normal_impulse
            collision_events.append({
                "frame": int(event.frame),
                "timestamp_s": round(float(event.timestamp), 3),
                "other_actor_id": int(other.id),
                "other_actor_type": other.type_id,
                "ego_location_at_event": {
                    "x": round(ego.get_location().x, 3),
                    "y": round(ego.get_location().y, 3),
                    "z": round(ego.get_location().z, 3),
                },
                "normal_impulse": {
                    "x": round(impulse.x, 3),
                    "y": round(impulse.y, 3),
                    "z": round(impulse.z, 3),
                    "magnitude": round(math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2), 3),
                },
                "ego_speed_kmh": round(speed_kmh(ego), 3),
            })

        collision_sensor.listen(on_collision)

        ego.apply_control(carla.VehicleControl(brake=1.0))
        obstacle.apply_control(carla.VehicleControl(hand_brake=True))
        for _ in range(10):
            world.tick()
        while not images.empty():
            images.get_nowait()

        dt = float(config["fixed_delta_seconds"])
        total_ticks = int(float(config["simulation_seconds"]) / dt)
        post_ticks = int(float(config["post_collision_seconds"]) / dt)
        capture_every = max(1, round((1.0 / float(config["camera_fps"])) / dt))
        frames_saved = 0
        last_image_frame = None
        phase = "APPROACH"

        print(f"Scenario: {config['scenario_name']}", flush=True)
        print(f"Map: {current_map}; spawn index: {spawn_index}", flush=True)
        print(f"Ego actor: {ego.id}; obstacle actor: {obstacle.id}", flush=True)
        print(f"Obstacle distance: {config['obstacle_distance_m']} m", flush=True)

        for tick in range(total_ticks):
            if collision_events and phase == "APPROACH":
                phase = "POST_COLLISION"
                print(f"Collision detected at simulation tick {tick}", flush=True)

            if phase == "APPROACH":
                ego.apply_control(carla.VehicleControl(
                    throttle=float(config["initial_throttle"]), brake=0.0
                ))
            else:
                ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))

            frame = world.tick()
            separation = distance(ego.get_location(), obstacle.get_location())
            telemetry.append({
                "tick": tick,
                "frame": frame,
                "sim_time_s": round(tick * dt, 3),
                "phase": phase,
                "distance_m": round(separation, 3),
                "ego_speed_kmh": round(speed_kmh(ego), 3),
                "collision_count": len(collision_events),
            })

            if tick % capture_every == 0:
                try:
                    image = images.get(timeout=30.0 if frames_saved == 0 else 5.0)
                    if image.frame != last_image_frame:
                        image.save_to_disk(str(frames / f"frame-{frames_saved:06d}.png"))
                        frames_saved += 1
                        last_image_frame = image.frame
                except queue.Empty:
                    print(f"WARNING: camera timeout after simulator frame {frame}", flush=True)

            if phase == "POST_COLLISION" and collision_events:
                collision_tick = collision_events[0]["frame"]
                if frame >= collision_tick + post_ticks:
                    break

        ego.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        world.tick()
        collision_count = len(collision_events)
        detected = collision_count >= int(config["minimum_collision_events"])
        status = "PASS" if detected and frames_saved > 0 else "FAIL"

        incident_report = {
            "report_type": "CARLA collision incident",
            "scenario": config["scenario_name"],
            "map": current_map,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "ego_actor_id": ego.id,
            "obstacle_actor_id": obstacle.id,
            "collision_detected": detected,
            "collision_count": collision_count,
            "events": collision_events,
            "evidence": {
                "frames_directory": str(frames),
                "telemetry_file": str(output / "telemetry.csv"),
            },
        }
        result = {
            "scenario": config["scenario_name"],
            "status": status,
            "map": current_map,
            "spawn_index": spawn_index,
            "ego_actor_id": ego.id,
            "obstacle_actor_id": obstacle.id,
            "collision_detected": detected,
            "collision_count": collision_count,
            "frames_saved": frames_saved,
        }
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        (output / "incident_report.json").write_text(json.dumps(incident_report, indent=2) + "\n")
        with (output / "telemetry.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=telemetry[0].keys())
            writer.writeheader()
            writer.writerows(telemetry)
        if frames_saved:
            shutil.copy2(sorted(frames.glob("frame-*.png"))[frames_saved // 2], output / "preview.png")

        print(json.dumps(result, indent=2), flush=True)
        print(f"LAB 3 RESULT: {status}", flush=True)
        if status != "PASS":
            raise RuntimeError("Accident was not detected or visual evidence was not saved")
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
