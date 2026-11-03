# AMR Warehouse Fleet 

A multi-robot warehouse simulation built with Python, Webots, and React. The project simulates three Festo Robotino Autonomous Mobile Robots (AMRs) operating in a warehouse environment, with a web-based dashboard for monitoring robot positions, telemetry, and fleet operations.

The system combines independent robot controllers, inter-robot communication, obstacle avoidance, and real-time visualisation to explore multi-robot coordination in a simulated warehouse.

## Features

### 1. Multi-Robot Simulation
- Three Festo Robotino AMRs: AMR1, AMR2, and AMR3.
- Independent Webots controllers for individual robots.
- Simulated warehouse environment containing pallet stacks, racks, docks, and charging points.
- Robot movement and coordination within a shared environment.

### 2. Real-Time Fleet Monitoring Dashboard
- React-based dashboard connected to the simulation through WebSocket (`ws://localhost:8765`).
- Live telemetry displaying:
  - Robot position (X, Y, and Z coordinates, according to the simulation).
  - Heading and orientation.
  - Battery level.
  - Payload information.
  - Operational status.
  - Assigned work orders.
- Warehouse map showing robot locations, headings, racks, docks, and charging points.
- Visual indicators for robot payload and operating status.

### 3. Fleet Coordination and Communication
- AMR1 acts as the fleet gateway and forwards commands to AMR2 and AMR3 using UDP.
- Simulated inter-robot communication using Webots Emitter and Receiver devices.
- Visual radio-wave effects representing communication signals exchanged between robots.
- Dashboard controls for:
  - Emergency stop.
  - Pause and resume.
  - Conflict simulation.
  - Task priority settings.

### 4. Obstacle Avoidance
- IR sensor-based obstacle detection.
- Bumper-based collision detection.
- Obstacle avoidance involving walls, pallet stacks, and nearby robots.

### 5. Visual Communication Effects
- Radio-wave indicators around robots visually represent simulated communication activity.
- Visual effects help illustrate interactions between robots within the warehouse environment.
- These indicators represent simulated communication, not measured physical radio-frequency signals or wireless propagation.

## System Architecture

The project consists of three main components:

1. **Webots Simulation:** Provides the warehouse environment, robot models, sensors, and individual robot controllers.
2. **Fleet Gateway:** AMR1 acts as the fleet gateway, handling communication and forwarding commands to the other robots.
3. **React Dashboard:** Displays robot telemetry and provides fleet-level monitoring and simulation controls.


## Technology Stack

| Technology | Purpose |
| Python | Robot controllers and fleet logic |
| Webots | Robot and warehouse simulation |
| React | Web-based monitoring dashboard |
| JavaScript | Dashboard functionality |
| WebSocket | Dashboard communication |
| UDP | Command forwarding |
| Webots Emitter/Receiver | Simulated inter-robot communication |

## Simulation Environment

The warehouse environment includes:

- Three simulated Festo Robotino AMRs.
- Warehouse racks and pallet stacks.
- Loading and unloading docks.
- Charging stations.
- Obstacles and shared navigation areas.
- Visual radio-wave indicators illustrating simulated robot communication.

The robots operate within the shared simulated environment and exchange information through the implemented communication mechanisms.


### Prerequisites

Make sure you have installed:

- Webots.
- Python.
- Node.js and npm.
- Required Python dependencies.
- Required React/Node.js dependencies.

### Running the Project

The general execution sequence is:

1. Open the warehouse world file in Webots.
2. Start the simulation and robot controllers.
3. Start the fleet gateway and communication services as required by the implementation.
4. Start the React dashboard:

```bash
npm run dev
```

5. Open the local dashboard URL displayed in the terminal.


## Limitations

- The project operates in a simulated Webots environment rather than a physical warehouse.
- Robot navigation and obstacle avoidance are evaluated within the simulation.
- Battery and payload values represent simulated telemetry.
- Radio-wave visual effects illustrate simulated communication activity and do not represent physical signal measurements.
- Communication reliability and navigation performance have not been established through physical robot testing.
- Performance in real-world warehouse environments has not been validated.

## Future Improvements

- Evaluate navigation performance across different warehouse layouts.
- Improve fleet-level task allocation and scheduling.
- Explore advanced multi-robot path-planning techniques.
- Introduce additional performance metrics for collision avoidance and task completion.
- Investigate coordination strategies for larger robot fleets.
- Evaluate communication reliability under different simulated conditions.

## Project Objective

This project explores the integration of autonomous mobile robot simulation, multi-robot communication, fleet coordination, obstacle avoidance, and real-time visualization in a warehouse environment.

It provides a foundation for further experimentation with robotics, autonomous systems, and intelligent fleet management.
