# Sensors, Telemetry, and Video

## RGB camera

An RGB camera produces numbered image frames such as `frame-000001.png`. These frames provide visual evidence for a scenario.

## LiDAR

LiDAR produces 3-D point clouds. Store scans as `.ply` files and record the corresponding simulation frame or timestamp.

## Collision sensor

Attach a collision sensor to the ego vehicle. Record the frame, other actor, impulse, and location whenever a collision occurs.

## Telemetry

Record simulation time, frame number, position, speed, steering/throttle/brake, and scenario phase. Telemetry supports claims more reliably than video alone.

## Expected output

```text
result.json       pass/fail and summary metrics
telemetry.csv     time-series measurements
preview.png       quick visual check
frames/           RGB camera sequence
lidar/            point clouds, when used
```

## Create a video on your Mac

HPC nodes may not provide `ffmpeg`. Copy the frames to your local computer and run:

```bash
ffmpeg -framerate 20 -pattern_type glob -i 'frame-*.png' \
  -c:v libx264 -pix_fmt yuv420p scenario.mp4
```

Use the video together with telemetry and `result.json`; video alone is not sufficient evidence.
