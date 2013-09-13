#!/usr/bin/env python
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../emmer"))

from emmer import Emmer
app = Emmer()

@app.route_read(".*")
def example_action(client_host, client_port, filename):
    return "example_output"

@app.route_write(".*")
def example_action(client_host, client_port, filename, data):
    output_file = open(filename, "w")
    output_file.write(data)

if __name__ == "__main__":
    app.run()
