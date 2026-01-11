# Jour 3 — Orchestration Big Data avec Airflow

> **Durée totale** : 7h  
> **Objectif** : Maîtriser Apache Airflow pour orchestrer des pipelines data robustes et production-ready

---

## 🌅 MATIN (3h30)

### 08:30 - 08:45 | Réactivation Jour 2 (15 min)
- Retour sur les scripts d'ingestion
- Questions sur le pattern n8n + scripts
- Transition : "Pourquoi aller plus loin que n8n ?"

### 08:45 - 10:15 | Bloc Théorique : "Des workflows à des DAGs" (1h30)

#### Partie 1 : Limites de n8n pour le Data Engineering (15 min)

| Aspect | n8n | Besoin Data Engineering |
|--------|-----|-------------------------|
| Scheduling | ✅ Cron simple | ❌ Backfill, catchup |
| Dépendances | ⚠️ Linéaire | Graphe complexe (DAG) |
| Retry granulaire | ⚠️ Basic | Par task, exponential |
| Observabilité | ⚠️ Logs simples | Metrics, lineage |
| State management | ❌ Manuel | ✅ Base de données |
| Scalabilité | ❌ Single node | Workers distribués |

**Conclusion** : n8n = prototypage, Airflow = production data pipelines

#### Partie 2 : Architecture Airflow (35 min)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Architecture Airflow                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │   Scheduler  │────►│   Executor   │────►│      Workers         │    │
│  │              │     │              │     │  (LocalExecutor ou   │    │
│  │  Parse DAGs  │     │ Queue tasks  │     │   CeleryExecutor)    │    │
│  │  Schedule    │     │              │     └──────────────────────┘    │
│  └──────┬───────┘     └──────────────┘                                  │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────┐     ┌──────────────┐                                  │
│  │  Metadata    │◄───►│  Webserver   │  ← Interface utilisateur        │
│  │   Database   │     │   (Flask)    │                                  │
│  │  (Postgres)  │     └──────────────┘                                  │
│  └──────────────┘                                                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                          DAG Files                                │  │
│  │   /dags/                                                          │  │
│  │   ├── pipeline_bronze.py                                          │  │
│  │   ├── pipeline_silver.py                                          │  │
│  │   └── pipeline_gold.py                                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Composants clés** :

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| Scheduler | Parse DAGs, schedule tasks | Python process |
| Webserver | UI, API REST | Flask |
| Executor | Distribue les tâches | Local, Celery, K8s |
| Workers | Exécute les tâches | Python processes |
| Metadata DB | State, historique | Postgres (prod), SQLite (dev) |

#### Partie 3 : Concepts fondamentaux (40 min)

**DAG (Directed Acyclic Graph)**
```python
from airflow import DAG
from datetime import datetime, timedelta

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@company.com"],
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="pipeline_bronze",
    default_args=default_args,
    description="Ingestion des données brutes",
    schedule_interval="@daily",          # ou cron: "0 6 * * *"
    start_date=datetime(2024, 1, 1),
    catchup=False,                        # Important !
    tags=["bronze", "ingestion"],
) as dag:
    # Tasks définies ici
    pass
```

**Operators principaux**
```python
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.filesystem import FileSensor

# BashOperator : exécute une commande shell
ingest = BashOperator(
    task_id="ingest_data",
    bash_command="python /scripts/ingest_api.py --date {{ ds }}",
)

# PythonOperator : exécute une fonction Python
def process_data(**context):
    execution_date = context["ds"]
    print(f"Processing data for {execution_date}")

process = PythonOperator(
    task_id="process_data",
    python_callable=process_data,
)

# Sensor : attend une condition
wait_file = FileSensor(
    task_id="wait_for_file",
    filepath="/data/bronze/{{ ds }}/data.parquet",
    poke_interval=60,
    timeout=3600,
)

# EmptyOperator : point de synchronisation
start = EmptyOperator(task_id="start")
end = EmptyOperator(task_id="end")

# Définir les dépendances
start >> ingest >> wait_file >> process >> end
```

**Variables et Connections**
```python
from airflow.models import Variable, Connection

# Variables (stockées en DB, éditables via UI)
api_key = Variable.get("API_KEY")
config = Variable.get("PIPELINE_CONFIG", deserialize_json=True)

# Connections (credentials centralisés)
# Créées via UI ou CLI : airflow connections add ...
# Utilisées dans les operators :
from airflow.providers.postgres.operators.postgres import PostgresOperator

load = PostgresOperator(
    task_id="load_to_postgres",
    postgres_conn_id="my_postgres",  # ← référence à une Connection
    sql="INSERT INTO events SELECT * FROM staging;",
)
```

