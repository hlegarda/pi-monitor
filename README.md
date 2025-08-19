# Raspberry Pi 5 Monitor

A lightweight Flask + Chart.js web app that provides a real-time dashboard of your Raspberry Pi’s system performance.

## Uses

The Raspberry Pi 5 Monitor is designed to give a clear, real-time overview of your Raspberry Pi’s system performance. It is particularly useful for:

- Monitoring CPU and memory usage to prevent system overloads.
- Keeping track of temperature to avoid thermal throttling or hardware issues.
- Observing disk and network activity for storage management and network diagnostics.
- Visualizing trends over time with responsive charts, helping to identify spikes or abnormal behavior.

This tool is ideal for hobbyists running multiple services on a Pi, small home servers, or any scenario where you want a lightweight, browser-based dashboard for system metrics.

## Docker Compose Setup

The app is designed to run easily with Docker Compose, simplifying deployment and updates.

1. Create a file named docker-compose.yml in your project folder with the following content:


```
services:
  pi-monitor:
    image: hanzellegarda/pi-monitor:latest
    container_name: pi-monitor
    restart: unless-stopped
    ports:
      - "5100:5100"
```

2. Start the service by running:
```
docker compose up -d
```
3. Access the dashboard by visiting:
```
http://<raspberry-pi-ip>:5100
```

This setup ensures the container automatically restarts if the Pi reboots and makes updating or redeploying the app as simple as running a few Docker Compose commands.

## Features

- Live-updating summary bar with CPU, temperature, memory, disk, and network stats.
- Color-coded alerts for high CPU, temperature, or memory/disk usage.
- Responsive charts for trends over time, optimized for both desktop and mobile.
- Minimal dependencies; runs efficiently in a Docker container.

## Requirements

- Docker + Docker Compose
- Raspberry Pi OS (or any Linux system)
- ARM64 architecture for Raspberry Pi 5

> The app uses vcgencmd on Raspberry Pi OS to read CPU temperature. If unavailable, it falls back to psutil’s thermal sensors.

## Dockler Image
https://github.com/hlegarda/pi-monitor



### Made with ❤️ for Raspberry Pi tinkering.
