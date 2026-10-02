"""Convert the SJSU OSM extract to a reusable OpenDRIVE file.

Run from the repository root on the GPU workstation while CARLA is running.
Traffic-light generation is intentionally disabled because the current OSM
extract causes the OSM-to-OpenDRIVE converter to crash when native signals are
requested.
"""

from pathlib import Path

import carla


REPO_ROOT = Path(__file__).resolve().parent
OSM_PATH = REPO_ROOT / "maps" / "sjsu.osm"
XODR_PATH = REPO_ROOT / "maps" / "sjsu.xodr"


def main():
    if not OSM_PATH.is_file():
        raise FileNotFoundError(f"Missing OSM file: {OSM_PATH}")

    osm_data = OSM_PATH.read_text(encoding="utf-8")

    settings = carla.Osm2OdrSettings()
    settings.center_map = True
    settings.generate_traffic_lights = False
    settings.all_junctions_with_traffic_lights = False

    print(f"Converting {OSM_PATH} ...")
    xodr = carla.Osm2Odr.convert(osm_data, settings)

    if not xodr or len(xodr) < 1000:
        raise RuntimeError("CARLA returned an empty or invalid OpenDRIVE file.")

    XODR_PATH.write_text(xodr, encoding="utf-8")
    print(f"Saved {XODR_PATH}")
    print(f"OpenDRIVE size: {XODR_PATH.stat().st_size / 1024:.1f} KiB")

    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(30.0)
    print("Loading the saved OpenDRIVE map into CARLA ...")
    world = client.generate_opendrive_world(xodr)
    print(f"Loaded map: {world.get_map().name}")
    print(f"Spawn points: {len(world.get_map().get_spawn_points())}")


if __name__ == "__main__":
    main()
