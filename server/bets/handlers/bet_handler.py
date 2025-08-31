import logging
from bets.models.bet import Bet
from common.utils import store_bets

class BetHandler:
    @staticmethod
    def process_bet(bet_data: dict) -> dict:
        """
        Processes bet data and stores it
        """
        try:
            required_fields = ['agency', 'first_name', 'last_name', 
                              'document', 'birthdate', 'number']
            
            for field in required_fields:
                if field not in bet_data:
                    return {'status': 'error', 'message': f'Field missing: {field}'}
            
            bet = Bet(
                agency=bet_data['agency'],
                first_name=bet_data['first_name'],
                last_name=bet_data['last_name'],
                document=bet_data['document'],
                birthdate=bet_data['birthdate'],
                number=bet_data['number']
            )
            
            store_bets([bet])
            
            return {'status': 'success', 'message': 'Bet stored successfully'}
            
        except Exception as e:
            logging.error(f"action: process_bet | result: fail | error: {e}")
            return {'status': 'error', 'message': str(e)}