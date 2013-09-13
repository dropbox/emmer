# Emmer TFTP Server

A framework for dynamic tftp servers. Serve data through tftp
independently from your file system, based on client IP, Port, request
filename, or even on some other form of server stored state.

The interface is inspired by the Flask framework.

Emmer is a work in progress and is very basic right now. Bug reports and
contribution are welcome!.

# Author

Emmer is built by David Mah, a former intern on the Site Reliability
Team at Dropbox. You can contact mahhaha at gmail about this.

# Diving In

A very small basic application:

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

## Basic Usage Explanation

You must include this at the top of your file in order to import the
framework.

    from emmer import Emmer
    app = Emmer()

Include this annotation, and every read request that regex matches the
passed in filename will execute your function before transferring any
data.

    @app.route_read(".*")
    def example_action(client_host, client_port, filename):
        return "example_output"

Include this annotation, and every write request that regex matches the
passed in filename will execute your function after receiving the data.
If a request comes that doesn't match any of your routes, then it will
be immediately rejected.

    @app.route_write(".*")
    def example_action(client_host, client_port, filename, data):
        output_file = open(filename, "w")
        output_file.write(data)

Finally, now that you have added your routes, the following code will
start up the server and begin listening!

    if __name__ == "__main__":
        app.run()

Note that this application would be considered insecure. A directory
traversal attack would allow a client to write to arbitrary locations on
your disk. Having said that, that layer of security is left for the
client to design and control.

## Deeper Configuration

By default, Emmer runs on port 3942 as a development port and runs under
the host 127.0.0.1, which allows only local access to the server. You
can modify server configuration settings by changing values in
emmer.config.

    import emmer
    emmer.config.HOST = "0.0.0.0"
    emmer.config.port = 69

Emmer uses the logging module, which can be imported and configured by
the application.

## Implementation Details

See *emmer/README.md*.

# Todo List

Features:
* Support for put operation
  * Hook at the beginning of the put operation. Allow for accept/deny
    before the transfer even occurs.
  * Upload reject at the end of the upload if the user returns False.
* Options support
  * block sizes other than 512
  * timeout
* octet and binary support
* Support for Overriding WriteBuffer/ReadBuffer
