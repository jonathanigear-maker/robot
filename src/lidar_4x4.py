import math
import struct

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import PointCloud2, PointField
from rclpy.duration import Duration

class Lidar4x4(Node):

    def __init__(self):
        super().__init__("lidar_4x4")

        self.subscription = self.create_subscription(
            Int32MultiArray,
            "/spencer/lidar_4x4",
            self.lidar_callback,
            10,
        )

        self.publisher = self.create_publisher(
            PointCloud2,
            "/spencer/lidar_4x4/points",
            10,
        )

        # Assumed 60-degree horizontal and vertical FOV.
        # Angles of the four measurement centres.
        self.angles = [
            math.radians(a) for a in (-22.5, -7.5, 7.5, 22.5)
        ]

        self.get_logger().info("4x4 LiDAR point cloud started")

    def lidar_callback(self, msg):
        if len(msg.data) != 16:
            return

        points = []

        for row in range(4):
            for col in range(4):
                distance_mm = msg.data[row * 4 + col]

                if distance_mm <= 0 or distance_mm >= 4000:
                    continue

                distance = distance_mm / 1000.0

                horizontal = self.angles[col]
                vertical = self.angles[row]

                # Sensor forward = +Z
                # Sensor left/right = X
                # Sensor up/down = Y
                x = distance * math.cos(vertical) * math.sin(horizontal)
                y = distance * math.sin(vertical)
                z = distance * math.cos(vertical) * math.cos(horizontal)

                points.append((x, y, z))

        cloud = PointCloud2()
        cloud.header.stamp = (
            self.get_clock().now() - Duration(seconds=0.3)
        ).to_msg()
        cloud.header.frame_id = "lidar_4x4_frame"

        cloud.height = 1
        cloud.width = len(points)

        cloud.fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        ]

        cloud.is_bigendian = False
        cloud.point_step = 12
        cloud.row_step = 12 * len(points)
        cloud.is_dense = True

        cloud.data = b"".join(
            struct.pack("<fff", *point) for point in points
        )

        self.publisher.publish(cloud)


def main():
    rclpy.init()
    node = Lidar4x4()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()