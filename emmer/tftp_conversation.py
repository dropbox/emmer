import logging
import calendar
import threading
import time

import packets
from response_router import WriteBuffer
from utility import lock

UNINITIALIZED = 0
WRITING = 1
READING = 2
COMPLETED = 3


class TFTPConversation(object):
    """A TFTPConversation represents a single conversation between one client
    and this server. It acts as a state machine that manages the process of
    handling a tftp operation.

    Properties:
        current_block_num: Equivalent to the block number that is attached to
            the packet most recently sent out by the conversation.
        cached_packet: The most recently sent non error packet from this
            conversation. Use for retries.
        time_of_last_interaction: The seconds since epoch of the most recently
            received legal packet. Use for timeouts.
    """
    def __init__(self, client_host, client_port, response_router):
        """Initializes a TFTPConversation with the given client.

        Args:
            client_host: The ip or hostname of the client.
            client port: The port that the clietn is connecting from
            response_router: A response router to handle reads/writes to the
                tftp server.
        """
        self.cached_packet = None
        self.client_host = client_host
        self.client_port = client_port
        self.lock = threading.Lock()
        self.response_router = response_router
        self.retries_made = 0
        self.state = UNINITIALIZED
        self.time_of_last_interaction = calendar.timegm(time.gmtime())

    @lock
    def handle_packet(self, packet):
        """Takes a packet from the client and advances the state machine
        depending on that packet. Resets the time of last interaction and the
        retries made count. Caches the output packet in case it needs to be
        resent, unless the output packet is an ErrorPacket. In that case, it
        maintains whatever previously was in the cache.

        Args:
            packet: A packet object that has already been unpacked.

        Returns:
            a packet object with which to send back to the client. Returns a
            NoOpPacket if the conversation has ended.
        """
        if self.state == UNINITIALIZED:
            output_packet = self._handle_initial_packet(packet)
        elif self.state == READING:
            output_packet = self._handle_read_packet(packet)
        elif self.state == WRITING:
            output_packet = self._handle_write_packet(packet)
        else:
            # TODO: Replace with a more appropriate exception type?
            raise Exception("Illegal State of TFTPConversation")

        # Only cache the packet and mark this packet as an interaction with
        # regards to timeouts if this did not result in an ErrorPacket
        if not isinstance(output_packet, packets.ErrorPacket):
            self.cached_packet = output_packet
            self._reset_retry_and_time_data()
        return output_packet

    def _handle_initial_packet(self, packet):
        """Takes a packet from the client and advances the state machine
        depending on that packet. This should only be invoked from the
        UNINITIALIZED state.

        Args:
            packet: A packet object that has already been unpacked.

        Returns:
            a packet object with which to send back to the client.
        """
        assert self.state == UNINITIALIZED
        if isinstance(packet, packets.ReadRequestPacket):
            return self._handle_initial_read_packet(packet)
        if isinstance(packet, packets.WriteRequestPacket):
            return self._handle_initial_write_packet(packet)
        else:
            self.state = COMPLETED
            return packets.ErrorPacket(5, "Unknown transfer tid."
                "Host: %s, Port: %s" % (self.client_host, self.client_port))

    def _handle_initial_read_packet(self, packet):
        """Check if there is an application action to respond to this
        request If so, then send the first block and move the state to
        READING. Otherwise, send back an error packet and move the state
        to COMPLETED.

        Args:
            packet: An unpacked ReadRequestPacket.

        Returns:
            A Data packet if the request's filename matches any possible read
            rule. The data packet includes the first block of data from the
            output of the read action. Otherwise, an ErrorPacket with a file
            not found error code and message.
        """
        assert isinstance(packet, packets.ReadRequestPacket)
        self.filename = packet.filename
        self.mode = packet.mode
        self.read_buffer = self.response_router.initialize_read(
            self.filename, self.client_host, self.client_port)
        if self.read_buffer:
            self.state = READING
            data = self.read_buffer.get_block(1)
            self.current_block_num = 1
            return packets.DataPacket(1, data)
        else:
            self.log("READREQUEST", "File not found")
            self.state = COMPLETED
            return packets.ErrorPacket(1, "File not found. Host: %s, Port: %s"
                % (self.client_host, self.client_port))
    def _handle_initial_write_packet(self, packet):

        """ Check if there is an application action to receive this message.
        If so, then send an acknowledgement and move the state to WRITING.
        Otherwise, send back an error packet and move the state to COMPLETED.

        Args:
            packet: An unpacked WriteRequestPacket.

        Returns:
            An Acknowledgement packet if the request's filename matches any
            possible write rule. Otherwise, an ErrorPacket with an access
            violation code and message.
        """
        assert isinstance(packet, packets.WriteRequestPacket)
        self.filename = packet.filename
        self.mode = packet.mode
        self.current_block_num = 0
        self.write_action = self.response_router.initialize_write(
            self.filename, self.client_host, self.client_port)
        if self.write_action:
            self.state = WRITING
            self.write_buffer = WriteBuffer()
            return packets.AcknowledgementPacket(0)
        else:
            self.state = COMPLETED
            self.log("WRITEREQUEST", "Access Violation")
            return packets.ErrorPacket(2, "Access Violation. Host: %s, Port: %s"
                % (self.client_host, self.client_port))

    def _handle_read_packet(self, packet):
        """Takes a packet from the client and advances the state machine
        depending on that packet. This should only be invoked from the READING
        state. Returns an appropriate DataPacket containing the next block of
        data.

        Args:
            packet: A packet object that has already been unpacked.

        Returns:
            a packet object with which to send back to the client.
        """
        assert self.state == READING
        if not isinstance(packet, packets.AcknowledgementPacket):
            return packets.ErrorPacket(0, "Illegal packet type given"
                  " current state of conversation.  Host: %s, Port: %s."
                  % (self.client_host, self.client_port))
        if self.current_block_num != packet.block_num:
            return packets.NoOpPacket()

        previous_block_num = packet.block_num
        if previous_block_num == self.read_buffer.get_block_count():
            self.state = COMPLETED
            self.log("READREQUEST", "Success")
            return packets.NoOpPacket()
        else:
            self.current_block_num += 1
            data = self.read_buffer.get_block(self.current_block_num)
            return packets.DataPacket(self.current_block_num, data)

    def _handle_write_packet(self, packet):
        """Takes a packet from the client and advances the state machine
        depending on that packet. This should only be invoked from the WRITING
        state. If given the last packet in a data transfer (bytes of data is
        less than 512), then invokes the application level action with all of
        the data from the conversation.

        Args:
            packet: A packet object that has already been unpacked.

        Returns:
            An appropriate AcknowledgementPacket containing a matching block
            number.
        """
        assert self.state == WRITING
        if not isinstance(packet, packets.DataPacket):
            return packets.ErrorPacket(0, "Illegal packet type given"
                                          " current state of conversation")
        # Add one because acknowledgements are always behind one block number
        if self.current_block_num + 1 != packet.block_num:
            return packets.NoOpPacket()

        block_num = packet.block_num
        self.write_buffer.receive_data(packet.data)
        if len(packet.data) < 512:
            self.state = COMPLETED
            self.log("WRITEREQUEST", "Success")
            self.write_action(self.client_host, self.client_port,
                              self.filename, self.write_buffer.data)
        self.current_block_num += 1
        return packets.AcknowledgementPacket(block_num)

    def _reset_retry_and_time_data(self, new_time_of_last_interaction=None):
        """Resets the time since last interaction to the new time and sets the
        retries made count to 0.

        Args:
            new_time_of_last_interaction: The time to set the
                time_since_last_interaction to (seconds since epoch). If None
                passed, then use the current time since epoch.
        """
        self._update_time_of_last_interaction(new_time_of_last_interaction)
        self.retries_made = 0

    @lock
    def mark_retry(self, new_time_of_last_interaction=None):
        """Increases the stored count of sending attempts made with the most
        recent outward packet.

        Returns:
            The packet to send out.
        """
        self._update_time_of_last_interaction(new_time_of_last_interaction)
        self.retries_made += 1
        return self.cached_packet

    def _update_time_of_last_interaction(self,
                                         new_time_of_last_interaction=None):
        """Sets the time of the last interaction for this conversation.

        Args:
            new_time_of_last_interaction: An integer representing seconds since
            epoch to be used as the new time_of_last_intersection. If None is
            passed, uses the current amount of seconds since epoch.
        """
        if not new_time_of_last_interaction:
            new_time_of_last_interaction = calendar.timegm(time.gmtime())
        self.time_of_last_interaction = new_time_of_last_interaction

    def log(self, request_type, comment):
            logging.info("%s:%s - %s - %s - %s"
                    % (self.client_host, self.client_port, request_type,
                        self.filename, comment))

