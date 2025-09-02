import struct
import logging
from bets.protocol.protocol_consts import (
    HEADER_TYPE_BET_BATCH,
    HEADER_TYPE_CONFIRM,
    HEADER_TYPE_FAILURE,
    HEADER_TYPE_FINISH_NOTIFY,
    HEADER_TYPE_WINNERS_QUERY,
    HEADER_TYPE_WINNERS_LIST,
    HEADER_SIZE,
    CONFIRMATION_LENGTH
)

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

    def send_winners_list(self, dni_list, agency):
        """
        Send a list of winners' DNI as a comma-separated string.
        """
        winners_str = ",".join(dni_list)
        winners_bytes = winners_str.encode('utf-8')
        header = struct.pack('!BH', HEADER_TYPE_WINNERS_LIST, len(winners_bytes))
        try:
            self.sock.sendall(header)
            if winners_bytes:
                self.sock.sendall(winners_bytes)
            logging.info(f"action: send_winners_list | result: success | agency: {agency} | winners: {winners_str}")
            return True
        except (OSError, struct.error) as e:
            logging.error(f"action: send_winners_list | result: fail | error: {e}")
            return False

    def receive_message(self):
        """
        Receives a message and interprets it according to its type:
        - Batch of bets
        - End of sending notification
        - Winners query
        """
        try:
            header = self._recv_all(HEADER_SIZE)
            if not header:
                return None

            msg_type, message_length = struct.unpack('!BH', header)

            if msg_type == HEADER_TYPE_BET_BATCH:
                message_bytes = self._recv_all(message_length)
                if not message_bytes:
                    return None
                message_str = message_bytes.decode('utf-8').strip()
                return self._parse_batch_message(message_str)

            elif msg_type == HEADER_TYPE_FINISH_NOTIFY:
                logging.info("action: receive_finish_notify | result: success | msg: client finished sending bets")
                return {'type': 'finished'}

            elif msg_type == HEADER_TYPE_WINNERS_QUERY:
                agency_bytes = self._recv_all(message_length)
                if not agency_bytes:
                    return None
                agency = agency_bytes.decode('utf-8').strip()
                logging.info(f"action: receive_winners_query | result: success | agency: {agency}")
                return {'type': 'winners_query', 'agency': agency}

            else:
                logging.error(f"action: receive_message | result: fail | error: unexpected_type | type: {msg_type}")
                return None

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