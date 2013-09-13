"""
packets.py

Implements data structures to represent packets in a TFTP conversation.

All Packet objects offer the following functions:
    pack: Take internal values and return a string satisfying the tftp
        specification for that type of packet
    __str__: Return a human readable string describing the contents of that
        packet.

Furthermore, this module offers a function called `unpack_packet`, which takes
packet data that satisfies the tftp specification and returns an instance of
the corresponding type of packet.
"""


import logging
import struct


READ_REQUEST_OPCODE = 1
WRITE_REQUEST_OPCODE = 2
DATA_OPCODE = 3
ACKNOWLEDGEMENT_OPCODE = 4
ERROR_OPCODE = 5


def unpack_packet(packet_data):
    """Takes a tftp packet and returns the corresponding object for that type
    of packet

    Args:
        packet_data: A str that represents a tftp packet.

    Returns:
        A Packet subclass that corresponds to the type of packet sent in the
        tftp conversation. If the packet is illegal in some way, then a
        NoOpPacket is returned.
    """
    try:
        opcode = bytes_to_int(packet_data[0:2])
        if opcode == READ_REQUEST_OPCODE:
            split_data = packet_data[2:].split("\x00")
            filename = split_data[0]
            mode = split_data[1]
            options = options_list_to_dictionary(split_data[2:-1])
            return ReadRequestPacket(filename, mode, options)
        elif opcode == WRITE_REQUEST_OPCODE:
            split_data = packet_data[2:].split("\x00")
            filename = split_data[0]
            mode = split_data[1]
            options = options_list_to_dictionary(split_data[2:-1])
            return WriteRequestPacket(filename, mode, options)
        elif opcode == DATA_OPCODE:
            block_num = bytes_to_int(packet_data[2:4])
            data = packet_data[4:]
            return DataPacket(block_num, data)
        elif opcode == ACKNOWLEDGEMENT_OPCODE:
            block_num = bytes_to_int(packet_data[2:4])
            return AcknowledgementPacket(block_num)
        elif opcode == ERROR_OPCODE:
            error_code = bytes_to_int(packet_data[2:4])
            error_message = packet_data[4:-1]
            return ErrorPacket(error_code, error_message)
        # TODO: Add method for error response, Code 4, Illegal TFTP Operation
    except:
        logging.warn("Invalid packet %s" % packet_data)
    return NoOpPacket()


def int_to_bytes(int_value):
    return struct.pack(">h", int_value)

def bytes_to_int(byte_value):
    return struct.unpack(">h", byte_value)[0]

def options_dictionary_to_string(options_dictionary):
    """Given a dictionary, returns a string in the form:

    "\x00KEY1\x00VALUE1\x00KEY2\x00VALUE2\x00...\x00"

    Sorted in order of key
    """
    ops = []
    for (key, value) in sorted(options_dictionary.iteritems()):
        ops.append(key)
        ops.append(value)
    ops_string = "\x00".join(ops)
    ops_string +=  "\x00" if ops else ""
    return ops_string

def options_list_to_dictionary(options_list):
    """Given a list of options of the form:
    [KEY1, VALUE1, KEY2, VALUE2, ..]

    Returns a dictionary of those keys and values.
    """
    options = dict([(options_list[i*2], options_list[i*2+1])
                    for i in xrange(len(options_list) / 2)])
    return options


