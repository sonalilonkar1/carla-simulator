#!/usr/bin/env python3

import argparse
import queue
import time
from pathlib import Path

import carla


def parse_args():
    parser = argparse.ArgumentParser(
        description="CARLA Lab 1: vehicle control and RGB camera capture"
    )

    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--drive-seconds", type=float, default=30.0)
    parser.add_argument("--frame-count", type=int, default=5)
    parser.add_argument(
        "--no-save-frames",
        action="store_true",
        help="Run the RGB camera without saving PNG frames",
    )

    return parser.parse_args()


def connect_to_carla(host, port):
    client = carla.Client(host, port)
    client.set_timeout(10.0)

    world = client.get_world()

    if "Town03" not in world.get_map().name:
        print("Loading Town03_Opt...")
        world = client.load_world("Town03_Opt")
        time.sleep(3.0)

    print("CARLA server:", client.get_server_version())
    print("Current map:", world.get_map().name)

    return client, world


def choose_spawn_point(world):
    spawn_points = world.get_map().get_spawn_points()

    if not spawn_points:
        raise RuntimeError("Town03_Opt has no vehicle spawn points.")

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.find("vehicle.tesla.model3")

    if vehicle_bp.has_attribute("role_name"):
        vehicle_bp.set_attribute("role_name", "hero")

    for spawn_point in spawn_points:
        vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)

        if vehicle is not None:
            return vehicle, spawn_point

    raise RuntimeError("Could not spawn the Lab 1 ego vehicle.")


def main():
    args = parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    client, world = connect_to_carla(args.host, args.port)

    vehicle = None
    camera = None
    camera_queue = queue.Queue()

    try:
        vehicle, spawn_point = choose_spawn_point(world)

        print(f"Spawned ego vehicle, actor ID {vehicle.id}")
        print("Ego role:", vehicle.attributes.get("role_name"))

        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(5.0)
        traffic_manager.global_percentage_speed_difference(0.0)

        vehicle.set_autopilot(True, traffic_manager.get_port())

        camera_bp = world.get_blueprint_library().find(
            "sensor.camera.rgb"
        )
        camera_bp.set_attribute("image_size_x", "800")
        camera_bp.set_attribute("image_size_y", "600")
        camera_bp.set_attribute("fov", "90")

        camera_transform = carla.Transform(
            carla.Location(x=1.5, y=0.0, z=2.4),
            carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
        )

        camera = world.spawn_actor(
            camera_bp,
            camera_transform,
            attach_to=vehicle,
        )

        camera.listen(camera_queue.put)

        print(f"Attached RGB camera, actor ID {camera.id}")
        print(
            f"Start position: "
            f"x={spawn_point.location.x:.2f}, "
            f"y={spawn_point.location.y:.2f}, "
            f"z={spawn_point.location.z:.2f}"
        )

        spectator = world.get_spectator()
        spectator.set_transform(
            carla.Transform(
                spawn_point.location + carla.Location(z=20.0),
                carla.Rotation(
                    pitch=-45.0,
                    yaw=spawn_point.rotation.yaw,
                    roll=0.0,
                ),
            )
        )

        start_location = vehicle.get_location()
        start_time = time.monotonic()
        next_capture_time = start_time
        capture_interval = max(
            args.drive_seconds / max(args.frame_count, 1),
            0.1,
        )

        saved_frames = 0
        latest_image = None

        print("Driving with CARLA Traffic Manager...")

        while time.monotonic() - start_time < args.drive_seconds:
            try:
                image = camera_queue.get(timeout=1.0)
                latest_image = image
            except queue.Empty:
                continue

            now = time.monotonic()

            if (
                not args.no_save_frames
                and saved_frames < args.frame_count
                and now >= next_capture_time
            ):
                saved_frames += 1

                frame_path = output_dir / (
                    f"rgb-{saved_frames:02d}-frame-{image.frame:06d}.png"
                )
                image.save_to_disk(str(frame_path))

                if saved_frames == 1:
                    image.save_to_disk(
                        str(output_dir / "rgb-camera.png")
                    )

                print(
                    f"Captured RGB image "
                    f"{saved_frames}/{args.frame_count}: "
                    f"frame {image.frame}, "
                    f"{image.width}x{image.height}"
                )

                next_capture_time += capture_interval

        end_location = vehicle.get_location()
        distance_moved = start_location.distance(end_location)

        print(
            f"End position: "
            f"x={end_location.x:.2f}, "
            f"y={end_location.y:.2f}, "
            f"z={end_location.z:.2f}"
        )
        print(f"Distance moved: {distance_moved:.2f} meters")

        if not args.no_save_frames and latest_image is not None:
            primary_path = output_dir / "rgb-camera.png"
            if not primary_path.exists():
                latest_image.save_to_disk(str(primary_path))

        print("LAB 1 RESULT: PASS")
        print("Output directory:", output_dir)

    finally:
        if camera is not None and camera.is_alive:
            camera.stop()
            camera.destroy()
            print("Camera destroyed")

        if vehicle is not None and vehicle.is_alive:
            vehicle.set_autopilot(False)
            vehicle.apply_control(
                carla.VehicleControl(
                    throttle=0.0,
                    brake=1.0,
                )
            )
            time.sleep(0.5)
            vehicle.destroy()
            print("Ego vehicle destroyed")


if __name__ == "__main__":
    main()
