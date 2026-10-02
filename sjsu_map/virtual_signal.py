"""Traffic-signal logic for the SJSU map.

The imported SJSU OSM extract currently loads reliably without native CARLA
traffic lights. This module provides a deterministic signal/stop-line test
that works on the same road map and is easy for students to modify.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import carla


@dataclass
class SignalConfig:
    # Replace these with a measured location from route_inspection.py.
    stop_line_x: float
    stop_line_y: float
    stop_line_z: float = 0.5
    red_seconds: float = 8.0
    green_seconds: float = 10.0
    yellow_seconds: float = 2.0
    tolerance_m: float = 2.5


class VirtualSignal:
    def __init__(self, world: carla.World, config: SignalConfig):
        self.world = world
        self.config = config
        self.location = carla.Location(
            x=config.stop_line_x, y=config.stop_line_y, z=config.stop_line_z
        )
        self.started = time.monotonic()

    @property
    def state(self) -> str:
        cycle = self.config.red_seconds + self.config.green_seconds + self.config.yellow_seconds
        elapsed = (time.monotonic() - self.started) % cycle
        if elapsed < self.config.red_seconds:
            return "RED"
        if elapsed < self.config.red_seconds + self.config.green_seconds:
            return "GREEN"
        return "YELLOW"

    def draw(self, seconds: float = 0.2) -> None:
        color = {
            "RED": carla.Color(255, 0, 0),
            "GREEN": carla.Color(0, 255, 0),
            "YELLOW": carla.Color(255, 220, 0),
        }[self.state]
        self.world.debug.draw_point(
            self.location + carla.Location(z=3.0),
            size=0.35,
            color=color,
            life_time=seconds,
        )
        self.world.debug.draw_line(
            self.location + carla.Location(z=0.03, x=-2.0),
            self.location + carla.Location(z=0.03, x=2.0),
            thickness=0.12,
            color=color,
            life_time=seconds,
        )

    def crossed_during_red(self, vehicle: carla.Vehicle, previous_x: float | None) -> bool:
        if previous_x is None or self.state != "RED":
            return False
        current_x = vehicle.get_location().x
        crossed = (previous_x - self.location.x) * (current_x - self.location.x) <= 0
        close_y = abs(vehicle.get_location().y - self.location.y) <= self.config.tolerance_m
        return crossed and close_y
