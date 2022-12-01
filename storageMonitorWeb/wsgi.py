#!/usr/bin/python3.6
import sys
from pathlib import Path
from pprint import pprint
parent = Path(__file__).parent.absolute().parent.absolute().as_posix()
if parent not in sys.path:
    sys.path.append(parent)
from storageMonitorWeb import app
if __name__ == "__main__":
    app.run()
