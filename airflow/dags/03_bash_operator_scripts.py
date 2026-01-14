"""
03 - Exemple avec BashOperator : Exécuter des Scripts Externes

Ce fichier démontre comment :
- Utiliser BashOperator pour exécuter des scripts shell/Python
- Exploiter les template variables Airflow ({{ ds }}, {{ ds_nodash }}, etc.)
- Orchestrer des scripts existants dans un pipeline
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


# Default arguments
default_args = {
    'owner': 'data-eng',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
}


# =============================================================================
# Template Variables Airflow - Référence Rapide
# =============================================================================
#
# {{ ds }}              : Date d'exécution (YYYY-MM-DD)
# {{ ds_nodash }}       : Date sans tirets (YYYYMMDD)
# {{ execution_date }}  : Timestamp complet d'exécution
# {{ prev_ds }}         : Date de l'exécution précédente
# {{ next_ds }}         : Date de la prochaine exécution
# {{ dag.dag_id }}      : ID de la DAG
# {{ task.task_id }}    : ID de la task courante
# {{ ti.xcom_pull() }}  : Récupérer une valeur XCom
# {{ params.key }}      : Accéder aux paramètres personnalisés
#
# =============================================================================


with DAG(
    dag_id='bash_operator_scripts_example',
    default_args=default_args,
    schedule='@daily',
    catchup=False,
    tags=['bash', 'scripts', 'example'],
    description='Pipeline utilisant BashOperator pour orchestrer des scripts',
) as dag:
    
    # -------------------------------------------------------------------------
    # Task 1: Ingestion des données depuis une API
    # -------------------------------------------------------------------------
    # Appelle un script Python externe avec un fichier d'état
    # pour gérer l'ingestion incrémentale
    
    t_ingest = BashOperator(
        task_id='run_ingest',
        bash_command='''
            echo "Démarrage de l'ingestion pour la date {{ ds }}"
            python /scripts/ingest_api.py \
                --state-file state.json \
                --date {{ ds }}
            echo "Ingestion terminée"
        ''',
    )
    
    # -------------------------------------------------------------------------
    # Task 2: Validation des données
    # -------------------------------------------------------------------------
    # Valide les données ingérées pour la date d'exécution
    
    t_validate = BashOperator(
        task_id='run_validate',
        bash_command='''
            echo "Validation des données pour {{ ds }}"
            python /scripts/validate_data.py \
                /data/bronze/date={{ ds }}/data.parquet
        ''',
    )
    
    # -------------------------------------------------------------------------
    # Task 3: Transformation Bronze -> Silver
    # -------------------------------------------------------------------------
    # Applique les transformations et nettoie les données
    
    t_transform = BashOperator(
        task_id='run_transform',
        bash_command='''
            echo "Transformation Bronze -> Silver pour {{ ds }}"
            python /scripts/transform_data.py \
                --input /data/bronze/date={{ ds }}/data.parquet \
                --output /data/silver/date={{ ds }}/data.parquet
        ''',
    )
    
    # -------------------------------------------------------------------------
    # Task 4: Chargement vers le Data Warehouse
    # -------------------------------------------------------------------------
    # Charge les données nettoyées vers BigQuery/PostgreSQL
    
    t_load = BashOperator(
        task_id='run_load',
        bash_command='''
            echo "Chargement vers le Data Warehouse pour {{ ds }}"
            python /scripts/load_to_warehouse.py \
                --source /data/silver/date={{ ds }}/data.parquet \
                --table crypto_prices \
                --partition-date {{ ds_nodash }}
        ''',
    )
    
    # -------------------------------------------------------------------------
    # Task 5: Notification de succès (optionnel)
    # -------------------------------------------------------------------------
    
    t_notify = BashOperator(
        task_id='notify_success',
        bash_command='''
            echo "Pipeline terminé avec succès pour {{ ds }}"
            echo "DAG: {{ dag.dag_id }}"
            echo "Run ID: {{ run_id }}"
        ''',
    )
    
    # -------------------------------------------------------------------------
    # Définition des dépendances
    # -------------------------------------------------------------------------
    # ingest -> validate -> transform -> load -> notify
    
    t_ingest >> t_validate >> t_transform >> t_load >> t_notify
