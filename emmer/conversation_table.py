import threading

from utility import lock


def check_for_conversation_existence(alternate_return_value):
    """A decorator that checks for a conversations existence based on the inner
    functions given client_host and client_port. If it does exist, then run the
    original function, otherwise return the alternate return value.

    Three arguments are assumed of the wrapped function:
        self: The containing ConversationTable
        client_host: A hostname or ip address of the client.
        client_port: The port from which the client is connecting.

    Args:
        alternate_return_value: What to return if the TFTPConversation doesn't
        exist.
    """
    def decorator_outer(function):
        def decorator_inner(self, client_host, client_port, *args):
            if (client_host, client_port) in self.conversation_table:
                return function(self, client_host, client_port, *args)
            else:
                return alternate_return_value

        return decorator_inner

    return decorator_outer


class ConversationTable(object):
    """Manages a mapping of (client host, client port) to TFTPConversation.
    Guarantees serializability even if multiple threads are running operations
    against the same ConversationTable.

    (client host, client port) => conversation
    """
    def __init__(self):
        self.conversation_table = {}
        self.lock = threading.RLock()

    @lock
    def add_conversation(self, client_host, client_port, conversation):
        """Adds a conversation to the conversation table keyed on the client's
        identifying information.

        Args:
            client_host: A hostname or ip address of the client.
            client_port: The port from which the client is connecting.
            conversation: An already created TFTPConversation object.
        """
        self.conversation_table[(client_host, client_port)] = conversation

    @lock
    @check_for_conversation_existence(None)
    def get_conversation(self, client_host, client_port):
        """Given a client hostname and port, looks up the corresponding
        TFTPConversation

        Args:
            client_host: A hostname or ip address of the client.
            client_port: The port from which the client is connecting.

        Returns:
            A preexisting TFTPConversation corresponding to the given client.
            None if there does not exist a TFTPConversation for the given
            client.
        """
        return self.conversation_table[(client_host, client_port)]

    @lock
    @check_for_conversation_existence(False)
    def delete_conversation(self, client_host, client_port):
        """Given a client hostname and port, deletes the corresponding
        TFTPConversation

        Args:
            client_host: A hostname or ip address of the client.
            client_port: The port from which the client is connecting.

        Returns:
            True on success. False if there didn't exist a TFTPConversation.
        """
        del self.conversation_table[(client_host, client_port)]
        return True

    @property
    def conversations(self):
        """Returns a list of all conversations currently stored"""
        return self.conversation_table.values()

    def __len__(self):
        """Returns the number of conversations in the ConversationTable"""
        return len(self.conversation_table)

    def __str__(self):
        """Returns a human readable form of the ConversationTable"""
        return str(self.conversation_table)
