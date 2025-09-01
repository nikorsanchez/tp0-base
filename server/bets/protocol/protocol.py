import struct
import logging
from bets.protocol.protocol_consts import HEADER_TYPE_BET, HEADER_TYPE_CONFIRM, HEADER_SIZE, CONFIRMATION_LENGTH, HEADER_TYPE_FAILURE

class LotteryProtocol:
    def __init__(self, sock):
        self.sock = sock

    def send_confirmation(self):
        """
        Send only a confirmation header
        """
        try:
            header = struct.pack('!BH', HEADER_TYPE_CONFIRM, CONFIRMATION_LENGTH)
            self.sock.sendall(header)
            logging.info("action: send_confirmation | result: success")
            return True
        except (OSError, struct.error) as e:
            logging.error(f"action: send_confirmation | result: fail | error: {e}")
            return False
        
    def send_confirmation_failed(self):
        try:
            header = struct.pack('!BH', HEADER_TYPE_FAILURE, CONFIRMATION_LENGTH)
            self.sock.sendall(header)
            logging.info("action: send_confirmation_failed | result: success")
            return True
        except (OSError, struct.error) as e:
            logging.error(f"action: send_confirmation_failed | result: fail | error: {e}")
            return False

    def receive_message(self):
        """
        Receive a complete message avoiding short reads
        """
        try:
            header = self._recv_all(HEADER_SIZE)
            if not header:
                return None
            
            msg_type, message_length = struct.unpack('!BH', header)
            
            if msg_type != HEADER_TYPE_BET:
                logging.error(f"action: receive_message | result: fail | error: unexpected_type | type: {msg_type}")
                return None
            
            message_bytes = self._recv_all(message_length)
            if not message_bytes:
                return None
            
            message_str = message_bytes.decode('utf-8').strip()
            parts = message_str.split('|')
            
            if len(parts) != 6:
                logging.error(f"action: receive_message | result: fail | error: invalid_format | expected 6 fields, got {len(parts)}")
                return None
            
            message = {
                'agency': parts[0],
                'first_name': parts[1],
                'last_name': parts[2],
                'document': parts[3],
                'birthdate': parts[4],
                'number': parts[5]
            }
            
            return message
            
        except (OSError, struct.error, UnicodeDecodeError, ValueError) as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            return None

    def _recv_all(self, n):
        """
        Receive exactly n bytes avoiding short reads
        """
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def close(self):
        """
        Close the underlying socket
        """
        try:
            self.sock.close()
        except OSError:
            pass