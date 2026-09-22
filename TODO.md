# Robot To-Do List

Living checklist for the robot project. Tick items off as they are completed and add/refine tasks as the design develops.

## Current priority

Development order agreed:

1. Voice on the Raspberry Pi 5
2. Local SLM command interpretation
3. ROS command/behaviour integration without hardware movement
4. Arduino and subsystem communication
5. Arm / ros2_control / MoveIt hardware integration
6. Higher-level behaviours, tracking and OpenAI conversation

---

## 1. Pi 5 / base ROS setup

- [x] Install Ubuntu 24.04 on Raspberry Pi 5
- [x] Install ROS 2 Jazzy desktop
- [x] Configure CycloneDDS
- [x] Install MoveIt
- [x] Install ros2_control and ros2_controllers
- [x] Run Panda MoveIt demo
- [x] Confirm Panda controllers active
- [x] Confirm joint-state feedback
- [x] Confirm MoveIt plan + execute works
- [ ] Check/fix Raspberry Pi low-power warning
- [ ] Finish reliable remote-desktop setup for reboot/headless use
- [ ] Tidy ROS workspace/startup environment once development layout settles

## 2. Voice — next practical work

- [x] Prototype ReSpeaker + Vosk on earlier Pi
- [x] Confirm ReSpeaker hardware access
- [ ] Move current ReSpeaker/Vosk code to Pi 5
- [ ] Confirm ReSpeaker is detected reliably after reboot
- [ ] Test microphone capture on Pi 5
- [ ] Run existing Vosk recognition code on Pi 5
- [ ] Re-test direction-of-arrival / microphone features we want to retain
- [ ] Decide final wake/activation approach
- [ ] Turn voice recognition into a ROS 2 node
- [ ] Publish recognised speech/commands on suitable ROS topic(s)
- [ ] Keep voice path non-blocking so robot control remains responsive

## 3. Local SLM command interpreter

- [ ] Choose first local SLM/LLM to test on Pi 5
- [ ] Install/run it locally
- [ ] Measure response speed and RAM use
- [ ] Define simple structured command output
- [ ] Test natural phrases -> structured commands
- [ ] Handle multiple intents in one phrase
- [ ] Handle commands with parameters
- [ ] Handle unknown/ambiguous commands safely
- [ ] Initially print/log interpreted commands rather than moving hardware
- [ ] Connect Vosk -> local SLM -> ROS intent/command output

Example target:

```text
"It's a bit dark in here"
        ↓
Vosk
        ↓
local SLM
        ↓
{ action: set_light, brightness: 80 }
```

## 4. ROS robot architecture

- [x] Establish node/topic/controller concepts
- [x] Draft example voice -> eye-controller -> Arduino command flow
- [ ] Create main ROS 2 Python package(s)
- [ ] Implement first simple controller node with no real hardware
- [ ] Define naming convention for robot topics/messages
- [ ] Decide which commands use standard ROS messages and which need custom messages
- [ ] Implement behaviour controller
- [ ] Test a multi-subsystem behaviour such as SLEEP using simulated/logged outputs
- [ ] Establish subsystem priority/override rules
- [ ] Decide robot startup/ready/safe-state sequence

## 5. Pi <-> Arduino interface

- [ ] Decide physical Pi-Arduino connection and serial device setup
- [ ] Define simple human-readable serial protocol
- [ ] Implement single Arduino bridge/interface node on Pi
- [ ] Implement non-blocking serial parser on Arduino
- [ ] Add acknowledgements/status where useful
- [ ] Add error messages
- [ ] Add timeout/watchdog behaviour
- [ ] Define safe behaviour if Pi/ROS communication disappears
- [ ] Test high-rate serial traffic before attaching moving hardware

Possible protocol style:

```text
Pi -> Arduino:
LED,BRIGHTNESS,SET,80
EYES,POSITION,SET,120,80
ARM,...

Arduino -> Pi:
ENCODER,BRIGHTNESS,+3
ARM_POS,...
ERROR,...
```

## 6. Arduino I2C cleanup

- [ ] Recover/identify latest Arduino sketch
- [ ] Recover latest ESP32 eye firmware
- [ ] Confirm actual I2C addresses currently in use
- [ ] Remove obsolete DF2301Q voice-module code if no longer needed
- [ ] Replace old global timing/delays with per-device scheduling
- [ ] Add I2C error counters
- [ ] Add timeout/failure handling
- [ ] Add failed-device offline/retry behaviour
- [ ] Add bus recovery/reinitialisation
- [ ] Test eyes for long-duration reliability
- [ ] Test encoders/buttons without interrupt dependence where practical
- [ ] Stress-test I2C with motors/servos operating

## 7. Eyes

