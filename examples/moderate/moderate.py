#!/usr/bin/env python
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../emmer"))

import emmer
from emmer import Emmer

emmer.config.PORT = 69
emmer.config.HOST = "0.0.0.0"
app = Emmer()

logging_format = '%(asctime)s %(message)s'
logging.basicConfig(format=logging_format, level=logging.DEBUG)

@app.route_read("data/.*")
def example_action(client_host, client_port, filename):
    return "output from the data \"directory\": filename: %s" % filename

@app.route_read("file_example")
def get_passwd_lol(client_host, client_port, filename):
    return open("/boot/memtest86+.bin").read()

@app.route_read("example_directory/.*")
def example_action(client_host, client_port, filename):
    # Arbitrary way to show that you can have varying output based on these
    # inputs
    if client_port > 30000:
        return ("output from the example \"directory\": filename: %s."
                " You are using a high port number and the filename: " % filename)
    else:
        return ("output from the bear \"directory\": filename: %s."
                " You are using a low port number and the filename: " % filename)

@app.route_read("healthcheck")
def healthcheck(client_host, client_port, filename):
    return "OK"

@app.route_write(".*")
def example_action(client_host, client_port, filename, data):
    print ("client host %s from client port %s just sent a file called %s."
           " Data: %s" % (client_host, client_port, filename, data))

if __name__ == "__main__":
    app.run()
