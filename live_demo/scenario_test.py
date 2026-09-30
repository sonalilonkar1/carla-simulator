import argparse
import carla, time
from violation_monitor import ViolationMonitor
from stops import *
import random

def start_driving(vehicle, tm, *,  dangerous = False):
    if dangerous:
        tm.ignore_signs_percentage(vehicle, 100)
        tm.ignore_lights_percentage(vehicle, 100)
        tm.ignore_vehicles_percentage(vehicle, 100)
        tm.ignore_walkers_percentage(vehicle, 100)
        tm.global_percentage_speed_difference(25)
    else:
        tm.ignore_signs_percentage(vehicle, 0)
        tm.ignore_lights_percentage(vehicle, 0)
        tm.ignore_vehicles_percentage(vehicle, 0)
        tm.ignore_walkers_percentage(vehicle, 0)
        tm.global_percentage_speed_difference(0)
    vehicle.set_autopilot(True)

def stop_driving(vehicle):
    vehicle.set_autopilot(False)
    control = carla.VehicleControl()
    control.throttle = 0.0
    control.brake = 1.0  # Full braking (0.0 to 1.0)
    control.hand_brake = False
    vehicle.apply_control(control)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the four live CARLA traffic-violation scenarios."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--tm-port", type=int, default=8000)
    parser.add_argument("--map", default="Town10HD_Opt")
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--log-file", default="violations.txt")
    return parser.parse_args()


def spawn_ego(world, blueprint, transform):
    """Spawn the ego robustly and make it discoverable by the live spectator."""
    if blueprint.has_attribute("role_name"):
        blueprint.set_attribute("role_name", "hero")

    vehicle = world.try_spawn_actor(blueprint, transform)
    if vehicle is None:
        raise RuntimeError(
            "Could not spawn the ego vehicle because the selected position is occupied."
        )
    return vehicle


def main():
    args = parse_args()

    # Carla essentials
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()
    if not world.get_map().name.endswith(args.map):
        print(f"Loading {args.map}...")
        world = client.load_world(args.map)
        time.sleep(2.0)
    blueprint_library= world.get_blueprint_library()
    spectator = world.get_spectator()
    traffic_manager = client.get_trafficmanager(args.tm_port)
    all_actors = world.get_actors()

    # Traffic violation monitoring
    vm = ViolationMonitor(
        host=args.host,
        port=args.port,
        tm_port=args.tm_port,
        file=args.log_file,
    )

    #--------------------------------------------
    # Scenario #1: Red light with no other actors
    #--------------------------------------------

    vehicle_bp = random.choice(blueprint_library.filter('vehicle.tesla.model3'))
    temp_spawn = random.choice(world.get_map().get_spawn_points())
    vehicle = spawn_ego(world, vehicle_bp, temp_spawn)

    traffic_lights = []
    for actor in all_actors:
        if 'light' in actor.type_id:
            traffic_lights.append(actor)
    
    traffic_light = traffic_lights[0]

    wp = traffic_light.get_stop_waypoints()[0]
    transform = carla.Transform(wp.transform.location, wp.transform.rotation)
    vehicle.set_transform(transform)
    transform.location.z += 2
    spectator.set_transform(transform)

    print('\nScenario #1: Red light with empty street\n')
    time.sleep(2.0)
    traffic_light.set_state(carla.TrafficLightState.Red)
    
    start_driving(vehicle, traffic_manager, dangerous=True)
    vm.monitor(vehicle=vehicle, duration=args.duration)
    stop_driving(vehicle); time.sleep(1.0)

    #--------------------------------------------
    # Scenario #2: Stop sign with no other actors
    #--------------------------------------------
    
    stop_signs = []
    for actor in all_actors:
        if 'stop' in actor.type_id:
            waypoints = get_stop_sign_waypoints(world.get_map(), actor, world)
            stop_signs.append((actor, waypoints))

    pair = stop_signs[-1]
    wp = pair[1][0]
    transform = wp.transform
    vehicle.set_transform(transform)
    transform.location.z += 2
    spectator.set_transform(transform)
    print('\nScenario #2: Stop sign with empty street\n')
    time.sleep(2.0)
    
    start_driving(vehicle,traffic_manager, dangerous=True)
    vm.monitor(vehicle=vehicle, duration=args.duration)
    stop_driving(vehicle); time.sleep(1.0)
    vehicle.destroy()

    #---------------------------------------------------
    # Scenario #3: Red light with pedestrians on the map
    #---------------------------------------------------

    wp = traffic_light.get_stop_waypoints()[0]
    transform = carla.Transform(wp.transform.location, wp.transform.rotation)
    transform.location.z += 0.5
    vehicle = spawn_ego(world, vehicle_bp, transform)
    transform.location.z += 1.5
    spectator.set_transform(transform)
    print('\nScenario #3: Red light with pedestrians\n')

    input('Ensure background pedestrians are running, then press Enter...')

    start_driving(vehicle,traffic_manager, dangerous=True)
    vm.monitor(vehicle=vehicle, duration=args.duration)
    stop_driving(vehicle); time.sleep(1.0)

    input('Press Enter to continue to the stop-sign scenario...')

    #---------------------------------------------------
    # Scenario #4: Stop sign with pedestrians on the map
    #---------------------------------------------------

    pair = stop_signs[-1]
    wp = pair[1][0]
    transform = wp.transform
    vehicle.set_transform(transform)
    transform.location.z += 2
    spectator.set_transform(transform)
    print('\nScenario #4: Stop sign with pedestrians\n')

    input('Ensure background pedestrians are running, then press Enter...')

    start_driving(vehicle,traffic_manager, dangerous=True)
    vm.monitor(vehicle=vehicle, duration=args.duration)
    stop_driving(vehicle); time.sleep(1.0)

    vehicle.destroy(); print('Finished testing all scenarios')

if __name__ == '__main__':
    main()