- [ ] Confirm current ESP32 eye command protocol
- [ ] Fix/replace old eye random-movement timer logic
- [ ] Implement ROS eye controller
- [ ] Define eye target/state/blink inputs
- [ ] Implement controller priority rules
- [ ] Preserve gaze target while blinking
- [ ] Add idle/random eye movement as a low-priority behaviour
- [ ] Test Pi -> ROS -> Arduino -> ESP32 eye path

## 8. LEDs / controls

- [ ] Implement ROS LED controller
- [ ] Read physical encoder changes through Arduino
- [ ] Publish relative encoder changes to ROS
- [ ] Keep authoritative brightness/colour state on Pi
- [ ] Send absolute LED state back to Arduino
- [ ] Support temporary animation overrides without losing user setting
- [ ] Test latency of encoder -> ROS -> LED round trip

## 9. Arm model / URDF

- [ ] Collect final CAD/STL files for modified robot
- [ ] Confirm actual arm dimensions against reference xArm model
- [ ] Define robot base and arm link hierarchy
- [ ] Set joint origins and axes
- [ ] Establish real mechanical joint limits
- [ ] Add detailed visual meshes
- [ ] Create suitable simplified collision geometry
- [ ] Model rigid head/top attachments with fixed links
- [ ] Model gripper and linked/mimic fingers if appropriate
- [ ] Configure allowed collisions for intentional interlocking/adjacent parts
- [ ] Inspect complete model in RViz

## 10. Arm / ros2_control hardware integration

- [x] Identify existing xArmServoController Arduino library
- [x] Inspect its multi-servo position command
- [x] Confirm it can request multiple servo positions
- [x] Study daira-ai ROS xArm implementation as a reference
- [x] Decide ROS side should use radians and convert at hardware boundary
- [ ] Confirm exact servo/controller hardware and servo IDs
- [ ] Measure zero position for every joint
- [ ] Measure direction/scale for every joint
- [ ] Establish safe native servo limits
- [ ] Store calibration in ROS configuration
- [ ] Implement radians <-> native servo conversion
- [ ] Implement custom ros2_control hardware interface
- [ ] Send all joint targets as one timed xArm command
- [ ] Return actual servo positions to ros2_control
- [ ] Test reliable command/feedback rate at current 9600-baud arm link
- [ ] Test initial ~10 Hz / ~100 ms command approach
- [ ] Test repeated timed-target retargeting for smoothness
- [ ] Experiment with movement duration slightly longer than update interval if useful
- [ ] Configure tracking/path/goal tolerances
- [ ] Report Arduino native-limit rejection back to ROS
- [ ] Abort/recover safely from excessive tracking error
- [ ] Run first real MoveIt trajectory on hardware at conservative speed
- [ ] Validate collision model against real motion

References:

- Hiwonder xArm Arduino library: https://github.com/ccourson/Hiwonder-xArm1S/tree/main/Arduino/xArmServoController
- ROS xArm reference implementation: https://github.com/daira-ai/xArm_Lewansoul_ROS
- Project arm notes: `docs/arm-moveit-integration.md`

## 11. Tracking / head behaviour

- [ ] Choose/update face-tracking perception source
- [ ] Publish tracked target in an appropriate coordinate frame
- [ ] Implement head tracking controller
- [ ] Query IK quickly for candidate poses without executing them
- [ ] Prefer vertical tracking while preserving X/Y where possible
- [ ] Introduce backward movement when useful for future reach
- [ ] Introduce head tilt gradually rather than at a hard limit
- [ ] Estimate target velocity
- [ ] Predict target position roughly 1–2 seconds ahead
- [ ] Start reconfiguration before reaching joint/workspace limits
- [ ] Monitor proximity to joint limits/collisions/awkward configurations
- [ ] Keep gaze tracking as primary objective during reconfiguration

## 12. Personality and behaviours

- [ ] Define basic reusable actions: blink, look, LED state, head pose, etc.
- [ ] Implement SLEEP behaviour
- [ ] Add small natural idle movements
- [ ] Add movement characteristics that reflect personality
- [ ] Add sound/reaction behaviours
- [ ] Add games/fun interactions after core control is reliable
- [ ] Ensure higher-level behaviours cannot bypass subsystem safety/controller authority

## 13. OpenAI / conversational layer — later

- [ ] Reintroduce OpenAI Realtime voice conversation
- [ ] Define when local handling is enough vs cloud AI is needed
- [ ] Add explicit web-search/tool workflow where useful
- [ ] Integrate robot functions/actions with AI safely
- [ ] Add volume control
- [ ] Decide conversation timeout/reconnect behaviour
- [ ] Preserve local commands when internet/API is unavailable

## Documentation / housekeeping

- [x] Create voice workflow proposal
- [x] Create ROS command-flow example
- [x] Create arm/MoveIt integration notes
- [x] Create living TODO checklist
- [ ] Keep this file updated as tasks are completed or priorities change
- [ ] Preserve old Arduino/ESP32 code in repository as legacy/reference
- [ ] Correct/trim obsolete notes when experiments disprove an assumption
