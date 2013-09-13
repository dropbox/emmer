import re


class ResponseRouter(object):
    """Handles the passing of control from a conversation to a client app's
    routes.

    For read requests and write requests, ResponseRouter maintains two lists of
    rules, where each rule is a tuple is of the form(filename pattern, action).
    When a request comes in, the filename given is checked against the list of
    filename regex patterns, and the first rule that matches invokes the
    corresponding action.

    actions are application level functions that take the following argument:
        client_host: The ip or hostname of the client.
        client_port: The port of the client
        filename: The filename included in the client request.

    Additionally, a write request takes an additional argument:
        data: The data sent from the client in the tftp conversation.

    In the case of read requests, actions should return string data that will
    be served directly back to clients.
    """
    def __init__(self):
        self.read_rules = []
        self.write_rules = []

    def append_read_rule(self, filename_pattern, action):
        """Adds a rule associating a filename pattern with an action for read
        requests. The action given will execute when a read request is received
        but before any responses are given.

        Args:
            filename_pattern: A string pattern to match future read request
                filenames against.
            action: A function to invoke when a later read request arrives
                matching the given filename_pattern.
        """
        self.read_rules.append((filename_pattern, action))

    def append_write_rule(self, filename_pattern, action):
        """Adds a rule associating a filename pattern with an action for write
        requests. The action given will execute when a write request is
        completed and all data received.

        Args:
            filename_pattern: A string pattern to match future read request
                filenames against.
            action: A function to invoke when a later read request arrives
                matching the given filename_pattern.
        """
        self.write_rules.append((filename_pattern, action))

    def initialize_read(self, filename, client_host, client_port):
        """For a read request, finds the appropriate action and invokes it.

        Args:
            filename: The filename included in the client's request.
            client_host: The host of the client connecting.
            client_port: The port of the client connecting.

        Returns:
            A ReadBuffer containing the file contents to return. If there is no
            corresponding action, returns None.
        """
        action = self.find_action(self.read_rules, filename)
        if action:
            return ReadBuffer(action(client_host, client_port, filename))
        else:
            return None

    def initialize_write(self, filename, client_host, client_port):
        """For a write request, finds the appropriate action and returns it.
        This is different than a read request in that the action is invoked at
        the end of the file transfer.

        Args:
            filename: The filename included in the client's request.
            client_host: The host of the client connecting.
            client_port: The port of the client connecting.

        Returns:
            An action that is to be run at the end of a write request file
            transfer. If there is no corresponding action, returns None.
        """
        return self.find_action(self.write_rules, filename)

    def find_action(self, rules, filename):
        """Given a list of rules and a filename to match against them, returns
        an action stored in one of those rules. The action returned corresponds
        to the first rule that matches the filename given.

        Args:
            rules: A list of tuples, where each tuple is (filename pattern,
                action).
            filename: A filename to match against the filename regex patterns.

        Returns:
            An action corresponding to the first rule that matches the filename
            given. If no rules match, returns None.
        """
        for (filename_pattern, action) in rules:
            if re.match(filename_pattern, filename):
                return action
        return None


class ReadBuffer(object):
    """A ReadBuffer is used to temporarily store read request data while the
    transfer has not completely succeeded. It offers an interface for
    retrieving chunks of data in 512 byte chunks based on block number.
    """
    def __init__(self, data):
        self.data = data

    def get_block_count(self):
        """Returns the amount of blocks that this ReadBuffer can produce
        This amount is also the largest value that can be passed into
        get_block.
        """
        return (len(self.data) / 512) + 1

    def get_block(self, block_num):
        """Returns the data corresponding to the given block number

        Args:
            block_num: The block number of data to request. By the TFTP
            protocol, blocks are consecutive 512 byte sized chunks of data with
            the exception of the final block which may be less than 512 chunks.

        Return:
            A 512 byte or less chunk of data corresponding to the given block
            number.
        """
        return self.data[(block_num - 1) * 512:block_num * 512]


class WriteBuffer(object):
    """A WriteBuffer is used to temporarily store write request data while the
    transfer has not completely succeeded.

    Retrieve the data from the `data` property.
    """
    def __init__(self):
        self.data = ""

    def receive_data(self, data):
        """Write some more data to the WriteBuffer """
        self.data += data
