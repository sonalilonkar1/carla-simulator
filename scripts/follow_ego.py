#!/usr/bin/env python3

import argparse
import time

import carla


EGO_ROLE = "hero"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Smoothly follow the CARLA ego vehicle."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    return parser.parse_args()


def find_ego_vehicle(world):
    vehicles = world.get_actors().filter("vehicle.*")

    ego_vehicles = [
        vehicle
        for vehicle in vehicles
        if vehicle.attributes.get("role_name") == EGO_ROLE
        and vehicle.is_alive
    ]

    if not ego_vehicles:
        return None

    # Use the lowest actor ID if more than one hero exists.
    return sorted(ego_vehicles, key=lambda vehicle: vehicle.id)[0]


def main():
    args = parse_args()

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)

    world = client.get_world()
    spectator = world.get_spectator()

    current_location = None
    current_rotation = None
    last_message_time = 0.0
    followed_vehicle_id = None

    print(f"Waiting for vehicle with role_name='{EGO_ROLE}'...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            ego = find_ego_vehicle(world)

            if ego is None:
                now = time.monotonic()

                if now - last_message_time > 2.0:
                    print(
                        f"Waiting for role_name='{EGO_ROLE}'...",
                        flush=True,
                    )
                    last_message_time = now

                current_location = None
                current_rotation = None
                followed_vehicle_id = None

                time.sleep(0.1)
                continue

            if ego.id != followed_vehicle_id:
                print(
                    f"Following ego vehicle {ego.id} "
                    f"(role_name='{EGO_ROLE}')"
                )
                followed_vehicle_id = ego.id

            vehicle_transform = ego.get_transform()
            vehicle_location = vehicle_transform.location
            vehicle_rotation = vehicle_transform.rotation
            forward = vehicle_transform.get_forward_vector()

            # Third-person camera: behind, above, and looking forward.
            desired_location = carla.Location(
                x=vehicle_location.x - forward.x * 8.0,
                y=vehicle_location.y - forward.y * 8.0,
                z=vehicle_location.z + 4.0,
            )

            desired_rotation = carla.Rotation(
                pitch=-12.0,
                yaw=vehicle_rotation.yaw,
                roll=0.0,
            )

            # Smooth camera movement.
            smoothing = 0.15

            if current_location is None:
                current_location = desired_location
                current_rotation = desired_rotation
            else:
                current_location.x += (
                    desired_location.x - current_location.x
                ) * smoothing
                current_location.y += (
                    desired_location.y - current_location.y
                ) * smoothing
                current_location.z += (
                    desired_location.z - current_location.z
                ) * smoothing

                current_rotation.pitch += (
                    desired_rotation.pitch
                    - current_rotation.pitch
                ) * smoothing

                current_rotation.yaw += (
                    desired_rotation.yaw
                    - current_rotation.yaw
                ) * smoothing

            spectator.set_transform(
                carla.Transform(
                    current_location,
                    current_rotation,
                )
            )

            time.sleep(1.0 / 30.0)

    except KeyboardInterrupt:
        print("\nVehicle-follow camera stopped.")


if __name__ == "__main__":
    main()
