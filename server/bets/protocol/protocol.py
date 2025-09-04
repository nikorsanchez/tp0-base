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

    def send_winners_list(self, dni_list, agency):
        """
        Send a list of winners' DNI, expected to be received as 8 digit long each.
        """
        dni_bytes = b"".join(dni.encode('utf-8') for dni in dni_list)
        message_length = len(dni_bytes)
        header = self._serialize_header(msg_type=HEADER_TYPE_WINNERS_LIST, length=message_length)

        logging.info(f"action: send_winners_list | result: in_progress | agency: {agency} | winners count: {len(dni_list)}")

        try:
            self._send_all(header)
            self._send_all(dni_bytes)
            logging.info(f"action: send_winners_list | result: success | agency: {agency} | winners sent: {dni_list}")
            return True
        except (OSError, ValueError) as e:
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

            msg_type, message_length = self._deserialize_header(header)

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
    
    def _send_all(self, data: bytes) -> None:
        """
        Send exactly all bytes in data
        """
        total_sent = 0
        while total_sent < len(data):
            sent = self.sock.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent
    
    def _serialize_header(self, msg_type, length):
        header = bytearray()
        header.append(msg_type)
        header.extend(length.to_bytes(2, 'big', signed=False))
        return bytes(header)

    def _deserialize_header(self, header_bytes):
        if len(header_bytes) != HEADER_SIZE:
            raise ValueError("Invalid header size")
        
        msg_type = header_bytes[0]
        length = int.from_bytes(header_bytes[1:3], 'big', signed=False)
        
        return msg_type, length

    def close(self):
        """
        Close the underlying socket
        """
        try:
            self.sock.close()
        except OSError:
            pass
            
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