class ReadRequestPacket(object):
    """
    Structure of a RRQ packet:
        2 bytes     string    1 byte     string   1 byte
        ------------------------------------------------
       | Opcode |  Filename  |   0  |    Mode    |   0  |
        ------------------------------------------------

    Or an optional version
        +-------+---~~---+---+---~~---+---+---~~---+---+---~~---+---+
        |  opc  |filename| 0 |  mode  | 0 | blksize| 0 | #octets| 0 |
        +-------+---~~---+---+---~~---+---+---~~---+---+---~~---+---+

    """
    def __init__(self, filename, mode, options={}):
        self.opcode = READ_REQUEST_OPCODE
        self.filename = filename
        self.mode = mode
        self.options = options

    def pack(self):
        """Take internal values and return a string satisfying the tftp
        specification with this packet's values.
        """
        opcode_encoded = int_to_bytes(self.opcode)
        ops_string = options_dictionary_to_string(self.options)

        return (opcode_encoded + self.filename + "\x00" + self.mode
            + "\x00" + ops_string)

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return ("<ReadRequestPacket:: filename: %s, mode: %s>"
                % (self.filename, self.mode))


class WriteRequestPacket(object):
    """
    Structure of a WRQ packet:
        2 bytes     string    1 byte     string   1 byte
        ------------------------------------------------
       | Opcode |  Filename  |   0  |    Mode    |   0  |
        ------------------------------------------------

    """
    def __init__(self, filename, mode, options={}):
        self.opcode = WRITE_REQUEST_OPCODE
        self.filename = filename
        self.mode = mode
        self.options = options

    def pack(self):
        """Take internal values and return a string satisfying the tftp
        specification with this packet's values.
        """
        opcode_encoded = int_to_bytes(self.opcode)
        ops_string = options_dictionary_to_string(self.options)
        return (opcode_encoded + self.filename + "\x00" + self.mode
                + "\x00" + ops_string)

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return ("<WriteRequestPacket:: filename: %s, mode: %s>"
                % (self.filename, self.mode))


class DataPacket(object):
    """
    Structure of a DATA packet:
        2 bytes     2 bytes      n bytes
        ----------------------------------
       | Opcode |   Block #  |   Data     |
        ----------------------------------
    """
    def __init__(self, block_num, data):
        self.opcode = DATA_OPCODE
        self.block_num = block_num
        self.data = data

    def pack(self):
        """Take internal values and return a string satisfying the tftp
        specification with this packet's values.
        """
        opcode_encoded = int_to_bytes(self.opcode)
        block_num_encoded = int_to_bytes(self.block_num)
        return opcode_encoded + block_num_encoded + self.data

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return ("<DataPacket:: block_num: %s, data: %s>"
                % (self.block_num, self.data))


class AcknowledgementPacket(object):
    """
    Structure of an ACK packet:
         2 bytes     2 bytes
         ---------------------
        | Opcode |   Block #  |
         ---------------------
    """
    def __init__(self, block_num):
        self.opcode = ACKNOWLEDGEMENT_OPCODE
        self.block_num = block_num

    def pack(self):
        """Take internal values and return a string satisfying the tftp
        specification with this packet's values.
        """
        opcode_encoded = int_to_bytes(self.opcode)
        block_num_encoded = int_to_bytes(self.block_num)
        return opcode_encoded + block_num_encoded

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return ("<AcknowledgementPacket:: block_num: %s>" % (self.block_num))


class ErrorPacket(object):
    """
    Structure of an ERROR packet:
        2 bytes     2 bytes      string    1 byte
        -----------------------------------------
        | Opcode |  ErrorCode |   ErrMsg   |   0  |
        -----------------------------------------
    """
    def __init__(self, error_code, error_message):
        self.opcode = ERROR_OPCODE
        self.error_code = error_code
        self.error_message = error_message

    def pack(self):
        """Take internal values and return a string satisfying the tftp
        specification with this packet's values.
        """
        opcode_encoded = int_to_bytes(self.opcode)
        error_code_encoded = int_to_bytes(self.error_code)
        return (opcode_encoded + error_code_encoded
                + self.error_message + "\x00")

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return ("<ErrorPacket:: error_code: %s, error_message: %s>"
                % (self.error_code, self.error_message))


class NoOpPacket(object):
    """This packet type is used when no action should be taken"""

    def __str__(self):
        """ Return a human readable string describing the contents of the
        packet.
        """
        return "NoOpPacket"
