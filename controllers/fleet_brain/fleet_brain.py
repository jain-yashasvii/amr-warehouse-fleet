"""
Multi-AMR Festo Robotino 3 Controller & Real-Time Sync Hub
With Safe Exception Catching & Auto-Fallback
"""

import sys
import traceback

try:
    import math
    import json
    import socket
    import threading
    import asyncio
    from controller import Robot
except Exception as e:
    print(f"[FATAL INIT ERROR]: {e}", file=sys.stderr)
    traceback.print_exc()

# Safe WebSockets Import Check
HAS_WEBSOCKETS = False
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    print("[WARNING] 'websockets' module not found in Webots Python environment. Install with: pip install websockets", file=sys.stderr)

robot = Robot()
time_step = int(robot.getBasicTimeStep())
raw_name = robot.getName()

if "1" in raw_name:
    clean_id = "AMR1"
elif "2" in raw_name:
    clean_id = "AMR2"
elif "3" in raw_name:
    clean_id = "AMR3"
else:
    clean_id = "AMR1"

print(f"[{clean_id}] Initializing controller...")

# Bind Motors
motors = []
num_devices = robot.getNumberOfDevices()
all_device_names = [robot.getDeviceByIndex(i).getName() for i in range(num_devices)]

candidate_names = ["wheel0_joint", "wheel1_joint", "wheel2_joint"]
for name in candidate_names:
    if name in all_device_names:
        dev = robot.getDevice(name)
        if hasattr(dev, "setPosition"):
            dev.setPosition(float('inf'))
            dev.setVelocity(0.0)
            motors.append(dev)

if len(motors) < 3:
    motors = []
    for i in range(num_devices):
        dev = robot.getDeviceByIndex(i)
        if dev.getNodeType() in [50, 51] and hasattr(dev, "setPosition"):
            dev.setPosition(float('inf'))
            dev.setVelocity(0.0)
            motors.append(dev)

gps = robot.getDevice("gps") if "gps" in all_device_names else None
if gps:
    gps.enable(time_step)

compass = robot.getDevice("compass") if "compass" in all_device_names else None
if compass:
    compass.enable(time_step)

def drive_robotino(v_fwd, v_str, omega=0.0):
    if len(motors) >= 3:
        v0 = -0.866 * v_fwd + 0.5 * v_str + 0.25 * omega
        v1 =  0.000 * v_fwd - 1.0 * v_str + 0.25 * omega
        v2 =  0.866 * v_fwd + 0.5 * v_str + 0.25 * omega

        MAX_V = 8.0
        motors[0].setVelocity(max(-MAX_V, min(MAX_V, v0 * 6.0)))
        motors[1].setVelocity(max(-MAX_V, min(MAX_V, v1 * 6.0)))
        motors[2].setVelocity(max(-MAX_V, min(MAX_V, v2 * 6.0)))

def stop_motors():
    if len(motors) >= 3:
        for m in motors:
            m.setVelocity(0.0)

LANE_X = {"AMR1": -2.0, "AMR2": 0.0, "AMR3": 2.0}
lane_x = LANE_X.get(clean_id, 0.0)

Y_MAX = 1.2
Y_MIN = -1.2
# Physical X route limits used by the current straight-line mission.
ROUTE_MIN = -4.6
ROUTE_MAX = 4.6
direction = None
dwell_ticks = 0
has_payload = (clean_id == "AMR3")
battery_level = 98.0 if clean_id == "AMR1" else (94.0 if clean_id == "AMR2" else 91.0)
order_seq = 100 + int(clean_id[-1])
current_order = f"ORD-{order_seq}"
current_sku = "SKU-ELEC-01"

sim_state = {"paused": False, "emergency_stop": False, "forced_conflict": False, "priority_robot": "AMR1"}

UDP_PORT = 9876
CMD_PORTS = {"AMR2": 9872, "AMR3": 9873}

fleet_positions = {
    "AMR1": {"robot_id": "AMR1", "x": -2.0, "y": 0.0, "heading_deg": 0.0, "battery": 98.0, "status": "IN_TRANSIT", "has_payload": False, "active_order": "ORD-101", "sku": "SKU-ELEC-01"},
    "AMR2": {"robot_id": "AMR2", "x": 0.0, "y": 0.0, "heading_deg": 90.0, "battery": 94.0, "status": "IN_TRANSIT", "has_payload": False, "active_order": "ORD-102", "sku": "SKU-MECH-44"},
    "AMR3": {"robot_id": "AMR3", "x": 2.0, "y": 0.0, "heading_deg": 180.0, "battery": 91.0, "status": "IN_TRANSIT", "has_payload": True, "active_order": "ORD-103", "sku": "SKU-AUTO-88"}
}

