import argparse
import time

import carla


def parse_args():
    parser = argparse.ArgumentParser(description="Follow the CARLA ego vehicle live.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--distance", type=float, default=8.0)
    parser.add_argument("--height", type=float, default=4.0)
    return parser.parse_args()


def choose_ego(vehicles):
    heroes = [
        vehicle
        for vehicle in vehicles
        if vehicle.attributes.get("role_name", "").lower() in ("hero", "ego")
    ]
    return heroes[0] if heroes else None


def main():
    args = parse_args()
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    followed_id = None

    print("Live spectator started; waiting for a hero/ego vehicle.")

    try:
        while True:
            world = client.get_world()
            spectator = world.get_spectator()
            vehicle = choose_ego(list(world.get_actors().filter("vehicle.*")))

            if vehicle is None:
                followed_id = None
                time.sleep(0.1)
                continue

            if followed_id != vehicle.id:
                print(f"Following hero vehicle actor {vehicle.id}")
                followed_id = vehicle.id

            transform = vehicle.get_transform()
            forward = transform.get_forward_vector()
            camera_location = carla.Location(
                x=transform.location.x - args.distance * forward.x,
                y=transform.location.y - args.distance * forward.y,
                z=transform.location.z + args.height,
            )
            camera_rotation = carla.Rotation(
                pitch=-15.0,
                yaw=transform.rotation.yaw,
                roll=0.0,
            )
            spectator.set_transform(
                carla.Transform(camera_location, camera_rotation)
            )
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nLive spectator stopped.")


if __name__ == "__main__":
    main()
