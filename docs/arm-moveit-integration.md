# Arm / MoveIt Integration Notes

Working design notes for connecting the customised Hiwonder/LewanSoul xArm-style arm to ROS 2 Jazzy, ros2_control and MoveIt.

## Proposed command path

```text
MoveIt
  ↓
joint_trajectory_controller
  ↓ desired joint positions (radians)
custom ros2_control hardware interface
  ↓ radians → native servo units
Pi → Arduino serial protocol
  ↓
Arduino
  ↓ existing xArmServoController library
Hiwonder xArm controller
  ↓
servos
```

ROS and MoveIt should remain in normal ROS joint units (radians for revolute joints). Native xArm values such as 0–1000 should exist only below the hardware-interface boundary.

The Arduino should stay deliberately simple. It receives native target positions plus a movement duration and uses the existing xArm library to send them to the controller.

## Why the existing Arduino library is useful

The xArmServoController library already supports sending several servo targets in one command with one common duration:

```cpp
setPosition(xArmServo servos[], int count, unsigned duration, bool wait = false);
```

This is a good match for a ros2_control update cycle because all arm joints can receive the next target together.

It also supports requesting several servo positions together:

```cpp
getPosition(xArmServo servos[], int count);
```

That can provide actual joint-position feedback to ROS.

Reference:
- https://github.com/ccourson/Hiwonder-xArm1S/tree/main/Arduino/xArmServoController
- Source: https://github.com/ccourson/Hiwonder-xArm1S/tree/main/Arduino/xArmServoController/src

## Trajectory execution idea

A useful reference implementation is daira-ai/xArm_Lewansoul_ROS. It is ROS 1, so it is not drop-in code for Jazzy, but its control approach is relevant.

Its hardware interface is configured for a nominal 10 Hz loop. Each update reads joint positions, lets controller_manager update the desired joint state, and then sends the current desired positions to the arm using approximately the elapsed control-cycle time as the servo movement duration.

Reference:
- https://github.com/daira-ai/xArm_Lewansoul_ROS
- Hardware interface: https://github.com/daira-ai/xArm_Lewansoul_ROS/tree/melodic-devel/xarm_hardware_interface

For our implementation, an initial experiment could therefore be:

```text
about every 100 ms:
    read actual servo positions
    update ros2_control
    obtain interpolated desired joint positions
    convert radians → native servo positions
    send all servo targets with about 100 ms duration
```

The exact update rate and movement duration must be tested on the real arm rather than assumed.

## Calibration belongs on the Pi / ROS side

Each joint needs calibration between ROS radians and the native servo value.

Conceptually:

```text
servo_value = zero + radians * scale
radians     = (servo_value - zero) / scale
```

A negative scale handles a joint whose servo direction is opposite to the ROS joint direction.

Calibration should be configuration data rather than scattered conversion code. For example:

```yaml
shoulder:
  servo_id: 2
  zero: 500
  scale: 191

elbow:
  servo_id: 3
  zero: 500
  scale: -191
```

The actual values will be measured from the customised robot.

Rounding to an integer native servo position is unavoidable. ROS should use sensible joint/goal tolerances so a tiny quantisation difference is accepted rather than treated as a fault.

## Limits and error handling

There should be limits at more than one level:

```text
MoveIt / URDF joint limits
        ↓
ROS hardware-interface calibration and limits
        ↓
Arduino native servo safety limits
```

The Arduino limits are a final safety backstop. An invalid command should not be silently hidden by clamping if that would make ROS believe a different position was commanded.

Possible serial error messages:

```text
ERROR,ARM,LIMIT,2,850
ERROR,ARM,TIMEOUT
ERROR,ARM,NO_RESPONSE,4
```

Normal feedback could be something like:

```text
ARM_POS,501,785,601,399,500,502
```

The exact serial protocol is still to be designed.

## Feedback and trajectory failure

MoveIt normally plans a trajectory first. During execution, the trajectory controller follows that time-based trajectory; MoveIt does not automatically recalculate the path every time a servo is slightly behind.

Actual servo positions should therefore be fed back through the hardware interface. Small tracking/rounding errors are tolerated. If commanded versus actual position exceeds configured trajectory tolerances, execution can fail/abort.

Higher-level robot logic can then decide whether to stop, retry, report a fault, or request a new plan from the robot's actual position.

This matters for collision safety: if a joint is substantially away from the planned position, the rest of the planned motion should not blindly be assumed safe.

## Model / MoveIt notes

The daira-ai repository is also a useful reference for xArm geometry and MoveIt structure. Our robot is modified, so dimensions, joint origins, axes and limits must be verified against the actual hardware.

Detailed STL meshes can be used for visual geometry. Collision geometry can use simpler shapes/meshes where appropriate. Rigid robot additions can be fixed links. Mechanical over-folding should primarily be represented with correct joint limits; self-collision checking handles collisions within those allowed ranges.

For linked gripper fingers, a URDF mimic joint may be useful if one physical actuator drives both fingers.

## Open questions / experiments

- Confirm exact servo/controller hardware and current servo IDs.
- Measure each joint's zero, direction, scale and safe native limits.
- Measure reliable command + position-feedback rate over the existing 9600-baud arm link.
- Test whether repeated ~100 ms timed targets retarget smoothly.
- Test whether a movement duration slightly longer than the update period improves continuity.
- Decide final Pi ↔ Arduino serial message format.
- Configure trajectory tracking and goal tolerances from measured real-arm behaviour.
- Verify modified robot geometry before relying on MoveIt collision checking.
