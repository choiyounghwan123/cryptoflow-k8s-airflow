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
            processed_data = context['task_instance'].xcom_pull(task_ids='preprocess_data')

            if not processed_data:
                raise ValueError("No processed data found")
            
            df = pd.DataFrame(processed_data)

            logger.info(f"Saving {len(df)} records to MinIO")

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


            current_time = datetime.now()
            date_str = current_time.strftime('%Y-%m-%d')
            hour_str = current_time.strftime('%H')
            filename = f"crypto_data_{current_time.strftime('%Y%m%d_%H%M%S')}.parquet"
            
            object_key = f"date={date_str}/hour={hour_str}/{filename}"
            
            # Parquet으로 저장
            parquet_buffer = BytesIO()
            df.to_parquet(
                parquet_buffer,
                engine='pyarrow',
                compression='snappy',  # 빠른 압축
                index=False
            )
            
            parquet_data = parquet_buffer.getvalue()
            file_size = len(parquet_data)
            
            # MinIO에 업로드
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=parquet_data,
                ContentType='application/octet-stream',
                Metadata={
                    'source': 'coincap-api',
                    'format': 'parquet',
                    'compression': 'snappy',
                    'record_count': str(len(df)),
                    'avg_quality_score': str(df['quality_score'].mean()),
                    'valid_records': str(df['is_valid'].sum()),
                    'collection_timestamp': current_time.isoformat()
                }
            )
            
            logger.info(f"Successfully saved to {object_key} ({file_size:,} bytes)")
            
            return {
                'bucket': bucket_name,
                'key': object_key,
                'record_count': len(df),
                'file_size_bytes': file_size,
                'avg_quality_score': df['quality_score'].mean(),
                'valid_records': df['is_valid'].sum()
            }
        except Exception as e:
            logger.error(f"Error saving data to MinIO: {e}")
            raise