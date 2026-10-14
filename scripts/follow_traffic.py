#!/usr/bin/env python3

import time
import carla

HOST = "127.0.0.1"
PORT = 2000

def main():
    client = carla.Client(HOST, PORT)
    client.set_timeout(10.0)

    world = client.get_world()
    spectator = world.get_spectator()

    print("Map:", world.get_map().name)
    print("Press Ctrl+C to stop the spectator.")

    try:
        while True:
            vehicles = world.get_actors().filter("vehicle.*")

            if vehicles:
                vehicle = vehicles[0]
                transform = vehicle.get_transform()
                location = transform.location

                spectator.set_transform(
                    carla.Transform(
                        location + carla.Location(z=35),
                        carla.Rotation(
                            pitch=-65,
                            yaw=transform.rotation.yaw,
                            roll=0,
                        ),
                    )
                )

                print(
                    f"\rFollowing vehicle {vehicle.id} | "
                    f"vehicles: {len(vehicles)}",
                    end="",
                    flush=True,
                )

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nSpectator stopped.")


if __name__ == "__main__":
    main()
