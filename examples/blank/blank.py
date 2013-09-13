#!/usr/bin/env python
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../emmer"))

from emmer import Emmer
app = Emmer()

if __name__ == "__main__":
    app.run()
