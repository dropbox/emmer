#!/usr/bin/env python
"""
    emmer_bench

Furiously nukes the TFTP server with file requests, abandoning some and being
illegal in some cases. May or may not later be extended to be more
customizable.
"""
import gflags
import os
import random
import socket
import sys
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import packets

FLAGS = gflags.FLAGS

class ProgressState(object):
    """A shared object that stores the shared state of the script"""
    def __init__(self, concurrency, host, port, requests, filenames):
        self.concurrency = concurrency
        self.host = host
        self.port = port
        self.requests = requests
        self.filenames = filenames
        self.conversations = self.requests
        self.lock = threading.Lock()
        self.threads = []

    def get_filename(self):
        return random.choice(self.filenames)


def run_conversation(state, thread_num):
    """
    Run a single TFTP conversation against the TFTP server. Acts as a lousy client
    through the following properties:
    * Waits between two and six seconds before responding to a received message
    * Has a chance of dropping the connection after receiving any particular
      message.
    * In some cases will stall for twenty seconds before responding to a
      received message.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = random.randint(2000, 65535)

    sock.bind(("0.0.0.0", port))

    packet_data =  packets.ReadRequestPacket(state.get_filename(), "netascii").pack()
    print state.host, state.port
    sock.sendto(packet_data, (state.host, state.port))

    finished = False
    while not finished:
        response = sock.recvfrom(1024)
        packet_data = response[0]
        response_packet = packets.unpack_packet(packet_data)
        print "  [thread_num: %s][outward_port: %s] received %s" % (thread_num, port, response_packet)

        # A data packet of under size 512 is considered a final packet
        if len(response_packet.data) < 512:
            finished = True

        # Implement the lousy client properties as described in docstring
        time.sleep(random.randint(2, 6))
        if random.randint(0, 8) == 0:
            finished = True
        if random.randint(0, 8) == 0:
            time.sleep(20)

        ack_packet =  packets.AcknowledgementPacket(response_packet.block_num)
        print "  [%s][%s] sending %s" % (thread_num, port, ack_packet)
        sock.sendto(ack_packet.pack(), (state.host, state.port))

    sock.close()


def run_thread(state, thread_num):
    """Runs a single request thread. The thread will take one away from the
    remaining conversations counter and then run a single conversation with the
    TFTP server until the remaining conversations counter hits zero.
    """
    while state.conversations > 0:
        state.lock.acquire()
        if state.conversations > 0:
            state.conversations -= 1
            state.lock.release()
            run_conversation(state, thread_num)
        else:
            state.lock.release()

def usage_and_exit():
    print "Usage: %s hostname filename..." % sys.argv[0]
    print "Blasts a TFTP server with lousy requests"
    print FLAGS
    exit(1)

def main():
    gflags.DEFINE_integer("concurrency", 1, "concurrency", 1, short_name="c")
    gflags.DEFINE_integer("port", 69, "port of tftp server", 1, 65535,
                          short_name="p")
    gflags.DEFINE_integer("requests", 1, "amount of requests to make", 1,
                          short_name="r")
    args = FLAGS(sys.argv)

    if len(args) < 3:
        usage_and_exit()
    host = args[1]
    filenames = args[2:]

    # Initialize State
    state = ProgressState(FLAGS.concurrency, host, FLAGS.port, FLAGS.requests,
                          filenames)

    # Spawn and run threads
    for i in xrange(state.concurrency):
        th = threading.Thread(target=run_thread, args=(state, i))
        state.threads.append(th)
        th.start()

    # Wait for threads to finish
    for th in state.threads:
        th.join()


if __name__ == "__main__":
    main()
