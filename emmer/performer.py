import calendar
import logging
import time
import threading

import packets
import tftp_conversation
from utility import lock


class Performer(object):
    """A Performer class runs background tasks on the TFTP server such as:
    * Timeout detection for packet resending.
    * Garbage collection for conversations that have run out of allowed retry
      attempts or conversations that have already completed.
    """
    def __init__(self, sock, conversation_table,
                 resend_timeout, retries_before_giveup):
        """
        Args:
            sock: The UDP socket that the server is listening on.
            conversation_table: A conversation table to poll for
                conversations.
            resend_timeout: The amount of seconds to wait before attempting a
                packet resend.
            retries_before_giveup: The amount of packet retries to make before
                permanently discarding a conversation.
        """
        self.conversation_table = conversation_table
        self.lock = threading.Lock()
        self.sock = sock
        self.resend_timeout = resend_timeout
        self.retries_before_giveup = retries_before_giveup

    def run(self, sleep_interval):
        while True:
            try:
                logging.debug(self.conversation_table)
                self.conversation_table.lock.acquire()
                self.find_and_handle_stale_conversations()
                self.sweep_completed_conversations()
                self.conversation_table.lock.release()
                time.sleep(sleep_interval)
            except Exception as ex:
                logging.debug("\033[31m%s\033[0m" % ex)

    @lock
    def find_and_handle_stale_conversations(self):
        """Finds all conversations that are stale (not interacted with within
        the resend timeout window) and for each one either retries the previous
        message or destroys it.
        """
        stale_conversations = (
            self._get_stale_conversations(self.resend_timeout))
        for conversation in stale_conversations:
            self._handle_stale_conversation(conversation)

    def _handle_stale_conversation(self, conversation):
        """Given a conversation that is known to be stale
        (time_of_last_interaction beyond resend_timeout), either:
        * Retry sending of the most recent packet if retries_made is less
          than retries_before_giveup.
        * Destroy that conversation and send ErrorPacket about Timeout otherwise.

        Args:
            conversation: The conversation described above.
        """
        client_host = conversation.client_host
        client_port = conversation.client_port
        if conversation.retries_made < self.retries_before_giveup:
            packet = conversation.mark_retry()
            if not isinstance(packet, packets.NoOpPacket):
                logging.debug("%s:%s Resending" % (client_host, client_port))
                self.sock.sendto(packet.pack(), (client_host, client_port))
            return
        packet = packets.ErrorPacket(0, "Conversation Timed Out")
        self.sock.sendto(packet.pack(), (client_host, client_port))
        self.conversation_table.delete_conversation(client_host, client_port)

    def _get_stale_conversations(self, time_elapsed, time_reference=None):
        """Returns all conversations that have not been interacted with
        for a time greater than or equal to the given time elapsed.

        Args:
            time_elapsed: The amount of time in seconds which sets the
                threshold for which conversations should be retrieved.
            time_reference: The time (since epoch) that should be used as the
                reference point. If not passed anything, seconds since epoch is
                used.

        Returns:
            A list of conversations.
        """
        if not time_reference:
            time_reference = calendar.timegm(time.gmtime())
        stale_conversations = []
        for client_addr in self.conversation_table.conversation_table:
            conversation = (
                self.conversation_table.get_conversation(*client_addr))
            time_of_last_interaction = conversation.time_of_last_interaction
            if time_reference - time_elapsed >= time_of_last_interaction:
                stale_conversations.append(conversation)
        return stale_conversations

    @lock
    def sweep_completed_conversations(self):
        """Deletes all completed conversations from the conversation table."""
        completed_conversation_client_addrs = []
        for client_addr in self.conversation_table.conversation_table:
            conversation = (
                self.conversation_table.get_conversation(*client_addr))
            if conversation.state == tftp_conversation.COMPLETED:
                completed_conversation_client_addrs.append(client_addr)
        for client_addr in completed_conversation_client_addrs:
            self.conversation_table.delete_conversation(*client_addr)
