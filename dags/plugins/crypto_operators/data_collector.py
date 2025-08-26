import sys
import os
import logging
import time
import requests
from datetime import datetime, timezone

# Add dags directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import CryptoConfig, get_api_key

logger = logging.getLogger(__name__)

class CryptoDataCollector:
    @staticmethod
    def collect_crypto_data(**context):
        try:
            api_key = get_api_key()
            base_url = CryptoConfig.API_URL

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            params = { "limit": CryptoConfig.LIMIT }

            logger.info("CoinCap API request started")

            response = requests.get(
            base_url,
            headers=headers,
            params=params,
            timeout=30
            )

            response.raise_for_status()

            raw_data = response.json()
            raw_data['_metadate'] = {
                'collected_at': datetime.now(tz=timezone.utc).isoformat(),
                'api_endpoint': base_url,
                'response_status': response.status_code
                
            }
            logger.info("CoinCap API request successful")
            return raw_data
        
        except Exception as e:
            logger.error(f"Error collecting crypto data: {e}")
            raise