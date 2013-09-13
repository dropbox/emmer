## Emmer Implementation

## Submodule Summaries

* config: Includes server configuration directives that can be
  overridden by a client application.

* conversation_table: A data structure that stores and manages lookups
  of tftp conversations.

* emmer: A wrapper for the entire framework that acts as the client
  application interface.

* packets: A collection of data structures that represent that different
  types of packets in the TFTP protocol.

* performer: A class that runs timeout, message retry, and garbage collection
  operations over the conversation table.

* reactor: A class that runs the server's listening event loop. When
  packets are received, the reactor forwards them to the tftp
  conversation, with an additional side effect of abstracting away the
  network interface.

* response_router: A module that maintains all client application routes.

* tftp_conversation: A class that defines the state machine for a single
  client to server tftp conversation.

* utility: Contains various utility functions used in multiple other
  modules.
