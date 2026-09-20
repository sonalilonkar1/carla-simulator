#!/usr/bin/env python3
"""List reproducible Town03 traffic-light approaches for CMPE 281."""

import argparse
import json
from pathlib import Path

import carla


TOWN03_LAYERS = (
    "Ground", "Buildings", "Walls", "Props", "StreetLights", "Decals",
    "ParkedVehicles", "Foliage", "Particles",
)


def load_world(client, requested_map):
    world = client.get_world()
    if world.get_map().name.split("/")[-1] == requested_map:
        return world
    if requested_map != "Town03_Opt":
        return client.load_world(requested_map)
    print("Loading Town03_Opt with MapLayer.NONE", flush=True)
    client.set_timeout(180.0)
    world = client.load_world(requested_map, True, carla.MapLayer.NONE)
    for name in TOWN03_LAYERS:
        print(f"Loading Town03 layer: {name}", flush=True)
        world.load_map_layer(getattr(carla.MapLayer, name))
    client.set_timeout(60.0)
    return world


def approaches(world, distance_m):
    rows = []
    lights = sorted(
        world.get_actors().filter("traffic.traffic_light*"),
        key=lambda light: (round(light.get_location().x, 3), round(light.get_location().y, 3)),
    )
    for light in lights:
        for stop_number, stop_wp in enumerate(light.get_stop_waypoints()):
            previous = stop_wp.previous(distance_m)
            if not previous:
                continue
            approach = min(
                previous,
                key=lambda wp: 0 if (wp.road_id, wp.lane_id) == (stop_wp.road_id, stop_wp.lane_id) else 1,
            )
            rows.append({
                "candidate_index": len(rows),
                "traffic_light_id": light.id,
                "stop_waypoint_number": stop_number,
                "road_id": stop_wp.road_id,
                "lane_id": stop_wp.lane_id,
                "stop_location": {
                    "x": round(stop_wp.transform.location.x, 3),
                    "y": round(stop_wp.transform.location.y, 3),
                    "z": round(stop_wp.transform.location.z, 3),
                },
                "approach_location": {
                    "x": round(approach.transform.location.x, 3),
                    "y": round(approach.transform.location.y, 3),
                    "z": round(approach.transform.location.z, 3),
                    "yaw": round(approach.transform.rotation.yaw, 3),
                },
            })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--map", default="Town03_Opt")
    parser.add_argument("--approach-distance", type=float, default=30.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    client = carla.Client(args.host, args.port)
    client.set_timeout(60.0)
    world = load_world(client, args.map)
    rows = approaches(world, args.approach_distance)
    payload = {"map": world.get_map().name.split("/")[-1], "candidate_count": len(rows), "candidates": rows}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Traffic-light approaches found: {len(rows)}")
    for row in rows[:10]:
        print(
            f"candidate={row['candidate_index']} light={row['traffic_light_id']} "
            f"road={row['road_id']} lane={row['lane_id']} "
            f"approach=({row['approach_location']['x']}, {row['approach_location']['y']})"
        )
    print(f"Discovery report: {path}")


if __name__ == "__main__":
    main()
