import os
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "../emmer"))

import packets
import tftp_conversation
from tftp_conversation import TFTPConversation
from response_router import WriteBuffer

# A set of stub readers
class StubResponseRouter(object):
    def initialize_read(self, urn, client_host, client_port):
        return StubReadBuffer()
    def initialize_write(self, urn, client_host, client_port):
        return WriteBuffer()

class StubReadBuffer(object):
    def get_block_count(self):
        return 1
    def get_block(self, block_num):
        if block_num == 1:
            return "abcde"

# A separate set of stub readers
class StubResponseRouterTwo(object):
    def initialize_read(self, urn, client_host, client_port):
        return StubReadBufferTwo()
    def initialize_write(self, urn, client_host, client_port):
        return StubWriteBufferTwo()

class StubReadBufferTwo(object):
    def get_block_count(self):
        return 3
    def get_block(self, block_num):
        # This won't be used to test any initial state
        assert block_num != 1
        if block_num == 2:
            return "X" * 512
        if block_num == 3:
            return "O" * 511

class StubWriteBufferTwo(object):
    def receive_data(self, data):
        self.data = data

# Stub reader for no action case
class NoActionAvailableResponseRouterStub(object):
    def initialize_read(self, urn, client_host, client_port):
        return None
    def initialize_write(self, urn, client_host, client_port):
        return None

class StubWriteActionWrapper(object):
    def stub_action(self, host, port, filename, data):
        self.received_state = (host, port, filename, data)

class TestTFTPConversationGeneral(unittest.TestCase):
    def setUp(self):
        self.client_host = "10.26.0.3"
        self.client_port = 12345

    def test_init(self):
        conversation = TFTPConversation(self.client_host, self.client_port, StubResponseRouter())
        self.assertEqual(conversation.client_host, "10.26.0.3")
        self.assertEqual(conversation.client_port, 12345)

    def test_illegal_acknowledgement_packet_during_uninitialized_state(self):
        packet = packets.AcknowledgementPacket(3)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        response_packet = conversation.handle_packet(packet)
        self.assertEqual(conversation.state, tftp_conversation.COMPLETED)
        self.assertEqual(response_packet.__class__, packets.ErrorPacket)
        self.assertEqual(response_packet.error_code, 5)

    def test_mark_retry(self):
        original_packet = packets.AcknowledgementPacket(3)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.cached_packet = original_packet
        retry_packet = conversation.mark_retry()
        self.assertEqual(conversation.retries_made, 1)
        self.assertEqual(retry_packet, original_packet)

    def test_reset_retry_and_time_data(self):
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.retries_made = 39
        conversation.time_of_last_interaction = 42
        conversation._reset_retry_and_time_data(9001)
        self.assertEqual(conversation.retries_made, 0)
        self.assertEqual(conversation.time_of_last_interaction, 9001)


class TestTFTPConversationRead(unittest.TestCase):
    def setUp(self):
        self.client_host = "10.26.0.3"
        self.client_port = 12345

    def test_no_action_for_reading(self):
        packet = packets.ReadRequestPacket("example_filename", "netascii")
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        NoActionAvailableResponseRouterStub())
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.COMPLETED)
        self.assertEqual(response_packet.__class__, packets.ErrorPacket)
        self.assertEqual(response_packet.error_code, 1)

    def test_begin_reading(self):
        packet = packets.ReadRequestPacket("example_filename", "netascii")
        conversation = TFTPConversation(self.client_host, self.client_port, StubResponseRouter())
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.READING)
        self.assertEqual(conversation.filename, "example_filename")
        self.assertEqual(conversation.mode, "netascii")
        self.assertEqual(conversation.current_block_num, 1)
        self.assertEqual(conversation.read_buffer.__class__, StubReadBuffer)
        self.assertEqual(response_packet.__class__, packets.DataPacket)
        self.assertEqual(conversation.cached_packet, response_packet)

    def test_continue_reading(self):
        packet = packets.AcknowledgementPacket(1)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.state = tftp_conversation.READING
        conversation.read_buffer = StubReadBufferTwo()
        conversation.current_block_num = 1
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.READING)
        self.assertEqual(conversation.current_block_num, 2)
        self.assertEqual(response_packet.data, "X" * 512)
        self.assertEqual(response_packet.__class__, packets.DataPacket)
        self.assertEqual(conversation.cached_packet, response_packet)

    def test_finish_reading(self):
        packet = packets.AcknowledgementPacket(3)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.filename = "example_filename"
        conversation.state = tftp_conversation.READING
        conversation.current_block_num = 3
        conversation.read_buffer = StubReadBufferTwo()
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.COMPLETED)
        self.assertEqual(response_packet.__class__, packets.NoOpPacket)
        self.assertEqual(conversation.cached_packet, response_packet)

    def test_illegal_packet_type_during_reading_state(self):
        packet = packets.DataPacket(2, "")
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.cached_packet = "stub packet"
        conversation.state = tftp_conversation.READING
        conversation.read_buffer = StubReadBufferTwo()
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.READING)
        self.assertEqual(response_packet.__class__, packets.ErrorPacket)
        self.assertEqual(response_packet.error_code, 0)
        self.assertEqual(conversation.cached_packet, "stub packet")

    def test_out_of_lock_step_block_num(self):
        packet = packets.AcknowledgementPacket(2)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.cached_packet = "stub packet"
        conversation.state = tftp_conversation.READING
        conversation.current_block_num = 1
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.READING)
        self.assertEqual(response_packet.__class__, packets.NoOpPacket)


