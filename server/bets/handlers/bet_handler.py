import logging
from bets.models import Bet
from common.utils import store_bets

class BetHandler:

    @staticmethod
    def process_batch_bet(batch_data):
        """
        Process a batch of bets
        """
        successful_bets = []
        failed_bets = []
        
        for bet_dict in batch_data['bets']:
            validation = BetHandler._validate_bet(bet_dict)
            if validation['status'] == 'success':
                successful_bets.append(bet_dict)
            else:
                failed_bets.append({'bet': bet_dict, 'error': validation['message']})
        
        total_bets = len(batch_data['bets'])
        successful_count = len(successful_bets)
        failed_count = len(failed_bets)
        
        if failed_count == 0:
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {total_bets}")
            return {'status': 'success', 'processed_count': successful_count}
        else:
            logging.info(f"action: apuesta_recibida | result: fail | cantidad: {total_bets}")
            return {
                'status': 'error', 
                'processed_count': successful_count,
                'failed_count': failed_count,
                'errors': failed_bets
            }

    @staticmethod
    def _validate_bet(bet_dict):
        """
        Validate a single bet
        """
        required_fields = ['first_name', 'last_name', 'document', 'birthdate', 'number']
        for field in required_fields:
            if not bet_dict.get(field):
                return {'status': 'error', 'message': f'Missing field: {field}'}
        
        if not bet_dict['document'].isdigit():
            return {'status': 'error', 'message': 'Invalid document format'}
        
        if not bet_dict['number'].isdigit():
            return {'status': 'error', 'message': 'Invalid number format'}
        
        return {'status': 'success'}