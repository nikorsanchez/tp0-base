import struct
import logging
from bets.protocol.protocol_consts import HEADER_TYPE_BET_BATCH, HEADER_TYPE_CONFIRM, HEADER_SIZE, CONFIRMATION_LENGTH, HEADER_TYPE_FAILURE

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
            
            if msg_type != HEADER_TYPE_BET_BATCH:
                logging.error(f"action: receive_message | result: fail | error: unexpected_type | type: {msg_type}")
                return None
            
            message_bytes = self._recv_all(message_length)
            if not message_bytes:
                return None
            
            message_str = message_bytes.decode('utf-8').strip()
            
            return self._parse_batch_message(message_str)
            
        except (OSError, struct.error, UnicodeDecodeError, ValueError) as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            return None
        
    def _parse_batch_message(self, message_str):
        """
        Parse a batch of bets message
        """
        bets = []
        error_count = 0
        
        bet_strings = message_str.split(';')
        
        logging.info(f"action: parse_batch | result: in_progress | total_bets: {len(bet_strings)}")
        
        for bet_str in bet_strings:
            if not bet_str.strip():
                continue
                
            parts = bet_str.split('|')
            
            if len(parts) != 6:
                logging.warning(f"action: parse_bet | result: skip | error: invalid_format | fields: {len(parts)} | bet: {bet_str}")
                error_count += 1
                continue
            
            bets.append({
                'agency': parts[0],
                'first_name': parts[1],
                'last_name': parts[2],
                'document': parts[3],
                'birthdate': parts[4],
                'number': parts[5]
            })
        
        if not bets:
            logging.error("action: parse_batch | result: fail | error: no_valid_bets")
            return None
        
        return {
            'type': 'batch',
            'bets': bets,
            'error_count': error_count,
            'total_received': len(bet_strings)
        }

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