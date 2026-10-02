"""Common CARLA setup for every SJSU scenario.

The CARLA server must already be running. The server may already contain
OpenDriveMap, or an .xodr file can be supplied to load_sjsu_world().
"""

from __future__ import annotations

import time
from pathlib import Path

import carla


def connect(host: str = "127.0.0.1", port: int = 2000, timeout: float = 15.0):
    client = carla.Client(host, port)
    client.set_timeout(timeout)
    return client


def load_sjsu_world(
    client: carla.Client,
    xodr_path: str | None = None,
    *,
    reload: bool = False,
) -> carla.World:
    """Return the SJSU OpenDRIVE world.

    Use xodr_path on a fresh CARLA server. If the server already loaded the
    map, omitting xodr_path avoids regenerating it.
    """
    if xodr_path:
        xodr_file = Path(xodr_path).expanduser().resolve()
        if not xodr_file.is_file():
            raise FileNotFoundError(f"SJSU OpenDRIVE file not found: {xodr_file}")
        if reload or client.get_world().get_map().name != "Carla/Maps/OpenDriveMap":
            print(f"Loading SJSU OpenDRIVE map: {xodr_file}")
            world = client.generate_opendrive_world(xodr_file.read_text())
            time.sleep(2.0)
        else:
            world = client.get_world()
    else:
        world = client.get_world()

    print(f"CARLA map: {world.get_map().name}")
    if "OpenDriveMap" not in world.get_map().name:
        raise RuntimeError(
            "The active CARLA world is not OpenDriveMap. Start the SJSU map "
            "or provide --xodr /path/to/sjsu.xodr."
        )
    print(f"Spawn points: {len(world.get_map().get_spawn_points())}")
    return world


def choose_spawn(world: carla.World, index: int = 0) -> carla.Transform:
    points = world.get_map().get_spawn_points()
    if not points:
        raise RuntimeError("The SJSU OpenDRIVE map has no vehicle spawn points.")
    return points[index % len(points)]


def destroy_actors(actors: list[carla.Actor]) -> None:
    for actor in reversed(actors):
        if actor is not None and actor.is_alive:
            actor.destroy()
