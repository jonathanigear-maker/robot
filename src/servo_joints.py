
import math

from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import JointState


# Servo order matches the Arduino SERVOS message.
# Centre = physical reference position (all arm servos at 500).
# Direction = sign of angle relative to that reference.
#
# Gripper: 120 fully open, 860 fully closed.
# Other servos: approximately 180 degrees over their calibrated range.

SERVOS = [
    {"name": "gripper_joint",       "centre": 120, "units_per_degree": None, "direction": 1},
    {"name": "wrist_roll_joint",    "centre": 500, "units_per_degree": 740 / 180, "direction": 1},
    {"name": "wrist_pitch_joint",   "centre": 500, "units_per_degree": 740 / 180, "direction": 1},
    {"name": "elbow_joint",         "centre": 500, "units_per_degree": 740 / 180, "direction": -1},
    {"name": "shoulder_joint",      "centre": 500, "units_per_degree": 740 / 180, "direction": 1},
    {"name": "base_rotation_joint", "centre": 500, "units_per_degree": 755 / 180, "direction": 1},
]


def servo_to_radians(servo_id, raw_position):
    servo = SERVOS[servo_id - 1]

    if servo_id == 1:
        # Normalised gripper opening:
        # 0.0 = fully open, 1.0 = fully closed
        return max(0.0, min(1.0, (raw_position - 120) / 740))

    degrees = (
        (raw_position - servo["centre"])
        / servo["units_per_degree"]
        * servo["direction"]
    )
    return math.radians(degrees)


def radians_to_servo(servo_id, angle):
    servo = SERVOS[servo_id - 1]

    if servo_id == 1:
        # For the gripper, angle is actually normalised closure.
        closure = max(0.0, min(1.0, angle))
        return round(120 + closure * 740)

    degrees = math.degrees(angle)

    return round(
        servo["centre"]
        + degrees * servo["units_per_degree"] * servo["direction"]
    )


class ServoJoints(Node):

    def __init__(self):
        super().__init__("spencer_servo_joints")

        self.subscription = self.create_subscription(
            Int32MultiArray,
            "/spencer/servos",
            self.servo_callback,
            10,
        )

        self.publisher = self.create_publisher(
            JointState,
            "/joint_states",
            10,
        )

    def servo_callback(self, msg):
        if len(msg.data) != 6:
            self.get_logger().warning(
                f"Expected 6 servo positions, received {len(msg.data)}"
            )
            return

        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()

        joint_state.name = [servo["name"] for servo in SERVOS]
        joint_state.position = [
            servo_to_radians(i + 1, raw)
            for i, raw in enumerate(msg.data)
        ]

        self.publisher.publish(joint_state)
