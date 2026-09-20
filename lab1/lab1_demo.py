#!/usr/bin/env python3
"""CMPE 281 CARLA Lab 1: spawn, drive, capture one RGB frame, and clean up."""

import argparse
import math
import shutil
import threading
import time
from pathlib import Path

import carla


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--drive-seconds", type=float, default=4.0)
    parser.add_argument("--frame-count", type=int, default=5)
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / "rgb-camera.png"

    client = carla.Client(args.host, args.port)
    client.set_timeout(30.0)
    world = client.get_world()
    blueprints = world.get_blueprint_library()
    vehicle = None
    camera = None
    images_ready = threading.Event()
    image_lock = threading.Lock()
    captured_paths = []

    def save_frame(image):
        with image_lock:
            if len(captured_paths) >= args.frame_count:
                return
            number = len(captured_paths) + 1
            frame_path = output_dir / f"rgb-{number:02d}-frame-{image.frame:06d}.png"
            image.save_to_disk(str(frame_path))
            captured_paths.append(frame_path)
            if number == 1:
                shutil.copyfile(frame_path, image_path)
            print(
                f"Captured RGB image {number}/{args.frame_count}: "
                f"frame {image.frame}, {image.width}x{image.height}",
                flush=True,
            )
            if number == args.frame_count:
                images_ready.set()

    try:
        print(f"Server version: {client.get_server_version()}", flush=True)
        print(f"Current map: {world.get_map().name}", flush=True)

        vehicle_bp = blueprints.find("vehicle.tesla.model3")
        for spawn_point in world.get_map().get_spawn_points():
            vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
            if vehicle is not None:
                break
        if vehicle is None:
            raise RuntimeError("No available vehicle spawn point")
        print(f"Spawned {vehicle.type_id}, actor ID {vehicle.id}", flush=True)

        camera_bp = blueprints.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", "800")
        camera_bp.set_attribute("image_size_y", "600")
        camera_bp.set_attribute("fov", "90")
        camera_bp.set_attribute("sensor_tick", "0.5")
        camera_transform = carla.Transform(
            carla.Location(x=1.5, z=2.4),
            carla.Rotation(pitch=-8.0),
        )
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        camera.listen(save_frame)
        print(f"Attached RGB camera, actor ID {camera.id}", flush=True)

        # Wait for authoritative simulator state before measuring the start point.
        world.wait_for_tick(10.0)
        start = vehicle.get_location()
        print(f"Start position: x={start.x:.2f}, y={start.y:.2f}, z={start.z:.2f}", flush=True)

        vehicle.apply_control(carla.VehicleControl(throttle=0.35, steer=0.0))
        time.sleep(args.drive_seconds)
        vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        world.wait_for_tick(10.0)
        end = vehicle.get_location()
        distance = math.sqrt(
            (end.x - start.x) ** 2 + (end.y - start.y) ** 2 + (end.z - start.z) ** 2
        )
        print(f"End position: x={end.x:.2f}, y={end.y:.2f}, z={end.z:.2f}", flush=True)
        print(f"Distance moved: {distance:.2f} meters", flush=True)

        if not images_ready.wait(timeout=20.0):
            raise RuntimeError(
                f"Received {len(captured_paths)}/{args.frame_count} RGB images"
            )
        if not image_path.is_file() or image_path.stat().st_size == 0:
            raise RuntimeError("RGB output file was not created correctly")
        print(f"Primary image saved: {image_path}", flush=True)
        print(f"Image sequence saved: {len(captured_paths)} frames", flush=True)
        print("LAB 1 RESULT: PASS", flush=True)
    finally:
        if camera is not None:
            camera.stop()
            camera.destroy()
            print("Camera destroyed", flush=True)
        if vehicle is not None:
            vehicle.destroy()
            print("Vehicle destroyed", flush=True)


if __name__ == "__main__":
    main()
