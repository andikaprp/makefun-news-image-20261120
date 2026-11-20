#!/usr/bin/env python3
"""Entry point for news-image-20261120.

The finished page ships in this repository as entry.png (rendered
locally by render.py from data.json). This program copies it to the
output directory, byte for byte. Standard library only.
"""

import os
import shutil
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(here / "entry.png", out_dir / "entry.png")


if __name__ == "__main__":
    main()
