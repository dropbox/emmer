import os
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "../emmer"))
import packets


class TestPackets(unittest.TestCase):
    def test_pack_and_unpack_packet_to_rrq(self):
        packet_data = "\x00\x01filename_example\x00mode_example\x00"
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.ReadRequestPacket)
        self.assertEqual(packet.filename, "filename_example")
        self.assertEqual(packet.mode, "mode_example")
        self.assertEqual(packet.options, {})
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_rrq_with_options(self):
        packet_data = (
            "\x00\x01filename_example\x00mode_example\x00blksize\x003128\x00timeout\x008\x00")
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.ReadRequestPacket)
        self.assertEqual(packet.filename, "filename_example")
        self.assertEqual(packet.mode, "mode_example")
        self.assertEqual(packet.options, {'blksize':"3128", 'timeout': "8"})
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_wrq(self):
        packet_data = "\x00\x02filename_example\x00mode_example\x00"
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.WriteRequestPacket)
        self.assertEqual(packet.filename, "filename_example")
        self.assertEqual(packet.mode, "mode_example")
        self.assertEqual(packet.options, {})
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_wrq_with_options(self):
        packet_data = "\x00\x02filename_example\x00mode_example\x00blksize\x003128\x00timeout\x008\x00"
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.WriteRequestPacket)
        self.assertEqual(packet.filename, "filename_example")
        self.assertEqual(packet.mode, "mode_example")
        self.assertEqual(packet.options, {'blksize':"3128", 'timeout': "8"})
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_data(self):
        data = "X" * 512
        packet_data = "\x00\x03\x15\x12" + data
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.DataPacket)
        self.assertEqual(packet.block_num, 5394)
        self.assertEqual(packet.data, data)
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_ack(self):
        packet_data = "\x00\x04\x15\x12"
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.AcknowledgementPacket)
        self.assertEqual(packet.block_num, 5394)
        self.assertEqual(packet.pack(), packet_data)

    def test_pack_and_unpack_packet_to_error(self):
        packet_data = "\x00\x05\x15\x12error_message_example\x00"
        packet = packets.unpack_packet(packet_data)
        self.assertEqual(packet.__class__, packets.ErrorPacket)
        self.assertEqual(packet.error_code, 5394)
        self.assertEqual(packet.error_message, "error_message_example")
        self.assertEqual(packet.pack(), packet_data)

if __name__ == "__main__":
    unittest.main()
