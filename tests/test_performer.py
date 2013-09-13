import os
import sys
import tftp_conversation
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "../emmer"))

from conversation_table import ConversationTable
from performer import Performer


class StubPacket(object):
    def pack(self):
        return "stub_packet_data"


class StubConversation(object):
    def __init__(self, time_of_last_interaction):
        self.time_of_last_interaction = time_of_last_interaction
        self.cached_packet = StubPacket()
        self.client_host = "stub_host"
        self.client_port = "stub_port"

    def mark_retry(self):
        return self.cached_packet


class StubSocket(object):
    def __init__(self):
        self.sent_data = None
        self.sent_addr = None

    def sendto(self, data, addr):
        self.sent_data = data
        self.sent_addr = addr


class TestPerformer(unittest.TestCase):
    def setUp(self):
        self.sock = StubSocket()

    def test_get_stale_conversations(self):
        table = ConversationTable()
        conversation_one = StubConversation(12344)
        conversation_two = StubConversation(12345)
        conversation_three = StubConversation(12346)
        table.conversation_table = {
            ("10.26.0.1", "3942"): conversation_one,
            ("10.26.0.2", "3942"): conversation_two,
            ("10.26.0.3", "3942"): conversation_three
        }

        performer = Performer(self.sock, table, 10, 6)

        # Either order of returned results is fine
        self.assertTrue(performer._get_stale_conversations(5, 12350)
            == [conversation_one, conversation_two]
            or performer.get_stale_conversations(5, 12350)
            == [conversation_two, conversation_one],
            "stale conversations found don't match")

    def test_handle_stale_conversation_retry(self):
        conversation = StubConversation(12344)
        conversation.retries_made = 0
        table = ConversationTable()
        performer = Performer(self.sock, table, 10, 6)
        performer._handle_stale_conversation(conversation)
        self.assertEqual(self.sock.sent_data, "stub_packet_data")
        self.assertEqual(self.sock.sent_addr, ("stub_host", "stub_port"))

    def test_handle_stale_conversation_giveup(self):
        conversation = StubConversation(12344)
        conversation.retries_made = 6
        table = ConversationTable()
        table.add_conversation("stub_host", "stub_port", conversation)
        performer = Performer(self.sock, table, 10, 6)
        performer._handle_stale_conversation(conversation)
        self.assertEqual(self.sock.sent_data,
            '\x00\x05\x00\x00Conversation Timed Out\x00')
        self.assertEqual(self.sock.sent_addr, ("stub_host", "stub_port"))
        self.assertIsNone(table.get_conversation("stub_host", "stub_port"), None)

    def test_find_and_handle_stale_conversations(self):
        conversation = StubConversation(12344)
        conversation.retries_made = 6
        table = ConversationTable()
        table.add_conversation("stub_host", "stub_port", conversation)
        performer = Performer(self.sock, table, 10, 6)
        performer.find_and_handle_stale_conversations()
        self.assertEqual(len(table), 0)

    def test_sweep_completed_conversations(self):
        conversation_one = StubConversation(12344)
        conversation_one.state = tftp_conversation.COMPLETED

        conversation_two = StubConversation(12345)
        conversation_two.state = tftp_conversation.READING

        conversation_three = StubConversation(12346)
        conversation_three.state = tftp_conversation.COMPLETED

        table = ConversationTable()
        table.conversation_table = {
                ("10.26.0.1", "3942"): conversation_one,
                ("10.26.0.2", "3942"): conversation_two,
                ("10.26.0.3", "3942"): conversation_three
        }

        performer = Performer(self.sock, table, 10, 6)
        performer.sweep_completed_conversations()
        self.assertEqual(table.conversation_table,
            {("10.26.0.2", "3942"): conversation_two, })
