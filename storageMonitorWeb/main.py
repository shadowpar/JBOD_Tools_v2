#!/usr/bin/python3
import sys
from pathlib import Path
parent = Path(__file__).parent.absolute().parent.absolute().parent.absolute()
parent = str(parent)
if parent not in sys.path:
    sys.path.append(parent)
print(sys.path)

from . import app

if __name__ == "__main__":
    app.run(host='0.0.0.0')
