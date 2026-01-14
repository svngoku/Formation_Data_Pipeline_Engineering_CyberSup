from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default arguments pour toutes les tasks
default_args = {
    'owner': 'data-eng',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
}

# Définir la DAG
with DAG(
    dag_id='data_pipeline',
    default_args=default_args,
    schedule='@daily',        # ou '0 2 * * *' (cron)
    catchup=True,
) as dag:
    # Les tasks se définissent ici (voir slide suivant)
    pass



# Créer des Tasks : PythonOperator

def extract_data():
    """Fonction Python pour étape extract."""
    import requests
    resp = requests.get("https://api.coingecko.com/api/v3/simple/price")
    return resp.json()

def transform_data(ti):
    """ti = TaskInstance pour accéder XCom."""
    data = ti.xcom_pull(task_ids='extract')
    # Transformer...
    return transformed_data

# Créer les tasks
t_extract = PythonOperator(
    task_id='extract',
    python_callable=extract_data
)

t_transform = PythonOperator(
    task_id='transform',
    python_callable=transform_data
)

# Définir dépendance
t_extract >> t_transform  # extract PUIS transform



# BashOperator : Exécuter des Scripts
### Appeler script Python externe (TP2.1 + TP2.2)
t_ingest = BashOperator(
    task_id='run_ingest',
    bash_command='python /scripts/ingest_api.py --state-file state.json',
)

t_validate = BashOperator(
    task_id='run_validate',
    bash_command='python /scripts/validate_data.py /data/bronze/date={{ds}}/data.parquet',
)

# Template variables disponibles
# {{ ds }} = execution date (YYYY-MM-DD)
# {{ ds_nodash }} = YYYYMMDD
# {{ execution_date }} = full timestamp
# {{ ti.xcom_pull() }} = récupérer XCom

# Dépendances
t_ingest >> t_validate