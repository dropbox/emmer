import socket
import thread

import config
from conversation_table import ConversationTable
from reactor import Reactor
from response_router import ResponseRouter
from performer import Performer


class Emmer(object):
    """This is the wrapping class for the Emmer framework. It initializes
    running services and also offers the client level interface.
    """
    def __init__(self):
        self.host = config.HOST
        self.port = config.PORT
        self.response_router = ResponseRouter()
        self.conversation_table = ConversationTable()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.reactor = Reactor(self.sock, self.response_router,
                               self.conversation_table)
        self.performer = Performer(self.sock, self.conversation_table,
                                   config.RESEND_TIMEOUT,
                                   config.RETRIES_BEFORE_GIVEUP)

    def route_read(self, filename_pattern):
        """Adds a function with a filename pattern to the Emmer server. Upon a
        read request, Emmer will run the action corresponding to the first
        filename pattern to match the request's filename.

        Use this function as a decorator on a function to add that function
        as an action with which to handle a tftp conversation.

        Args:
            filename_pattern: a regex pattern to match filenames against.
        """
        def decorator(action):
            self.response_router.append_read_rule(filename_pattern, action)

        return decorator

    def route_write(self, filename_pattern):
        """Adds a function with a filename pattern to the Emmer server. Upon a
        write request, Emmer will run the action corresponding to the first
        filename pattern to match the request's filename.

        Use this function as a decorator on a function to add that function
        as an action with which to handle a tftp conversation.

        Args:
            filename_pattern: a regex pattern to match filenames against.
        """
        def decorator(action):
            self.response_router.append_write_rule(filename_pattern, action)

        return decorator

    def run(self):
        """Initiates the Emmer server. This includes:
        * Listening on the given UDP host and port.
        * Sending messages through the given port to reach out on timed out
          tftp conversations.
        """
        self.sock.bind((self.host, self.port))
        print "TFTP Server running at %s:%s" % (self.host, self.port)
        thread.start_new_thread(self.performer.run,
                                (config.PERFORMER_THREAD_INTERVAL,))
        self.reactor.run()
