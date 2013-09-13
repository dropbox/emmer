import os
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "../emmer"))
from response_router import ResponseRouter


class TestResponseRouter(unittest.TestCase):
    def setUp(self):
        self.router = ResponseRouter()
        # These lambda functions simulate user actions
        self.router.append_read_rule("test1", lambda x, y, z: "1")
        self.router.append_read_rule("test2", lambda x, y, z: "2")
        self.router.append_read_rule("test3.*", lambda x, y, z: "3")
        # These lambda functions simulate user actions
        self.write_action_one = lambda x, y, z, data: "%s_4" % data
        self.write_action_two = lambda x, y, z, data: "%s_5" % data
        self.write_action_three = lambda x, y, z, data: "%s_6" % data

        self.router.append_write_rule("test1", self.write_action_one)
        self.router.append_write_rule("test2", self.write_action_two)
        self.router.append_write_rule("test3.*", self.write_action_three)

    def test_initialize_read(self):
        read_buffer = self.router.initialize_read("test1", "127.0.0.1", 3942)
        self.assertEqual(read_buffer.data, "1")

        read_buffer = self.router.initialize_read("test2", "127.0.0.1", 3942)
        self.assertEqual(read_buffer.data, "2")

        read_buffer = self.router.initialize_read("test3", "127.0.0.1", 3942)
        self.assertEqual(read_buffer.data, "3")

        read_buffer = self.router.initialize_read("test3if", "127.0.0.1", 3942)
        self.assertEqual(read_buffer.data, "3")

    def test_initialize_read_for_no_action(self):
        read_buffer = self.router.initialize_read("test4", "127.0.0.1", 3942)
        self.assertEqual(read_buffer, None)

    def test_initialize_write(self):
        write_action = self.router.initialize_write("test1", "127.0.0.1", 3942)
        self.assertEqual(write_action("a", "b", "c", "d"), "d_4")

        write_action = self.router.initialize_write("test2", "127.0.0.1", 3942)
        self.assertEqual(write_action("a", "b", "c", "d"), "d_5")

        write_action = self.router.initialize_write("test3", "127.0.0.1", 3942)
        self.assertEqual(write_action("a", "b", "c", "d"), "d_6")

    def test_initialize_write_for_no_action(self):
        write_action = self.router.initialize_write("test4", "127.0.0.1", 3942)
        self.assertEqual(write_action, None)

if __name__ == "__main__":
    unittest.main()