connected_ws_clients = set()
udp_client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if clean_id == "AMR1":
    def udp_telemetry_listener():
        udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp_server.bind(("127.0.0.1", UDP_PORT))
            while True:
                data, _ = udp_server.recvfrom(2048)
                msg = json.loads(data.decode("utf-8"))
                r_id = msg.get("robot_id")
                if r_id in fleet_positions:
                    fleet_positions[r_id] = msg
        except Exception:
            pass

    threading.Thread(target=udp_telemetry_listener, daemon=True).start()

    if HAS_WEBSOCKETS:
        async def ws_handler(ws):
            connected_ws_clients.add(ws)
            try:
                async for raw in ws:
                    cmd = json.loads(raw)
                    act, val = cmd.get("action"), cmd.get("value")
                    if act == "EMERGENCY_STOP": sim_state["emergency_stop"] = val
                    elif act == "PAUSE": sim_state["paused"] = val
                    elif act == "TRIGGER_CONFLICT": sim_state["forced_conflict"] = val
                    elif act == "SET_PRIORITY": sim_state["priority_robot"] = val

                    payload = json.dumps(sim_state).encode("utf-8")
                    udp_client_sock.sendto(payload, ("127.0.0.1", CMD_PORTS["AMR2"]))
                    udp_client_sock.sendto(payload, ("127.0.0.1", CMD_PORTS["AMR3"]))
            except Exception:
                pass
            finally:
                connected_ws_clients.discard(ws)

        async def broadcast_telemetry():
            while True:
                if connected_ws_clients:
                    payload = json.dumps(fleet_positions)
                    await asyncio.gather(*[c.send(payload) for c in list(connected_ws_clients)], return_exceptions=True)
                await asyncio.sleep(0.033)

        async def run_hub():
            try:
                async with websockets.serve(ws_handler, "127.0.0.1", 8765):
                    print("[AMR1] WebSocket Server successfully bound to ws://127.0.0.1:8765")
                    await broadcast_telemetry()
            except Exception as e:
                print(f"[AMR1 WS ERROR]: {e}", file=sys.stderr)

        threading.Thread(target=lambda: asyncio.run(run_hub()), daemon=True).start()

else:
    my_port = CMD_PORTS.get(clean_id, 9872)
    def cmd_listener():
        cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cmd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            cmd_sock.bind(("127.0.0.1", my_port))
            while True:
                data, _ = cmd_sock.recvfrom(1024)
                sim_state.update(json.loads(data.decode("utf-8")))
        except Exception:
            pass

    threading.Thread(target=cmd_listener, daemon=True).start()

step_counter = 0
print(f"[{clean_id}] Starting main control loop...")

# ---------------------------------------------------------
# MAIN CONTROL LOOP
# ---------------------------------------------------------
while robot.step(time_step) != -1:
    step_counter += 1

    if gps:
        vals = gps.getValues()
        cur_x = float(vals[0])
        cur_y = float(vals[1])  # This world's floor-depth axis
        cur_z = float(vals[2])  # This world's near-constant robot elevation
    else:
        cur_x, cur_y, cur_z = float(lane_x), 0.0, 0.0

    # Preserve raw coordinates. The dashboard projects X × Y as its floor
    # plan and displays Z separately as the robot's current elevation.
    route_position = cur_x

    if direction is None:
        direction = -1 if route_position >= 0.0 else 1

    battery_level = max(5.0, battery_level - 0.005)

    heading_deg = 0.0
    if compass:
        c = compass.getValues()
        heading_deg = (math.degrees(math.atan2(c[0], c[2])) + 360.0) % 360.0

    if sim_state["emergency_stop"] or sim_state["paused"]:
        stop_motors()
        status_txt = "E-STOPPED" if sim_state["emergency_stop"] else "PAUSED"
        t_data = {
            "robot_id": clean_id,
            "x": round(float(cur_x), 3),
            "y": round(float(cur_y), 3),
            "z": round(float(cur_z), 3),
            "heading_deg": round(heading_deg, 1),
            "battery": round(battery_level, 1),
            "status": status_txt,
            "has_payload": has_payload,
            "active_order": current_order,
            "sku": current_sku
        }
        if clean_id == "AMR1":
            fleet_positions["AMR1"] = t_data
        elif step_counter % 3 == 0:
            udp_client_sock.sendto(json.dumps(t_data).encode("utf-8"), ("127.0.0.1", UDP_PORT))
        continue

    if dwell_ticks > 0:
        dwell_ticks -= 1
        stop_motors()
        mission_status = "PICKING" if has_payload else "DELIVERED"
    elif direction == 1 and route_position >= ROUTE_MAX:
        dwell_ticks = 15
        stop_motors()
        direction = -1
        has_payload = not has_payload
        mission_status = "DELIVERED" if not has_payload else "PICKING"
    elif direction == -1 and route_position <= ROUTE_MIN:
        dwell_ticks = 15
        stop_motors()
        direction = 1
        has_payload = not has_payload
        mission_status = "DELIVERED" if not has_payload else "PICKING"
    else:
        # The active ground-travel direction in this world is GPS X. Convert
        # that desired world-space velocity to Robotino body-axis velocity.
        desired_world_x = 0.80 * direction
        heading_rad = math.radians(heading_deg)

        v_fwd = math.sin(heading_rad) * desired_world_x
        v_str = math.cos(heading_rad) * desired_world_x

        drive_robotino(v_fwd, v_str, 0.0)
        mission_status = "IN_TRANSIT"

    telemetry = {
        "robot_id": clean_id,
        "x": round(float(cur_x), 3),
        "y": round(float(cur_y), 3),
        "z": round(float(cur_z), 3),
        "heading_deg": round(heading_deg, 1),
        "battery": round(battery_level, 1),
        "status": mission_status,
        "has_payload": has_payload,
        "active_order": current_order,
        "sku": current_sku
    }

    if clean_id == "AMR1":
        fleet_positions["AMR1"] = telemetry
    elif step_counter % 2 == 0:
        try:
            udp_client_sock.sendto(json.dumps(telemetry).encode("utf-8"), ("127.0.0.1", UDP_PORT))
        except Exception:
            pass