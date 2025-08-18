from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello():
    print("Git Sync 동작 확인!")
    return "ok"

dag = DAG(
    dag_id="test_git_sync",
    start_date=datetime(2025, 8, 18),
    schedule=None,
    catchup=False,
)

PythonOperator(
    task_id="print_hello",
    python_callable=hello,
    dag=dag
)
