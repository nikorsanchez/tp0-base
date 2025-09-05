import socket
import logging
import signal
from multiprocessing import Process, Manager, Event
from bets.protocol.protocol import LotteryProtocol
from bets.handlers.bet_handler import BetHandler
from common.utils import store_bets, bets_from_dict_list, load_bets, has_won, close_client_connection, log_batch_reception
from common.errors import handle_batch_failure, handle_connection_error

class Server:
    def __init__(self, port, listen_backlog, expected_clients):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._expected_clients = expected_clients
        self._shutdown_event = Event()
        self.manager = None
        self._finished_clients = None
        self._condition = None
        self._bets_lock = None
        
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        
    def _init_manager(self):
        if self.manager is None:
            self.manager = Manager()
            self._finished_clients = self.manager.Value('i', 0)
            self._condition = self.manager.Condition()
            self._bets_lock = self.manager.Lock()

    def handle_signal(self, signum, frame):
        logging.info(f"action: received_signal | signal: {signum} | result: in_progress")
        self._shutdown_event.set()
        self._graceful_shutdown()
        
    def _close_server_socket(self):
        try:
            logging.info("action: closing_server_socket | result: in_progress")
            if self._server_socket:
                self._server_socket.shutdown(socket.SHUT_RDWR)
                self._server_socket.close()
        except OSError as e:
            logging.error(f"action: closing_server_socket | result: fail | error: {e}")

    def run(self):
        self._init_manager()
        
        logging.info('server started, waiting for connections...')
        processes = []
        try:
            while not self._shutdown_event.is_set() and len(processes) < self._expected_clients:
                try:
                    client_sock = self.__accept_new_connection()
                    if client_sock is not None:
                        p = Process(
                            target=self.__handle_client_connection,
                            args=(
                                client_sock,
                                self._finished_clients,
                                self._condition,
                                self._expected_clients,
                                self._bets_lock,
                                self._shutdown_event
                            )
                        )
                        p.start()
                        processes.append(p)
                        logging.info(f"action: client_connected | total: {len(processes)}/{self._expected_clients}")
                except socket.timeout:
                    continue
            
            for p in processes:
                p.join()
            
            logging.info("action: server_completed | result: success")
                    
        except Exception as e:
            logging.error(f"action: server_loop | result: fail | error: {e}")
        finally:
            if self._shutdown_event.is_set():
                for p in processes:
                    if p.is_alive():
                        p.terminate()
                    p.join()

    def __handle_client_connection(self, client_sock, finished_clients, condition, expected_clients, bets_lock, shutdown_event):
        protocol = LotteryProtocol(client_sock)
        total_bets_received = 0
        batch_count = 0
        agency_number = None

        try:
            while not shutdown_event.is_set():
                try:
                    message_data = protocol.receive_message()
                    if message_data is None:
                        logging.info("action: client_disconnected | result: success | reason: no_data")
                        break
                    if message_data.get('type') == 'finished':
                        logging.info(f"action: client_finished | agency: {agency_number}")
                        
                        with condition:
                            finished_clients.value += 1                            
                            if finished_clients.value == expected_clients:
                                condition.notify_all()
                            else:
                                while (finished_clients.value < expected_clients and 
                                    not shutdown_event.is_set()):
                                    condition.wait()
                        
                        if not shutdown_event.is_set() and agency_number is not None:
                            logging.info("action: lottery | result: in_progress")
                            try:
                                bets = [bet for bet in load_bets() if bet.agency == agency_number]
                                winners = [bet.document for bet in bets if has_won(bet)]
                                protocol.send_winners_list(winners, agency_number)
                                logging.info(f"action: winners_sent | agency: {agency_number} | winners: {len(winners)}")
                            except Exception as e:
                                logging.error(f"action: send_winners | result: fail | error: {e}")
                        
                        break
                    if message_data.get('type') == 'batch':
                        log_batch_reception(self, batch_count + 1, client_sock)
                        batch_count += 1
                        response = BetHandler.process_batch_bet(message_data)
                        if response.get('status') == 'success':
                            try:
                                bet_objects = bets_from_dict_list(message_data['bets'])
                                if agency_number is None and bet_objects:
                                    agency_number = bet_objects[0].agency
                                with bets_lock:
                                    store_bets(bet_objects)
                                total_bets_received += len(bet_objects)
                                protocol.send_confirmation()
                            except Exception as e:
                                handle_batch_failure("batch_storage", batch_count, e, protocol)
                                break
                        else:
                            handle_batch_failure("process_batch", batch_count, response.get('message'), protocol)
                            break
                except (socket.timeout, ConnectionResetError) as e:
                    handle_connection_error(e)
                    break
                except Exception as e:
                    handle_batch_failure("process_batch", batch_count, e, None)
                    break
            logging.info(f"action: client_session_end | result: success | batches: {batch_count} | total_bets: {total_bets_received}")
        except Exception as e:
            logging.error(f"action: handle_client | result: fail | error: {e}")
        finally:
            logging.info("action: lottery | result: success")
            close_client_connection(client_sock)

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        try:
            client_sock, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return client_sock
        except socket.timeout:
            return None
        except OSError as e:
            if not self._shutdown_event.is_set():
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return None

    def _graceful_shutdown(self):
        logging.info("action: server_shutdown | result: in_progress")
        self._close_server_socket()
        logging.info("action: server_shutdown | result: success")
