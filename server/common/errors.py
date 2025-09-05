from bets.protocol.protocol import LotteryProtocol
import logging
import socket
from typing import Any

def handle_batch_failure(context: str, batch_count: int, error: Any, protocol=None):
    logging.error(f"action: {context} | result: fail | batch: {batch_count} | error: {error}")
    if protocol:
        try:
            protocol.send_confirmation_failed()
        except:
            logging.error("action: send_confirmation_failed | result: fail")

def handle_connection_error(self, error: Exception):
    reason = "idle_timeout" if isinstance(error, socket.timeout) else "connection_reset"
    logging.info(f"action: client_disconnected | result: success | reason: {reason}")