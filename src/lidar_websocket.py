#!/usr/bin/env python3

import asyncio
import json
import math
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

import websockets


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

HOST = "0.0.0.0"
PORT = 8765


# --------------------------------------------------------------------------
# Shared latest scan
# --------------------------------------------------------------------------

latest_scan = None
scan_lock = threading.Lock()


# --------------------------------------------------------------------------
# ROS2 LiDAR node
# --------------------------------------------------------------------------

class LidarNode(Node):

    def __init__(self):
        super().__init__("spencer_lidar_websocket")

        self.subscription = self.create_subscription(
            LaserScan,
            "/scan",
            self.scan_callback,
            10
        )

        self.get_logger().info("Listening to /scan")

    def scan_callback(self, msg):

        points = []

        angle = msg.angle_min

        for distance in msg.ranges:

            # Ignore invalid / missing measurements
            if (
                math.isfinite(distance)
                and msg.range_min <= distance <= msg.range_max
            ):
                x = distance * math.cos(angle)
                y = distance * math.sin(angle)

                # Round just to keep the WebSocket messages smaller
                points.append([
                    round(x, 3),
                    round(y, 3)
                ])

            angle += msg.angle_increment

        data = {
            "type": "lidar",
            "frame": msg.header.frame_id,
            "points": points
        }

        global latest_scan

        with scan_lock:
            latest_scan = data


# --------------------------------------------------------------------------
# WebSocket server
# --------------------------------------------------------------------------

async def websocket_handler(websocket):

    print("Viewer connected")

    try:
        while True:

            with scan_lock:
                data = latest_scan

            if data is not None:
                await websocket.send(json.dumps(data))

            # C1 is producing approximately 10 scans/sec
            await asyncio.sleep(0.1)

    except websockets.exceptions.ConnectionClosed:
        print("Viewer disconnected")


async def websocket_server():

    print(f"WebSocket server listening on port {PORT}")

    async with websockets.serve(
        websocket_handler,
        HOST,
        PORT
    ):
        await asyncio.Future()


# --------------------------------------------------------------------------
# ROS thread
# --------------------------------------------------------------------------

def run_ros():

    rclpy.init()

    node = LidarNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():

    ros_thread = threading.Thread(
        target=run_ros,
        daemon=True
    )

    ros_thread.start()

    asyncio.run(websocket_server())


if __name__ == "__main__":
    main()