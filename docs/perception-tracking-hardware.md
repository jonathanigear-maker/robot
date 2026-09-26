# Perception, Tracking, Mapping and Hardware Options

## Purpose of this document

Working notes for perception, tracking, navigation and possible sensor additions. These are options rather than a shopping list. Existing hardware should be integrated first and new hardware added when it solves a demonstrated limitation.

## Existing perception and interaction hardware

### HuskyLens on the arm

Currently used for face recognition and face tracking. This is particularly valuable for the first desk-bound interaction milestone.

The HuskyLens has multiple vision modes, so the robot can manage modes according to context. A possible state machine is:

```text
general/object mode
      |
      +-- person detected
              |
              v
       face-recognition mode
              |
       identify / track person
              |
       person lost for timeout
              |
              v
       return to general mode
```

ROS should see meaningful events such as PERSON_DETECTED, PERSON_IDENTIFIED, PERSON_LEFT and CAT_DETECTED rather than needing the AI to process every camera frame.

Because the camera is mounted on the arm, small arm movements can act like head/neck movements during conversation.

### Existing single-point ToF

Mounted near the top of the arm. Useful for direct range measurements and potentially for measuring the distance to something the arm/camera is examining.

### OpenMV Cam

Available as an alternative programmable vision camera. Keep it for a future dedicated vision job rather than replacing the currently useful HuskyLens unless there is a clear reason. Possible future jobs include fixed forward/downward perception, marker detection, floor/edge analysis or another lightweight always-on vision task.

### ReSpeaker XVF3800

Provides microphone/audio input for Vosk and OpenAI voice interaction. Direction-of-arrival information may also become useful for deciding where the robot should look when somebody speaks.

## Possible 8x8 ToF depth sensor

A small 8x8 ToF array such as the DFRobot RP2040/VL53L7CX module is a potential future addition.

An 8x8 sensor provides 64 depth measurements over a field of view rather than a single range. Physical spacing between samples increases with distance.

Potential arm mounting is attractive because ROS can combine:

- measured arm joint positions
- known sensor transform
- 64 depth measurements

to place the points in robot/world coordinates.

Potential uses:

- inspect objects near the gripper/camera
- estimate local 3D structure
- point down to inspect the floor
- detect raised objects or changes in floor height
- sweep the arm to accumulate a sparse local point cloud
- provide depth information alongside HuskyLens detections

It should not be treated as a replacement for the main 2D SLAM LiDAR. Arm-derived depth is better suited to local/temporary perception.

## Arm position and sensor accuracy

ROS forward kinematics can calculate sensor pose precisely from the robot model and joint readings, but real accuracy is limited by servo accuracy, backlash, flex, link-length measurements, servo zero calibration and sensor mounting alignment.

Calibration should include accurate link dimensions, joint zero offsets and the transform between HuskyLens/ToF sensors and the arm. A known flat floor can later provide useful calibration measurements.

## 2D LiDAR and persistent room mapping

Longer term, add a 360-degree 2D LiDAR for SLAM and navigation.

Planned software:

- SLAM Toolbox: create and save a persistent 2D occupancy map
- Nav2: localisation, route planning and obstacle avoidance
- TF: connect LiDAR, chassis, arm and other sensor coordinate frames
- MoveIt: arm collision/planning scene

A saved map is persistent across reboots. It represents the baseline/static environment; live costmaps handle temporary obstacles such as people, cats, chairs and boxes.

A rear-mounted LiDAR may be partially blocked by the arm. TF can describe an off-centre mounting position and known problematic scan sectors can be filtered, but a moving arm makes obstruction more complicated.

## Additional front/depth perception options

A front sensor may complement a rear 360-degree LiDAR, especially at another height.

Options previously considered:

- YDLIDAR GS2: wide line scan but very short range; better suited to close obstacle/edge sensing than room mapping.
- 8x8 matrix ToF: sparse 3D depth, useful for local obstacles and floor/height information.
- wider matrix dToF modules (for example 64x8): potentially useful for broader front depth sensing.
- ultrasonic range sensors: inexpensive supplementary close obstacle detection, not primary mapping.
- OpenMV: programmable camera for a dedicated visual task.

Do not buy these merely to increase sensor count; first determine what the main LiDAR/HuskyLens/existing ToF fail to perceive.

## IMU and odometry

An IMU is desirable once the robot drives. Tracked robots skid during turns, so motor/track odometry alone is imperfect.

Potential pose fusion:

```text
track/motor encoders ---+
IMU --------------------+--> robot_localization / pose estimate
optical flow (optional)-+
LiDAR/SLAM -------------+
```

If motors have encoders, use them for odometry. If they do not, commanded motor speed is only rough pseudo-odometry.

### Under-chassis optical flow

A mouse-like optical-flow sensor under the chassis could measure actual movement relative to the floor and help detect track slip.

Previously considered modules include PMW3901/PAA5100JE-class optical-flow sensors and combined optical-flow + ToF boards. Choice depends heavily on actual chassis-to-floor clearance and floor surfaces, so measure the robot before choosing hardware.

## Cats and household safety

Cats are household members, not merely generic obstacles.

Future navigation and arm behaviour should conservatively handle sudden cat movement, avoid moving tracks/arm into an animal, and check immediate surroundings before autonomous movement.

The mounted laser pointer may eventually be used for cat play, but activation and aiming must be constrained by deterministic safety rules: no intentional aiming toward faces/eyes and only use when a safe target area has been established.

## Home Assistant integration

Home Assistant can later become another source of household state and actions. Keep responsibilities separated:

```text
ROS / robot <--> bridge (e.g. MQTT) <--> Home Assistant <--> house devices/sensors
```

Home Assistant owns smart-home devices; ROS owns the robot. Household events such as doors, presence, lights and environmental sensors can become meaningful robot events, while robot capabilities can request smart-home actions.

## Longer-term navigation sequence

1. Finish desk-bound interaction/ROS integration.
2. Identify drive motor/controller and encoder capabilities.
3. Add IMU and basic odometry.
4. Add 2D LiDAR.
5. Build and save the first room/house map with SLAM Toolbox.
6. Add Nav2 localisation/navigation.
7. Add named places such as kitchen, living room and charging location.
8. Add supplementary floor/depth sensors only where testing shows a need.
9. Later combine navigation, perception, MoveIt and AI into higher-level household behaviours.

The guiding question for new perception hardware is: **does this help the robot live independently and safely in the house?**
