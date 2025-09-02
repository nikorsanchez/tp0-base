import socket
import logging
import signal
from bets.protocol.protocol import LotteryProtocol
from bets.handlers.bet_handler import BetHandler
from common.utils import store_bets, bets_from_dict_list, load_bets, has_won


class Server:
    def __init__(self, port, listen_backlog, expected_clients):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._expected_clients = expected_clients
        self._shutdown_requested = False
        self._setup_signal_handler()
        self._finished_clients = 0
        self._client_sockets = {}

    def _setup_signal_handler(self):
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        # Handle termination signal
        logging.info(f"action: received_signal | result: in_progress")
        self._shutdown_requested = True
        self._graceful_shutdown()

    def _close_server_socket(self):
        try:
            logging.info("action: closing_server_socket | result: in_progress")
            if self._server_socket:
                logging.info(f"action: closing_server_socket | result: in_progress | fd: {self._server_socket.fileno()}")
                self._server_socket.shutdown(socket.SHUT_RDWR)
                self._server_socket.close()
                logging.info(f"action: closing_server_socket | result: success | fd: {self._server_socket.fileno()}")
        except OSError as e:
            logging.error(f"action: closing_server_socket | result: fail | error: {e}")
        
    def run(self):
        """
        Server that accept a new connections and establishes a
        communication with a Lottery client.
        """

        logging.info('server started, waiting for connections...')
        try:
            while not self._shutdown_requested:
                client_sock = self.__accept_new_connection()
                if client_sock is not None:
                    self.__handle_client_connection(client_sock)
        except Exception as e:
            logging.error(f"action: server_loop | result: fail | error: {e}")

    def __handle_client_connection(self, client_sock):
        """
        Handle multiple batches from a client connection
        """
        protocol = LotteryProtocol(client_sock)
        total_bets_received = 0
        batch_count = 0
        agency_number = None

        def handle_batch_failure(context, batch_count, error):
            logging.error(f"action: {context} | result: fail | batch: {batch_count} | error: {error}")
            protocol.send_confirmation_failed()

        try:
            while not self._shutdown_requested:
                try:
                    client_sock.settimeout(10.0)  # 10 second timeout

                    message_data = protocol.receive_message()
                    if message_data.get('type') == 'finished':
                        logging.info("action: client_finished | result: success")
                        if agency_number is not None:
                            self._client_sockets[agency_number] = client_sock
                        self._finished_clients += 1
                        if self._finished_clients == self._expected_clients:
                            self._run_lottery_and_notify_winners()
                        break
                    if message_data is None:
                        logging.info("action: client_disconnected | result: success | reason: no_data")
                        break

                    if message_data.get('type') == 'batch':

                        addr = client_sock.getpeername()
                        batch_count += 1
                        logging.info(f'action: receive_batch | result: success | ip: {addr[0]} | batch: {batch_count}')

                        response = BetHandler.process_batch_bet(message_data)

                        if response.get('status') == 'success':
                            try:
                                bet_objects = bets_from_dict_list(message_data['bets'])
                                if agency_number is None and bet_objects:
                                    agency_number = bet_objects[0].agency
                                    self._client_sockets[agency_number] = client_sock
                                store_bets(bet_objects)
                                total_bets_received += len(bet_objects)
                                logging.info(f"action: batch_stored | result: success | batch: {batch_count} | bets: {len(bet_objects)} | total: {total_bets_received}")
                                protocol.send_confirmation()
                            except Exception as e:
                                handle_batch_failure("batch_storage", batch_count, e)
                                break
                        else:
                            handle_batch_failure("process_batch", batch_count, response.get('message'))
                            break

                except (socket.timeout, ConnectionResetError) as e:
                    reason = "idle_timeout" if isinstance(e, socket.timeout) else "connection_reset"
                    logging.info(f"action: client_disconnected | result: success | reason: {reason}")
                    break
                except Exception as e:
                    handle_batch_failure("process_batch", batch_count, e)
                    break

            logging.info(f"action: client_session_end | result: success | batches: {batch_count} | total_bets: {total_bets_received}")

        except Exception as e:
            logging.error(f"action: handle_client | result: fail | error: {e}")
        finally:
            if not (agency_number and self._finished_clients <= 5):
                protocol.close()

    def _run_lottery_and_notify_winners(self):
        logging.info("action: lottery | result: in_progress")
        bets_by_agency = {}
        for bet in load_bets():
            bets_by_agency.setdefault(bet.agency, []).append(bet)
        winners_by_agency = {}
        for agency, bets in bets_by_agency.items():
            winners = [bet.document for bet in bets if has_won(bet)]
            winners_by_agency[agency] = winners
        for agency, client_sock in self._client_sockets.items():
            protocol = LotteryProtocol(client_sock)
            winners = winners_by_agency.get(agency, [])
            try:
                protocol.send_winners_list(winners, agency)
            except Exception as e:
                logging.error(f"action: notify_winners | result: fail | agency: {agency} | error: {e}")
            #finally:
                #protocol.close()
        logging.info("action: lottery | result: success")

    def __accept_new_connection(self):
        """
        Accept new connections
        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        logging.info('action: accept_connections | result: in_progress')
        try:
            client_sock, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return client_sock
        except OSError as e:
            if not self._shutdown_requested:
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return None

    def _graceful_shutdown(self):
        logging.info("action: server_shutdown | result: in_progress")
        self._shutdown_requested = True
        self._close_server_socket()
        logging.info("action: server_shutdown | result: success")