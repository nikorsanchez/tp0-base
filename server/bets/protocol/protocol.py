import logging
import socket
from bets.protocol.protocol_consts import HEADER_TYPE_BET, HEADER_TYPE_CONFIRM, HEADER_SIZE, CONFIRMATION_LENGTH, HEADER_TYPE_FAILURE

class LotteryProtocol:
    def __init__(self, sock):
        self.sock = sock

    def _serialize_header(self, msg_type, length):
        header = bytearray()
        header.append(msg_type)  # Message type
        header.extend(length.to_bytes(2, 'big', signed=False))  # Length in big endian
        return bytes(header)

    def _deserialize_header(self, header_bytes):
        if len(header_bytes) != HEADER_SIZE:
            raise ValueError("Invalid header size")
        
        msg_type = header_bytes[0]
        length = int.from_bytes(header_bytes[1:3], 'big', signed=False)
        
        return msg_type, length

    def send_confirmation(self):
        """
        Send only a confirmation header
        """
        try:
            header = self._serialize_header(HEADER_TYPE_CONFIRM, CONFIRMATION_LENGTH)
            self.sock.sendall(header)
            logging.info("action: send_confirmation | result: success")
            return True
        except (OSError, ValueError) as e:
            logging.error(f"action: send_confirmation | result: fail | error: {e}")
            return False
        
    def send_confirmation_failed(self):
        try:
            header = self._serialize_header(HEADER_TYPE_FAILURE, CONFIRMATION_LENGTH)
            self.sock.sendall(header)
            logging.info("action: send_confirmation_failed | result: success")
            return True
        except (OSError, ValueError) as e:
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
            
            msg_type, message_length = self._deserialize_header(header)
            
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
            
        except (OSError, ValueError, UnicodeDecodeError) as e:
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