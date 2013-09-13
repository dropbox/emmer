# Examples

This directory contains various basic example uses of Emmer.

* blank
  Runs a TFTP server that has no routes. It will refuse every
  connection, but demonstrates basic usage of Emmer.

* basic
  Runs a TFTP server that has two routes to demonstrate reads and
  writes.

* moderate
  Demonstrates how different functions can be invoked based on different
  client filenames, and different output can be flexibly returned based on
  filename, client host, or client port.

  The write example demonstrates that you don't necessarily have to save
  the data from a write to your disk. It also demonstrates how to modify
  the server configuration to change the port that the server is running
  on.

  Also demonstrates use of logging.
