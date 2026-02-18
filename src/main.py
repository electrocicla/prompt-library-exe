"""
Not-Meta Prompt Library – entry point.

Run directly: python src/main.py
Build to exe: see build.ps1
"""

import sys
import pathlib

# Add src/ to path so absolute imports work from the exe and dev mode
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from ui.main_window import MainWindow


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
