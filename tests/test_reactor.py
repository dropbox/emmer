import unittest

import packets
from conversation_table import ConversationTable
from reactor import Reactor
from tftp_conversation import TFTPConversation

class TestReactor(unittest.TestCase):

    def test_get_conversation_new_with_reading_packet(self):
        conversation_table = ConversationTable()
        packet = packets.ReadRequestPacket('stub filename', 'stub mode')
        reactor = Reactor('stub_socket', 'stub_router', conversation_table)
        conversation = reactor.get_conversation('10.26.0.1', 3942, packet)
        self.assertEqual(len(conversation_table), 1)
        self.assertTrue(isinstance(conversation, TFTPConversation))

    def test_get_conversation_new_with_writing_packet(self):
        conversation_table = ConversationTable()
        packet = packets.WriteRequestPacket('stub filename', 'stub mode')
        reactor = Reactor('stub_socket', 'stub_router', conversation_table)
        conversation = reactor.get_conversation('10.26.0.1', 3942, packet)
        self.assertEqual(len(conversation_table), 1)
        self.assertTrue(isinstance(conversation, TFTPConversation))

    def test_get_conversation_old_with_acknowledge_packet(self):
        conversation_table = ConversationTable()
        packet = packets.AcknowledgementPacket('stub block number')
        old_conversation = TFTPConversation('10.26.0.1', 3942, 'stub_router')
        conversation_table.add_conversation('10.26.0.1', 3942, old_conversation)
        reactor = Reactor('stub_socket', 'stub_router', conversation_table)
        conversation = reactor.get_conversation('10.26.0.1', 3942, packet)
        self.assertEqual(len(conversation_table), 1)
        self.assertTrue(isinstance(conversation, TFTPConversation))
        self.assertEqual(conversation, old_conversation)

    def test_get_conversation_old_with_data_packet(self):
        conversation_table = ConversationTable()
        packet = packets.DataPacket('stub block number', 'stub data')
        old_conversation = TFTPConversation('10.26.0.1', 3942, 'stub_router')
        conversation_table.add_conversation('10.26.0.1', 3942, old_conversation)
        reactor = Reactor('stub_socket', 'stub_router', conversation_table)
        conversation = reactor.get_conversation('10.26.0.1', 3942, packet)
        self.assertEqual(len(conversation_table), 1)
        self.assertTrue(isinstance(conversation, TFTPConversation))
        self.assertEqual(conversation, old_conversation)


if __name__ == '__main__':
    unittest.main()

