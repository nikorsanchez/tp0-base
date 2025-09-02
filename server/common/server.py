import socket
import logging
import signal
from bets.protocol.protocol import LotteryProtocol
from bets.handlers.bet_handler import BetHandler
from common.utils import store_bets, bets_from_dict_list
from bets.models import Bet


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        
        self._shutdown_requested = False
        self._setup_signal_handler()

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
        communication with a Lottery client. After client with communucation
        finishes, servers starts to accept new connections again
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

        def handle_batch_failure(context, batch_count, error):
            logging.error(f"action: {context} | result: fail | batch: {batch_count} | error: {error}")
            protocol.send_confirmation_failed()

        try:
            while not self._shutdown_requested:
                try:
                    client_sock.settimeout(10.0)  # 10 second timeout

                    message_data = protocol.receive_message()
                    if message_data is None:
                        logging.info("action: client_disconnected | result: success | reason: no_data")
                        break

                    addr = client_sock.getpeername()
                    batch_count += 1
                    logging.info(f'action: receive_batch | result: success | ip: {addr[0]} | batch: {batch_count}')

                    response = BetHandler.process_batch_bet(message_data)

                    if response.get('status') == 'success':
                        try:
                            bet_objects = bets_from_dict_list(message_data['bets'])
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
            protocol.close()


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