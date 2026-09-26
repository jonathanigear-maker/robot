import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPENAI_VOICE = PROJECT_ROOT / "src" / "openai_voice.py"


def open():
    """Open the online OpenAI voice conversation."""

    print("BIG BRAIN: Opening...")

    subprocess.run(
        [sys.executable, str(OPENAI_VOICE)]
    )

    print("BIG BRAIN: Closed.")