**Scheduling et Backfill**
```
┌────────────────────────────────────────────────────────────────────┐
│                     Scheduling Airflow                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  start_date = 2024-01-01                                           │
│  schedule_interval = @daily                                         │
│                                                                     │
│  Timeline:                                                          │
│  ───────────────────────────────────────────────────────────────►  │
│  Jan 1    Jan 2    Jan 3    Jan 4    Jan 5                         │
│    │        │        │        │        │                           │
│    └── Run ─┴── Run ─┴── Run ─┴── Run ─┘                          │
│        for     for     for     for                                  │
│       Jan 1   Jan 2   Jan 3   Jan 4                                │
│                                                                     │
│  ⚠️ execution_date = date DÉBUT de l'intervalle                    │
│  ⚠️ Le run pour Jan 1 s'exécute le Jan 2 à 00:00                  │
│                                                                     │
│  catchup=True  → Exécute tous les runs manqués                     │
│  catchup=False → Exécute seulement le dernier                      │
└────────────────────────────────────────────────────────────────────┘
```

**Templating Jinja**
```python
# Variables disponibles dans les templates
BashOperator(
    task_id="example",
    bash_command="""
        echo "Execution date: {{ ds }}"           # 2024-01-15
        echo "Execution datetime: {{ ts }}"       # 2024-01-15T00:00:00+00:00
        echo "Previous date: {{ prev_ds }}"       # 2024-01-14
        echo "Next date: {{ next_ds }}"           # 2024-01-16
        echo "DAG ID: {{ dag.dag_id }}"          # pipeline_bronze
        echo "Task ID: {{ task.task_id }}"       # example
        echo "Variable: {{ var.value.API_KEY }}" # valeur de la variable
    """,
)
```

### 10:15 - 10:30 | ☕ Pause (15 min)

### 10:30 - 12:00 | Démonstration : Setup Airflow (1h30)

#### Installation avec Docker Compose (45 min)

**Structure projet**
```
airflow/
├── docker-compose.yaml
├── dags/
│   └── example_dag.py
├── logs/
├── plugins/
├── scripts/
│   ├── ingest_api.py
│   └── validate_data.py
└── data/
    ├── bronze/
    └── silver/
```

**docker-compose.yaml simplifié**
```yaml
version: '3.8'

x-airflow-common: &airflow-common
  image: apache/airflow:2.8.0
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    _PIP_ADDITIONAL_REQUIREMENTS: pandas pyarrow requests tenacity
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./scripts:/opt/airflow/scripts
    - ./data:/opt/airflow/data
  depends_on:
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  airflow-init:
    <<: *airflow-common
    command: >
      bash -c "
        airflow db init &&
        airflow users create \
          --username admin \
          --password admin \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@example.com
      "

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
```

**Lancement**
```bash
# Initialiser
docker-compose up airflow-init

# Démarrer
docker-compose up -d

# Vérifier
docker-compose ps
open http://localhost:8080  # admin/admin
```

#### Exploration de l'interface (30 min)

**Pages clés** :
1. **DAGs** : Liste, état, actions (trigger, pause)
2. **Grid View** : Historique des runs par task
3. **Graph View** : Visualisation du DAG
4. **Gantt** : Timeline d'exécution
5. **Code** : Source du DAG
6. **Admin > Variables** : Gestion des variables
7. **Admin > Connections** : Gestion des connexions

**Actions pratiques** :
- Trigger manuel d'un DAG
- Voir les logs d'une task
- Marquer une task comme success/failed
- Clear une task pour re-run

#### Premier DAG de test (15 min)
```python
# dags/hello_world.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def greet(name: str):
    print(f"Hello, {name}!")
    return f"Greeted {name}"

with DAG(
    dag_id="hello_world",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=["example"],
) as dag:

    task1 = BashOperator(
        task_id="print_date",
        bash_command="date",
    )

    task2 = PythonOperator(
        task_id="greet",
        python_callable=greet,
        op_kwargs={"name": "Airflow"},
    )

    task1 >> task2
```

### 12:00 - 12:15 | Checkpoint matin (15 min)

**Quiz** :
1. Quelle est la différence entre `schedule_interval` et `start_date` ?
2. Que signifie `catchup=False` ?
3. Comment passer des paramètres à un BashOperator avec la date du run ?

---

## 🍽️ PAUSE DÉJEUNER (12:15 - 13:30)

---

## 🌆 APRÈS-MIDI (3h30)

