import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent.parent
    subprocess.run(
        [
            "jupyter",
            "lab",
            "--config=.jupyter/jupyter_notebook_config.py",
            *sys.argv[1:],
        ],
        cwd=root,
        check=False,
    )
