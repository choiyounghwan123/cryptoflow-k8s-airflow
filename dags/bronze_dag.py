import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from plugins.crypto_operators.data_collector import CryptoDataCollector
from plugins.crypto_operators.data_preprocessor import CryptoDataPreprocessor
from plugins.crypto_operators.storage_manager import MinIOStorageManager

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='crypto_bronze_pipeline_v2',
    description='🚀 암호화폐 데이터 수집 → 전처리 → Parquet 저장',
    default_args=default_args,
    schedule_interval=timedelta(minutes=10),
    catchup=False,
    tags=['crypto', 'bronze-layer', 'parquet'],
) as dag:

    # 1. 데이터 수집
    collect_task = PythonOperator(
        task_id='collect_crypto',
        python_callable=CryptoDataCollector.collect_crypto_data,
    )

    # 2. 데이터 전처리 (추가!)
    preprocess_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=CryptoDataPreprocessor.preprocess_data,
    )

    # 3. Parquet 저장
    save_task = PythonOperator(
        task_id='save_to_minio',
        python_callable=MinIOStorageManager.save_to_minio,
    )

    # 순서: 수집 → 전처리 → 저장
    collect_task >> preprocess_task >> save_task
