#!/usr/bin/env python3

import time
import carla

client = carla.Client("127.0.0.1", 2000)
client.set_timeout(10.0)

world = client.get_world()
spectator = world.get_spectator()

vehicles = world.get_actors().filter("vehicle.*")

if vehicles:
    locations = [vehicle.get_location() for vehicle in vehicles]

    center_x = sum(p.x for p in locations) / len(locations)
    center_y = sum(p.y for p in locations) / len(locations)

    spectator.set_transform(
        carla.Transform(
            carla.Location(
                x=center_x,
                y=center_y,
                z=45
            ),
            carla.Rotation(
                pitch=-70,
                yaw=0,
                roll=0
            )
        )
    )

    print("Fixed bird's-eye view enabled.")
    print(f"Following area containing {len(vehicles)} vehicles.")
else:
    print("No vehicles found.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nBird's-eye view stopped.")
