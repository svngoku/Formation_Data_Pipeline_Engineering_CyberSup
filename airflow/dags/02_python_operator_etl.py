"""
02 - Exemple ETL avec PythonOperator

Ce fichier démontre comment créer un pipeline ETL avec Airflow :
- Utilisation de PythonOperator pour exécuter des fonctions Python
- Passage de données entre tasks via XCom
- Définition des dépendances entre tasks
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


# Default arguments
default_args = {
    'owner': 'data-eng',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
}


# =============================================================================
# Fonctions Python pour les étapes ETL
# =============================================================================

def extract_data(**kwargs):
    """
    Étape Extract : Récupérer les données depuis une API.
    
    Les données retournées sont automatiquement stockées dans XCom
    et peuvent être récupérées par les tasks suivantes.
    """
    import requests
    
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum',
        'vs_currencies': 'usd,eur'
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    print(f"Données extraites: {data}")
    
    return data  # Automatiquement poussé vers XCom


def transform_data(ti, **kwargs):
    """
    Étape Transform : Transformer les données.
    
    Args:
        ti: TaskInstance - permet d'accéder aux XCom des autres tasks
    """
    # Récupérer les données de la task 'extract' via XCom
    raw_data = ti.xcom_pull(task_ids='extract')
    
    if not raw_data:
        raise ValueError("Aucune donnée reçue de la task extract")
    
    # Transformation : Aplatir et enrichir les données
    transformed_data = []
    extraction_date = kwargs['ds']  # Date d'exécution (YYYY-MM-DD)
    
    for crypto, prices in raw_data.items():
        for currency, price in prices.items():
            transformed_data.append({
                'crypto': crypto,
                'currency': currency,
                'price': price,
                'extraction_date': extraction_date,
            })
    
    print(f"Données transformées: {transformed_data}")
    return transformed_data


def load_data(ti, **kwargs):
    """
    Étape Load : Charger les données vers la destination.
    
    Dans un cas réel, cela pourrait être :
    - Une base de données (PostgreSQL, BigQuery, etc.)
    - Un data lake (S3, GCS)
    - Un fichier Parquet
    """
    import json
    
    transformed_data = ti.xcom_pull(task_ids='transform')
    
    if not transformed_data:
        raise ValueError("Aucune donnée reçue de la task transform")
    
    # Simulation : sauvegarder en JSON
    output_path = f"/tmp/crypto_prices_{kwargs['ds_nodash']}.json"
    
    with open(output_path, 'w') as f:
        json.dump(transformed_data, f, indent=2)
    
    print(f"Données sauvegardées dans: {output_path}")
    return output_path


# =============================================================================
# Définition de la DAG et des Tasks
# =============================================================================

with DAG(
    dag_id='etl_python_operator_example',
    default_args=default_args,
    schedule='@daily',
    catchup=False,
    tags=['etl', 'python', 'example'],
    description='Pipeline ETL avec PythonOperator - Exemple crypto prices',
) as dag:
    
    # Task 1: Extract
    t_extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
    )
    
    # Task 2: Transform
    t_transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
    )
    
    # Task 3: Load
    t_load = PythonOperator(
        task_id='load',
        python_callable=load_data,
    )
    
    # Définir les dépendances (ordre d'exécution)
    # extract -> transform -> load
    t_extract >> t_transform >> t_load
