import socket
import logging
import signal
from bets.protocol.protocol import LotteryProtocol
from bets.handlers.bet_handler import BetHandler
from common.utils import store_bets
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
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        protocol = LotteryProtocol(client_sock)
        try:
            message = protocol.receive_message()
            
            if message is None:
                logging.error("action: receive_message | result: fail | error: invalid_message")
                return
            
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | message: {message}')
            
            response = BetHandler.process_bet(message)

            if response.get('status') == 'success':
                try:
                    bet = Bet(
                        message['agency'],
                        message['first_name'],
                        message['last_name'],
                        message['document'],
                        message['birthdate'],
                        message['number']
                    )
                    store_bets([bet])
                    logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document}")
                    protocol.send_confirmation()
                except Exception as e:
                    logging.error(f"action: apuesta_almacenada | result: fail | error: {e}")
            else:
                protocol.send_message(response)
            
        except Exception as e:
            logging.error(f"action: handle_client | result: fail | error: {e}")
            error_response = {'status': 'error', 'message': 'Server error'}
            protocol.send_message(error_response)
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
