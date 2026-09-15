# Robot Voice Assistant

A Raspberry Pi-based voice assistant project.

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