class TestTFTPConversationWrite(unittest.TestCase):
    def setUp(self):
        self.client_host = "10.26.0.3"
        self.client_port = 12345

    def test_no_action_for_writing(self):
        packet = packets.WriteRequestPacket("example_filename", "netascii")
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        NoActionAvailableResponseRouterStub())
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.COMPLETED)
        self.assertEqual(response_packet.__class__, packets.ErrorPacket)
        self.assertEqual(response_packet.error_code, 2)

    def test_begin_writing(self):
        packet = packets.WriteRequestPacket("example_filename", "netascii")
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouter())
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.WRITING)
        self.assertEqual(conversation.filename, "example_filename")
        self.assertEqual(conversation.mode, "netascii")
        self.assertEqual(conversation.current_block_num, 0)
        self.assertEqual(conversation.write_buffer.__class__, WriteBuffer)
        self.assertEqual(conversation.cached_packet, response_packet)
        self.assertEqual(response_packet.__class__, packets.AcknowledgementPacket)
        self.assertEqual(response_packet.block_num, 0)

    def test_continue_writing(self):
        packet = packets.DataPacket(2, "X" * 512)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.state = tftp_conversation.WRITING
        conversation.write_buffer = StubWriteBufferTwo()
        conversation.current_block_num = 1
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.WRITING)
        self.assertEqual(conversation.current_block_num, 2)
        self.assertEqual(conversation.write_buffer.data, "X" * 512)
        self.assertEqual(conversation.cached_packet, response_packet)
        self.assertEqual(response_packet.__class__, packets.AcknowledgementPacket)
        self.assertEqual(response_packet.block_num, 2)

    def test_finish_writing(self):
        packet = packets.DataPacket(3, "O" * 511)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.state = tftp_conversation.WRITING
        conversation.write_buffer = WriteBuffer()
        conversation.write_buffer.data = "X" * 512
        conversation.filename = "stub_filename"
        conversation.current_block_num = 2
        write_action_wrapper = StubWriteActionWrapper()
        conversation.write_action = write_action_wrapper.stub_action
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.COMPLETED)
        self.assertEqual(conversation.current_block_num, 3)
        self.assertEqual(conversation.cached_packet, response_packet)
        self.assertEqual(response_packet.__class__, packets.AcknowledgementPacket)
        self.assertEqual(response_packet.block_num, 3)
        # action should get invoked, saving this state in the wrapper class
        self.assertEqual(write_action_wrapper.received_state,
            ("10.26.0.3", 12345, "stub_filename", "X" * 512 + "O" * 511))

    def test_illegal_packet_type_during_writing_state(self):
        packet = packets.AcknowledgementPacket(2)
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.cached_packet = "stub packet"
        conversation.state = tftp_conversation.WRITING
        conversation.read_buffer = StubReadBufferTwo()
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.WRITING)
        self.assertEqual(response_packet.__class__, packets.ErrorPacket)
        self.assertEqual(response_packet.error_code, 0)
        self.assertEqual(conversation.cached_packet, "stub packet")

    def test_out_of_lock_step_block_num(self):
        packet = packets.DataPacket(2, "")
        conversation = TFTPConversation(self.client_host, self.client_port,
                                        StubResponseRouterTwo())
        conversation.cached_packet = "stub packet"
        conversation.state = tftp_conversation.WRITING
        conversation.current_block_num = 3
        response_packet = conversation.handle_packet(packet)

        self.assertEqual(conversation.state, tftp_conversation.WRITING)
        self.assertEqual(response_packet.__class__, packets.NoOpPacket)


if __name__ == "__main__":
    unittest.main()
