# ROS 2 / MoveIt Known Issues

## Jazzy ros2_control controller plugins — 21 September 2026

While testing the standard MoveIt Panda demo on the Raspberry Pi 5, MoveIt and RViz worked, including loading the robot model and motion planning, but the simulated arm could not execute trajectories correctly.

### Installed versions

- `ros-jazzy-controller-manager`: 4.48.0
- `ros-jazzy-controller-interface`: 4.48.0
- `ros-jazzy-ros2-control`: 4.48.0
- `ros-jazzy-ros2-controllers`: 4.42.1
- `ros-jazzy-joint-state-broadcaster`: 4.42.1
- `ros-jazzy-joint-trajectory-controller`: 4.42.1

APT reported all packages up to date, so this version split is what the current Jazzy ARM64 repository supplies.

### Symptoms

The Panda fake hardware loaded and activated successfully, and the gripper controller loaded normally. However, `controller_manager` failed to load:

- `joint_trajectory_controller/JointTrajectoryController`
- `joint_state_broadcaster/JointStateBroadcaster`

The controller manager reported `Loader ... not found` for both plugins.

As a consequence:

- `/joint_states` existed but had **0 publishers**.
- MoveIt did not receive a valid current Panda joint state.
- Planning from `<current>` could fail because the apparent/default state was in self-collision.
- Planning from an artificial named start state could work, but normal execution did not.

### Checks already completed

The following were confirmed:

- Both controller packages are installed.
- ROS can locate both packages under `/opt/ros/jazzy`.
- Their plugin XML files exist and contain the expected plugin classes.
- Their shared libraries exist:
  - `libjoint_state_broadcaster.so`
  - `libjoint_trajectory_controller.so`
- Their ament/pluginlib resource registrations exist.
- `ldd` reported no missing dependencies for either shared library.
- The Panda `ros2_controllers.yaml` correctly defines the arm controller, gripper controller and joint-state broadcaster.
- The fake Panda hardware exposes the expected seven arm position command interfaces and position/velocity state interfaces.

This therefore appears to be a current ROS 2 Jazzy `ros2_control` / `ros2_controllers` plugin/package compatibility issue, rather than a Panda URDF, MoveIt, or Raspberry Pi configuration problem.

### Decision

Do **not** downgrade packages or build controller packages from source yet.

Continue with development of our own robot description (URDF/Xacro), RViz model and MoveIt configuration. Revisit this issue before implementing real trajectory execution and first check whether newer Jazzy binary packages have resolved it.

### Our robot's possible execution architecture

The existing arm controller accepts a target joint position plus a movement time. MoveIt produces timed joint trajectories, so an alternative execution path is:

```text
MoveIt trajectory
      ↓
custom ROS bridge / trajectory adapter
      ↓
position + movement-time commands
      ↓
existing arm controller
      ↓
servos
```

We should still aim to get the standard `ros2_control` trajectory-controller stack working, because it provides a clean standard ROS architecture, but this custom bridge remains a practical option for the real robot.

### Revisit checklist

Before starting real arm execution:

1. Run `sudo apt update` and check versions of `ros2_control` and `ros2_controllers`.
2. Re-run the standard Panda MoveIt demo.
3. Check `ros2 control list_controllers`.
4. Confirm `joint_state_broadcaster` and `panda_arm_controller` are active.
5. Confirm `/joint_states` has a publisher.
6. Only investigate downgrade/source-build workarounds if the issue remains.
