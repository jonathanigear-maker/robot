# Robot Voice Assistant

A Raspberry Pi-based voice assistant project.

## Git and GitHub setup

Install Git on a fresh Pi:

```bash
sudo apt update
sudo apt install -y git
git --version
```

Configure the name and email used for commits:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Clone the robot repository:

```bash
git clone https://github.com/jonathanigear-maker/robot.git
cd robot
```

### GitHub authentication for pushing

Cloning a public repository does not require a login, but **pushing changes does require GitHub authentication**. GitHub does not accept an account password for Git operations over HTTPS.

On a fresh Pi, authenticate before the first push using your chosen GitHub authentication method (for example GitHub CLI/device login or a personal access token). Once authentication is configured, normal pushes can be made with:

```bash
git add .
git commit -m "Describe the change"
git push
```

Do not store GitHub access tokens or other credentials in this repository.

## Python environment setup

Raspberry Pi OS already includes Python. Check the installed version:

```bash
python3 --version
```

Update the package list and install virtual-environment support:

```bash
sudo apt update
sudo apt install -y python3-venv
```

Create the project directory and virtual environment:

```bash
mkdir -p ~/robot
cd ~/robot
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

The terminal prompt should now begin with `(.venv)`.

Confirm that the virtual environment's Python is active:

```bash
which python
```

Expected path:

```text
/home/jgear/robot/.venv/bin/python
```

Upgrade `pip` inside the environment:

```bash
python -m pip install --upgrade pip
```

## Voice chat setup

The voice assistant uses the ReSpeaker microphone array for audio input, Vosk for local speech recognition/commands, and the OpenAI API for conversational voice.

### System packages

Install the Linux audio/development packages needed by the Python audio stack:

```bash
sudo apt update
sudo apt install -y alsa-utils portaudio19-dev python3-dev
```

Useful checks for the ReSpeaker/audio devices:

```bash
arecord -l
aplay -l
```

### Python packages

Activate the project virtual environment first:

```bash
cd ~/robot
source .venv/bin/activate
```

Then install the voice-chat dependencies used by the project:

```bash
pip install openai websockets vosk sounddevice python-dotenv
```

- `openai` — OpenAI API client.
- `websockets` — WebSocket communication used for realtime voice.
- `vosk` — local/offline speech recognition and command detection.
- `sounddevice` — microphone capture/playback through PortAudio.
- `python-dotenv` — loads secrets such as the OpenAI API key from `.env`.

### OpenAI API key

Create a `.env` file in the project directory:

```text
OPENAI_API_KEY=your_api_key_here
```

Never commit this file to GitHub.

### ReSpeaker

The robot currently uses the **ReSpeaker 4-Mic Array with XVF3800**. It appears to Linux as an audio device and can be inspected with ALSA tools such as `arecord`.

We also added a udev rule while configuring access to the ReSpeaker:

```text
/etc/udev/rules.d/99-respeaker.rules
```

After changing udev rules, reload them with:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Keep any ReSpeaker-specific setup/calibration scripts with the project documentation so a fresh Pi installation can be reproduced.

### Vosk model

Vosk requires a local speech-recognition model. The model files should be downloaded separately and kept out of Git if they are large. Configure the program with the path to the installed model.

Vosk is intended to handle local commands/wake behaviour without sending every command to the OpenAI API. The OpenAI realtime connection can then be opened for full conversational interaction when required.

## Starting a new development session

Whenever you open a new terminal or SSH session:

```bash
cd ~/robot
source .venv/bin/activate
```

Before installing packages, check that the prompt begins with `(.venv)`.

Do not use `sudo pip` or `--break-system-packages`. Install project dependencies inside the virtual environment.

## Leaving the environment

```bash
deactivate
```

## Files that should not be committed

The repository's `.gitignore` should include:

```gitignore
.venv/
__pycache__/
*.pyc
.env
```

The `.env` file may contain API keys and must never be committed to GitHub.

## Future robot platform

The planned robot platform is Raspberry Pi 5 with Ubuntu 24.04 ARM64, ROS 2 Jazzy and MoveIt 2. The Arduino can remain as the low-level hardware controller for servos, buttons and other devices, with ROS communicating with it from the Pi.
