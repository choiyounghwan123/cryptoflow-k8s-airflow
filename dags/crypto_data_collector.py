import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
import json
from botocore.exceptions import ClientError

API_KEY = "139f371038c23b420a4450bf50e9cc902ef19028a6fd9069b0d7e83fb7ad6408"

MINIO_CONFIG = {
    'endpoint_url': 'http://minio:9000',
    'access_key': 'mlflow',
    'secret_key': 'mlflowpass',
}

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

def save_to_minio(**context):
    try:
        crypto_data = context['task_instance'].xcom_pull(task_ids='collect_crypto')
        if not crypto_data:
            raise ValueError("No crypto data found")
        
        s3_client = boto3.client('s3', **MINIO_CONFIG)
        bucket_name = 'crypto-data'

        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} created")
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_name = f'crypto_data_{timestamp}.json'

        json_data = json.dumps(crypto_data)
        json_bytes = json_data.encode('utf-8')

        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_bytes,
            ContentType='application/json'
        )
        
        print(f"File {file_name} uploaded to {bucket_name}")
        return file_name

        
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
    schedule = timedelta(minutes=10),
    catchup = False,
    tags = ['crypto', 'minio','bronze-layer'],
) as dag:
    collect_task = PythonOperator(
        task_id = 'collect_crypto',
        python_callable = collect_crypto_data,
    )

    save_task = PythonOperator(
        task_id = 'save_to_minio',
        python_callable = save_to_minio,
    )

    collect_task >> save_task
