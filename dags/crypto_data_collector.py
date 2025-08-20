import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
import json
from botocore.exceptions import ClientError

API_KEY = "139f371038c23b420a4450bf50e9cc902ef19028a6fd9069b0d7e83fb7ad6408"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def collect_crypto_data():
    try:
        url = "https://rest.coincap.io/v3/assets/"
        params = {"limit": 10}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    
    except Exception as e:
        print(f"Error: {e}")
        raise

def save_to_minio():
    try:
        crypto_data = context['task_instance'].xcom_pull(task_ids='collect_crypto')
        if not crypto_data:
            raise ValueError("No crypto data found")
    except Exception as e:
        print(f"Error saving to MinIO: {e}")


default_args = {
    'owner': 'choiyounghwan',
    'depends_on_past': False,
    'start_date': datetime(2025, 8, 20),
    'email_on_failure': True,
    'email_on_retry': True,
    'email': ['choiyounghwan@gmail.com'],
    'email_on_success': False,
    'retries': 1,
    'retry_delay':timedelta(minutes=5)
}

with DAG(
    dag_id = 'crypto_minio_pipeline',
    description = '🚀 암호화폐 데이터를 MinIO에 저장하는 파이프라인',
    default_args = default_args,
    schedule_interval = timedelta(minutes=10),
    catchup = False,
    tags = ['crypto', 'minio','bronze-layer'],
) as dag:
    collect_task = PythonOperator(
        task_id = 'collect_crypto',
        python_callable = collect_crypto_data,
        provide_context = True,
    )

    save_task = PythonOperator(
        task_id = 'save_to_minio',
        python_callable = save_to_minio,
        provide_context = True,
    )

    collect_task >> save_task