### 13:30 - 15:30 | TP3.2 : DAG "ingest → validate → load" (2h)

#### Objectif
> Créer un DAG Airflow qui orchestre les scripts développés les jours 1-2

#### DAG `pipeline_bronze.py` - Construction guidée

**Étape 1 : Structure de base (20 min)**
```python
# dags/pipeline_bronze.py
"""
Pipeline Bronze : Ingestion des données brutes.
- Exécution quotidienne à 06:00 UTC
- Ingestion API → Validation → Stockage Parquet
"""
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# Configuration
SCRIPTS_DIR = "/opt/airflow/scripts"
DATA_DIR = "/opt/airflow/data"

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["data-alerts@company.com"],
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}

with DAG(
    dag_id="pipeline_bronze",
    default_args=default_args,
    description="Ingestion quotidienne des données API vers Bronze",
    schedule_interval="0 6 * * *",  # Tous les jours à 06:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["bronze", "ingestion", "api"],
) as dag:
    pass  # Tasks à ajouter
```

**Étape 2 : Tasks d'ingestion et validation (40 min)**
```python
    # --- TASKS ---
    
    start = EmptyOperator(task_id="start")
    
    # Task 1: Ingestion
    ingest = BashOperator(
        task_id="ingest_api",
        bash_command=f"""
            python {SCRIPTS_DIR}/ingest_api.py \
                --start-date {{{{ ds }}}} \
                --end-date {{{{ ds }}}} \
                --output-dir {DATA_DIR}/bronze
        """,
        env={
            "PYTHONPATH": SCRIPTS_DIR,
        },
    )
    
    # Task 2: Validation
    validate = BashOperator(
        task_id="validate_data",
        bash_command=f"""
            # Trouver le fichier le plus récent pour cette date
            FILE=$(ls -t {DATA_DIR}/bronze/partition_date={{{{ ds }}}}/*.parquet | head -1)
            
            python {SCRIPTS_DIR}/validate_data.py \
                --input-file "$FILE" \
                --rules-file {SCRIPTS_DIR}/validation_rules.json
        """,
    )
    
    # Task 3: Décision basée sur validation
    def check_validation_result(**context):
        """Branch selon le résultat de validation."""
        ti = context["ti"]
        # En réalité, on lirait le résultat du XCom ou d'un fichier
        # Pour simplifier, on suppose succès
        return "log_success"
    
    branch = BranchPythonOperator(
        task_id="check_result",
        python_callable=check_validation_result,
    )
    
    # Task 4a: Succès
    log_success = BashOperator(
        task_id="log_success",
        bash_command='echo "Validation passed for {{ ds }}"',
    )
    
    # Task 4b: Échec
    handle_failure = BashOperator(
        task_id="handle_failure",
        bash_command=f"""
            # Déplacer vers quarantaine
            mkdir -p {DATA_DIR}/quarantine/{{{{ ds }}}}
            mv {DATA_DIR}/bronze/partition_date={{{{ ds }}}}/*.parquet \
               {DATA_DIR}/quarantine/{{{{ ds }}}}/
            echo "Data moved to quarantine"
        """,
    )
    
    # Task finale
    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )
    
    # --- DEPENDENCIES ---
    start >> ingest >> validate >> branch
    branch >> [log_success, handle_failure] >> end
```

**Étape 3 : Ajout de XCom pour communication inter-tasks (30 min)**
```python
from airflow.operators.python import PythonOperator
import json

def ingest_with_xcom(**context):
    """Ingestion avec retour de métadonnées via XCom."""
    import subprocess
    
    ds = context["ds"]
    cmd = [
        "python", f"{SCRIPTS_DIR}/ingest_api.py",
        "--start-date", ds,
        "--end-date", ds,
        "--output-dir", f"{DATA_DIR}/bronze"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Ingestion failed: {result.stderr}")
    
    # Parser le JSON de sortie
    output = json.loads(result.stdout)
    
    # Pousser vers XCom pour les tasks suivantes
    context["ti"].xcom_push(key="output_file", value=output["output_file"])
    context["ti"].xcom_push(key="records_count", value=output["records_count"])
    
    return output

ingest = PythonOperator(
    task_id="ingest_api",
    python_callable=ingest_with_xcom,
)

def validate_with_xcom(**context):
    """Validation utilisant le fichier de XCom."""
    ti = context["ti"]
    input_file = ti.xcom_pull(task_ids="ingest_api", key="output_file")
    
    # ... validation logic ...
    return {"status": "passed", "file": input_file}

validate = PythonOperator(
    task_id="validate_data",
    python_callable=validate_with_xcom,
)
```

