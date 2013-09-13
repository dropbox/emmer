#######################################
# Service Configuration Configuration #
#######################################

# Socket listening configuration
# Set to 0.0.0.0 and 69 for production
HOST = "127.0.0.1"
PORT = 3942

# How many seconds to wait before resending a non acked packet.
RESEND_TIMEOUT = 5

# How many times to retry sending a non acked packet before giving up.
RETRIES_BEFORE_GIVEUP = 6

#################################
# Internal Tuning Configuration #
#################################

# How often the daemon thread should sweep through
PERFORMER_THREAD_INTERVAL = 1
