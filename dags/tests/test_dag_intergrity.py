import os
# from airflow.models import DagBag

def test_dag_integrity():
    dag_dir = os.path.join(os.getcwd(),"dags")
    bag = DagBag(dag_folder=dag_dir, include_examples=False, safe_mode=True)
    assert len(bag.import_errors) == 0, f"Import errors: {bag.import_errors}"
