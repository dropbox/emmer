import os
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "../emmer"))

from conversation_table import ConversationTable


class StubConversation(object):
    pass


class TestConversationTable(unittest.TestCase):
    def test_add_get(self):
        table = ConversationTable()
        conversation = StubConversation()
        table.add_conversation("127.0.0.1", "3942", conversation)
        self.assertEqual(table.get_conversation("127.0.0.1", "3942"),
                         conversation)
        self.assertTrue(table.lock._RLock__count == 0)

    def test_get_without_add(self):
        table = ConversationTable()
        self.assertIsNone(table.get_conversation("127.0.0.1", "3942"))
        self.assertTrue(table.lock._RLock__count == 0)

    def test_add_delete(self):
        table = ConversationTable()
        conversation = StubConversation()
        table.add_conversation("127.0.0.1", "3942", conversation)
        self.assertTrue(table.delete_conversation("127.0.0.1", "3942"))
        self.assertIsNone(table.get_conversation("127.0.0.1", "3942"))
        self.assertTrue(table.lock._RLock__count == 0)

    def test_delete_without_add(self):
        # Seems uninteresting, but this test is useful to defend against
        # exceptions
        table = ConversationTable()
        self.assertEqual(table.delete_conversation("127.0.0.1", "3942"),
                         False)
        self.assertIsNone(table.get_conversation("127.0.0.1", "3942"))
        self.assertTrue(table.lock._RLock__count == 0)

    def test_conversations(self):
        table = ConversationTable()
        conversation_one = StubConversation()
        table.add_conversation("10.0.0.1", "3942", conversation_one)
        conversation_two = StubConversation()
        table.add_conversation("10.0.0.2", "3942", conversation_two)
        # Either order of returned results is fine
        self.assertTrue(
            table.conversations == [conversation_one, conversation_two]
            or table.conversations == [conversation_two, conversation_one],
            "conversations retrieved don't match")

if __name__ == "__main__":
    unittest.main()
