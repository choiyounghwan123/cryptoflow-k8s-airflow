import sys
import os
import logging
import json
import pandas as pd
import boto3
from io import BytesIO
from datetime import datetime

# Add dags directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.config import get_minio_config

logger = logging.getLogger(__name__)

class MinIOStorageManager:
    @staticmethod
    def save_to_minio(**context):
        try:
            raw_data = context['task_instance'].xcom_pull(task_ids='preprocess_data')

            if not raw_data:
                raise ValueError("No processed data found")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f'crypto_data_{timestamp}.json'

            minio_config = get_minio_config()
            bucket_name = 'crypto-data'
            s3_client = boto3.client(
                's3',
                **minio_config
            )

            # 버킷 생성
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except Exception as e:
                if e.response['Error']['Code'] == '404':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    raise
                
            s3_client.put_object(
                bucket_name=bucket_name,
                object_name=filepath,
                data=BytesIO(json.dumps(raw_data).encode('utf-8')),
                length=len(json.dumps(raw_data).encode('utf-8')),
            )
            logger.info(f"Saved data to MinIO: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving data to MinIO: {e}")
            raise