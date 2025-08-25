import logging
import time
import requests
from utils.config import CryptoConfig, get_api_key

logger = logging.getLogger(__name__)

class CryptoDataCollector:
    def __init__(self):
        self.api_key = get_api_key()
        self.base_url = CryptoConfig.API_URL
    
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

            data = response.json()

            logger.info("CoinCap API request successful")
            return data
        
        except Exception as e:
            logger.error(f"Error collecting crypto data: {e}")
            raise