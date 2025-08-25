import os
from airflow.models import Variable

class CtyptoConfig:
    API_URL = 'https://rest.coincap.io/v3/assets/'
    LIMIT = 10
    TIMEOUT = 30
    MAX_RETRIES = 3


def get_api_key():
    return Variable.get("COINCAP_API_KEY")

def get_minio_config():
    return {
        'endpoint_url': Variable.get("endpoint_url"),
        'aws_access_key_id': Variable.get("aws_access_key_id"),
        'aws_secret_access_key': Variable.get("aws_secret_access_key"),
    }
