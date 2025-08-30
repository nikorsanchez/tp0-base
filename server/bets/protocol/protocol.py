import struct
import json
import logging

# bytes
HEADER_TYPE_BET = 1
HEADER_TYPE_CONFIRM = 2
HEADER_SIZE = 1
LENGTH_SIZE = 3
FULL_HEADER_SIZE = HEADER_SIZE + LENGTH_SIZE

class LotteryProtocol:
    def __init__(self, sock):
        self.sock = sock

    def send_message(self, message):
        """
        Send a message with a header indicating the size to avoid short writes
        """
        try:
            message_bytes = json.dumps(message).encode('utf-8')
            message_length = len(message_bytes)
            if message_length > 0xFFFFFF:
                raise ValueError("Message too large")
            header = struct.pack('!B', HEADER_TYPE_BET)
            length = message_length.to_bytes(3, 'big')
            self.sock.sendall(header + length + message_bytes)
            return True
        except (OSError, struct.error, json.JSONEncodeError, ValueError) as e:
            logging.error(f"action: send_message | result: fail | error: {e}")
            return False
        
    def send_confirmation(self):
        """
        Send only a confirmation header (no body)
        """
        try:
            header = struct.pack('!B', HEADER_TYPE_CONFIRM)
            length = (0).to_bytes(3, 'big')
            self.sock.sendall(header + length)
            logging.info("action: send_confirmation | result: success")
            return True
        except (OSError, struct.error) as e:
            logging.error(f"action: send_confirmation | result: fail | error: {e}")
            return False

    def receive_message(self):
        """
        Receive a complete message avoiding short reads
        """
        try:
            header = self._recv_all(FULL_HEADER_SIZE)
            if not header:
                return None
            msg_type = header[0]
            message_length = int.from_bytes(header[1:4], 'big')
            if msg_type != HEADER_TYPE_BET:
                logging.error(f"action: receive_message | result: fail | error: unexpected_type | type: {msg_type}")
                return None
            message_bytes = self._recv_all(message_length)
            if not message_bytes:
                return None
            message = json.loads(message_bytes.decode('utf-8'))
            return message
        except (OSError, struct.error, json.JSONDecodeError) as e:
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