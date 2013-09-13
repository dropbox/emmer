import logging
import thread

import packets
from tftp_conversation import TFTPConversation


class Reactor(object):
    """A Reactor object runs the event loop and handles incoming requests. It
    polls a socket for messages and forwards them to conversations in a
    conversation table.

    A client of this module should call the run function in order to
    permanently listen on the given port.
    """
    def __init__(self, sock, response_router, conversation_table):
        """
        Args:
            sock: A socket to listen for messages on.
            response_router: A response router object used to hook application
                level actions into conversations.
            conversation_mangager: A conversation table object to poll and
                store conversations to.
        """
        self.response_router = response_router
        self.conversation_table = conversation_table
        self.sock = sock

    def run(self):
        """Runs the Reactor, listening on the socket given by this
        reactor's host and port. The socket should already be bound. This
        function invocation will never return.
        """
        while True:
            data, addr = self.sock.recvfrom(1024)
            thread.start_new_thread(self.handle_message,
                                    (self.sock, addr, data))

    def handle_message(self, sock, addr, data):
        """Accepts and responds (if applicable) to a message.

        Args:
            sock: The socket that the message originated from.
            addr: A tuple representing (client host, client port).
            data: Data received in a message from the client.
        """
        client_host = addr[0]
        client_port = addr[1]
        packet = packets.unpack_packet(data)
        logging.debug("%s:%s:   received: %s"
                      % (client_host, client_port, packet))

        # Invalid Packets are NoOp
        if isinstance(packet, packets.NoOpPacket):
            logging.info("Invalid packet received: %s" % data)
            return

        conversation = self.get_conversation(client_host, client_port, packet)
        response_packet = conversation.handle_packet(packet)
        self.respond_with_packet(client_host, client_port,
                response_packet)


    def get_conversation(self, client_host, client_port, packet):
        """Given a packet and client address information, retrieves the
        corresponding conversation. Read and Write request packets initiate new
        conversations, adding them to the conversation manager. Everything else
        retrieves preexisting conversations.

        Args:
            client_host: A hostname or ip address of the client.
            client_port: The port from which the client is connecting.
            packet: The packet that the client sent unpacked.

        Returns:
            A conversation.
        """
        if (isinstance(packet, (packets.WriteRequestPacket,
                                packets.ReadRequestPacket))):
            conversation = TFTPConversation(client_host, client_port,
                                            self.response_router)
            self.conversation_table.add_conversation(
                client_host, client_port, conversation)
        else:
            conversation = (
                self.conversation_table.get_conversation(client_host,
                                                         client_port))
        return conversation

    def respond_with_packet(self, client_host, client_port, packet):
        """Given client address information and a packet, packs the packet and
        sends it to the client.

        Args:
            client_host: A hostname or ip address of the client.
            client_port: The port from which the client is connecting.
            packet: The packet to send to the client. If given a NoOpPacket,
                does not send anything to the client.
        """
        if not isinstance(packet, packets.NoOpPacket):
            logging.debug("    sending: %s" % packet)
            self.sock.sendto(packet.pack(), (client_host, client_port))
