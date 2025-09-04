import csv
import datetime
import socket
import logging
from typing import Optional, Dict, Any
from bets.protocol.protocol import LotteryProtocol
from bets.models.bet import Bet


""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574


""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])



def bets_from_dict_list(bets_dict_list):
    """
    Convierte una lista de diccionarios en una lista de objetos Bet.
    """
    bet_objects = []
    for bet_dict in bets_dict_list:
        bet_objects.append(Bet(
            bet_dict['agency'],
            bet_dict['first_name'],
            bet_dict['last_name'],
            bet_dict['document'],
            bet_dict['birthdate'],
            bet_dict['number']
        ))
    return bet_objects


def close_client_connection(self, client_sock: socket.socket):
        try:
            if client_sock:
                client_sock.shutdown(socket.SHUT_RDWR)
                client_sock.close()
        except OSError as e:
            logging.error(f"action: close_client_socket | result: fail | error: {e}")
            
def log_batch_reception(self, batch_count: int, client_sock: socket.socket):
        addr = client_sock.getpeername()
        logging.info(f'action: receive_batch | result: success | ip: {addr[0]} | batch: {batch_count}')
        
def process_successful_batch(self, message_data: Dict[str, Any],
                                protocol: LotteryProtocol,
                                session_stats: '_ClientSessionStats',
                                agency_number: Optional[int],
                                bets_lock, batch_count: int):
        try:
            bet_objects = bets_from_dict_list(message_data['bets'])
            
            if agency_number is None and bet_objects:
                agency_number = bet_objects[0].agency
                
            with bets_lock:
                store_bets(bet_objects)
                
            session_stats.total_bets += len(bet_objects)
            
            logging.info(f"action: batch_stored | result: success | "
                        f"batch: {batch_count} | bets: {len(bet_objects)} | "
                        f"total: {session_stats.total_bets}")
                        
            protocol.send_confirmation()
            
        except Exception as e:
            self._handle_batch_failure("batch_storage", batch_count, e, protocol)
            raise