**Étape 4 : Variables et configuration (30 min)**

Via UI : Admin > Variables
```json
{
  "api_base_url": "https://jsonplaceholder.typicode.com",
  "validation_rules": {
    "required_columns": ["id", "title"],
    "min_rows": 1
  }
}
```

Utilisation dans le DAG :
```python
from airflow.models import Variable

# Récupérer une variable simple
api_url = Variable.get("api_base_url")

# Récupérer une variable JSON
rules = Variable.get("validation_rules", deserialize_json=True)

# Dans un template (Bash)
bash_command="""
    python script.py --api-url {{ var.value.api_base_url }}
"""
```

### 15:30 - 15:45 | ☕ Pause (15 min)

### 15:45 - 16:45 | TP3.3 : Gestion des erreurs et re-runs (1h)

#### Scénarios de test

**Scénario 1 : Échec d'une task (20 min)**
```python
# Forcer un échec
fail_task = BashOperator(
    task_id="failing_task",
    bash_command="exit 1",  # Force failure
)
```

Démonstration :
1. Trigger le DAG
2. Observer l'état "failed" dans Grid View
3. Voir les logs de la task
4. Clear la task pour re-run
5. Observer le retry automatique

**Scénario 2 : Retry avec backoff (20 min)**
```python
from airflow.operators.python import PythonOperator
import random

def flaky_function():
    """Fonction qui échoue aléatoirement."""
    if random.random() < 0.7:  # 70% de chance d'échec
        raise Exception("Random failure!")
    return "Success!"

flaky_task = PythonOperator(
    task_id="flaky_task",
    python_callable=flaky_function,
    retries=5,
    retry_delay=timedelta(seconds=30),
    retry_exponential_backoff=True,
    max_retry_delay=timedelta(minutes=10),
)
```

**Scénario 3 : Backfill historique (20 min)**
```bash
# Via CLI
docker-compose exec airflow-scheduler \
    airflow dags backfill \
    --start-date 2024-01-01 \
    --end-date 2024-01-07 \
    pipeline_bronze

# Ou via UI : DAG > Grid > Sélectionner dates > Actions > Clear
```

### 16:45 - 17:15 | Discussion : Patterns avancés (30 min)

**TaskFlow API (Airflow 2.x)**
```python
from airflow.decorators import dag, task

@dag(schedule_interval="@daily", start_date=datetime(2024, 1, 1), catchup=False)
def modern_pipeline():
    
    @task
    def extract():
        return {"data": [1, 2, 3]}
    
    @task
    def transform(data: dict):
        return {"processed": [x * 2 for x in data["data"]]}
    
    @task
    def load(data: dict):
        print(f"Loading: {data}")
    
    # Chaînage automatique via XCom
    raw = extract()
    processed = transform(raw)
    load(processed)

# Instancier le DAG
modern_pipeline()
```

**Dynamic Task Mapping**
```python
@task
def get_partitions():
    return ["2024-01-01", "2024-01-02", "2024-01-03"]

@task
def process_partition(partition: str):
    print(f"Processing {partition}")

@dag(...)
def dynamic_dag():
    partitions = get_partitions()
    process_partition.expand(partition=partitions)  # Crée N tasks dynamiquement
```

### 17:15 - 17:30 | Wrap-up Jour 3 (15 min)

#### Livrables attendus
- [ ] Airflow fonctionnel (docker-compose)
- [ ] DAG `pipeline_bronze.py` opérationnel
- [ ] Documentation des Variables/Connections
- [ ] README mis à jour

#### Récapitulatif
```
J3 : Orchestration Airflow
├── Architecture : Scheduler, Workers, Metadata DB
├── Concepts : DAG, Operators, Tasks, XCom
├── Scheduling : start_date, schedule_interval, catchup
├── Error handling : retries, backoff, trigger_rules
├── Ops : Backfill, Clear, Re-run
└── Modern : TaskFlow API, Dynamic Mapping
```

#### Preview Jour 4
> Demain : dbt pour les transformations SQL + Prefect comme alternative Python-first

---

## 📚 Ressources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Astronomer Guides](https://docs.astronomer.io/learn)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)

## ⚠️ Points d'attention formateur

1. **Docker resources** : Airflow consomme ~4GB RAM minimum
2. **Scheduler lag** : Les DAGs peuvent prendre 30s à apparaître
3. **Timezone** : Airflow utilise UTC par défaut
4. **XCom limits** : Éviter de passer de gros volumes via XCom (< 48KB recommandé)
