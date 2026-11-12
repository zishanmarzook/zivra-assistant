"""PyInstaller entry point; normal development uses python -m zivra."""
from zivra.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
