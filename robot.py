import time
import rclpy
import threading
import subprocess

from src import arduino_comms
from src import respeaker
from src import moonshine
from src import audio_output
from rclpy.signals import SignalHandlerOptions
from rclpy.executors import SingleThreadedExecutor
from src.servo_joints import ServoJoints
from src.lidar_4x4 import Lidar4x4

def main():
    print("Starting robot...")
    lidar_c1 = None
    state_publisher = None
    try:
        # Initialise ROS 2
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
        print("ROS 2 initialised.")

        # Start Spencer's robot state publisher
        with open(
            "/home/sodigece/ros2_ws/src/xarm_description/urdf/xarm.urdf"
        ) as f:
            robot_description = f.read()

        state_publisher = subprocess.Popen([
            "/opt/ros/jazzy/lib/robot_state_publisher/robot_state_publisher",
            "--ros-args",
            "-p", f"robot_description:={robot_description}"
        ])

        print("Robot state publisher started.")

        # Start RPLIDAR C1
        lidar_c1 = subprocess.Popen([
            "/home/sodigece/ros2_ws/install/sllidar_ros2/lib/sllidar_ros2/sllidar_node",
            "--ros-args",
            "-p", "serial_port:=/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_dcf5b7ee8f31f11196a48d5f30d20014-if00-port0",
            "-p", "serial_baudrate:=460800",
            "-p", "frame_id:=laser"
        ])

        print("RPLIDAR C1 started.")

        servo_node = ServoJoints()
        lidar_node = Lidar4x4()

        servo_executor = SingleThreadedExecutor()
        servo_executor.add_node(servo_node)
        servo_executor.add_node(lidar_node)

        servo_thread = threading.Thread(
            target=servo_executor.spin,
            daemon=True
        )
        servo_thread.start()


        # Start Spencer's systems
        arduino_comms.start(show_serial=False)
        respeaker.start()
        moonshine.start()

        print("Robot running.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping robot...")

    finally:
        print("Shutting down Spencer...")

        # Stop microphone callbacks before closing Moonshine.
        respeaker.stop()

        # Now safe to release Moonshine's resources.
        moonshine.stop()

        audio_output.stop_stream()

        # Stop Arduino after modules that might send commands.
        arduino_comms.stop()
        # Stop the servo ROS executor
        servo_executor.shutdown()
        servo_thread.join()
        servo_node.destroy_node()
        lidar_node.destroy_node()

        # Stop robot state publisher
        if state_publisher is not None:
            state_publisher.terminate()
            try:
                state_publisher.wait(timeout=5)
            except subprocess.TimeoutExpired:
                state_publisher.kill()
                state_publisher.wait()

        if lidar_c1 is not None:
            lidar_c1.terminate()
            try:
                lidar_c1.wait(timeout=5)
            except subprocess.TimeoutExpired:
                lidar_c1.kill()
                lidar_c1.wait()

        print("ROS 2 stopped.")
        print("Robot stopped.")


if __name__ == "__main__":
    main()