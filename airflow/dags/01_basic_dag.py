"""
01 - Introduction à Apache Airflow : Structure de base d'une DAG

Ce fichier présente la structure fondamentale d'une DAG Airflow :
- Import des modules essentiels
- Configuration des arguments par défaut
- Définition d'une DAG avec ses paramètres principaux
"""

from airflow import DAG
from datetime import datetime, timedelta

# Default arguments pour toutes les tasks
# Ces arguments seront hérités par toutes les tasks de la DAG
default_args = {
    'owner': 'data-eng',           # Propriétaire de la DAG
    'retries': 2,                   # Nombre de tentatives en cas d'échec
    'retry_delay': timedelta(minutes=5),  # Délai entre les tentatives
    'start_date': datetime(2025, 1, 1),   # Date de début d'exécution
}

# Définir la DAG
# Le context manager 'with' permet de définir les tasks à l'intérieur
with DAG(
    dag_id='basic_dag_intro',       # Identifiant unique de la DAG
    default_args=default_args,
    schedule='@daily',              # Fréquence d'exécution
                                    # Alternatives: '@hourly', '@weekly', '0 2 * * *' (cron)
    catchup=False,                  # Ne pas exécuter les runs manqués
    tags=['intro', 'basic'],        # Tags pour organiser les DAGs
    description='DAG de démonstration - Introduction à Airflow',
) as dag:
    # Les tasks se définissent ici
    # Voir les exemples suivants pour les différents types de tasks
    pass
