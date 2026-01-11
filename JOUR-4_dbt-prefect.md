# Jour 4 — dbt & Prefect : Transformations et Workflows Python

> **Durée totale** : 7h  
> **Objectif** : Maîtriser dbt pour les transformations SQL et découvrir Prefect comme orchestrateur Python-native

---

## 🌅 MATIN (3h30)

### 08:30 - 08:45 | Réactivation Jour 3 (15 min)
- Retour sur les DAGs Airflow
- Questions sur scheduling et backfill
- Introduction : "Le T de ELT"

### 08:45 - 10:15 | Bloc Théorique : "ELT moderne et Analytics Engineering" (1h30)

#### Partie 1 : ETL vs ELT (20 min)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ETL (Traditionnel)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Source ──► [Extract] ──► [Transform] ──► [Load] ──► Warehouse     │
│                              ▲                                       │
│                              │                                       │
│                    Transformation AVANT                              │
│                    chargement (ETL tools)                           │
│                                                                      │
│  Outils : Informatica, Talend, SSIS                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         ELT (Moderne)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Source ──► [Extract] ──► [Load] ──► Warehouse ──► [Transform]     │
│                                          ▲              │           │
│                                          │              │           │
│                               Transformation DANS       │           │
│                               le warehouse (SQL)        │           │
│                                                         ▼           │
│                                                   Tables finales    │
│                                                                      │
│  Outils : dbt, Dataform, SQLMesh                                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Pourquoi ELT aujourd'hui ?**
| Critère | ETL | ELT |
|---------|-----|-----|
| Coût compute | Serveurs ETL dédiés | Warehouse (pay-per-query) |
| Scalabilité | Limitée | Cloud-native |
| Flexibilité | Schéma rigide | Schema-on-read |
| Debugging | Logs ETL tools | SQL transparent |
| Collaboration | Propriétaire | Git, code review |

#### Partie 2 : Introduction à dbt (40 min)

**Qu'est-ce que dbt ?**
```
┌─────────────────────────────────────────────────────────────────────┐
│                           dbt (data build tool)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  "dbt permet aux analystes et ingénieurs de transformer             │
│   les données dans le warehouse en utilisant des instructions       │
│   SELECT simples"                                                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                       Workflow dbt                            │  │
│  │                                                               │  │
│  │   models/*.sql ──► dbt run ──► Tables/Views dans warehouse   │  │
│  │        │                                                      │  │
│  │        ├── Jinja templating                                  │  │
│  │        ├── Macros réutilisables                              │  │
│  │        ├── Tests automatiques                                │  │
│  │        └── Documentation générée                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Supporte : Snowflake, BigQuery, Redshift, Postgres, DuckDB...     │
└─────────────────────────────────────────────────────────────────────┘
```

**Concepts clés dbt**

| Concept | Description | Exemple |
|---------|-------------|---------|
| **Source** | Tables brutes (Bronze) | `{{ source('raw', 'events') }}` |
| **Model** | Transformation SQL | `stg_events.sql`, `fact_sales.sql` |
| **Test** | Validation des données | `unique`, `not_null`, `relationships` |
| **Macro** | Fonction Jinja réutilisable | `{{ cents_to_dollars(amount) }}` |
| **Seed** | Données statiques (CSV) | Mapping codes pays, lookup tables |
| **Snapshot** | Historisation (SCD Type 2) | Suivi des changements |

**Architecture Medallion avec dbt**
```
┌─────────────────────────────────────────────────────────────────────┐
│                     Medallion Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                    │
│  │  BRONZE  │────►│  SILVER  │────►│   GOLD   │                    │
│  │   raw_   │     │   stg_   │     │  dim_/   │                    │
│  │          │     │          │     │  fact_   │                    │
│  └──────────┘     └──────────┘     └──────────┘                    │
│       │                │                │                           │
│       ▼                ▼                ▼                           │
│  • Données brutes  • Nettoyées      • Business-ready              │
│  • Schéma source   • Typées         • Agrégées                    │
│  • Append-only     • Dédupliquées   • Jointes                     │
│  • Parquet/JSON    • Normalisées    • Documentées                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Structure projet dbt**
```
dbt_project/
├── dbt_project.yml          # Configuration projet
├── profiles.yml             # Connexions DB (hors repo)
├── models/
│   ├── staging/             # Silver layer
│   │   ├── _staging.yml     # Tests & docs
│   │   ├── stg_events.sql
│   │   └── stg_users.sql
│   ├── marts/               # Gold layer
│   │   ├── _marts.yml
│   │   ├── dim_users.sql
│   │   └── fact_events.sql
│   └── sources.yml          # Définition des sources
├── macros/
│   └── custom_macros.sql
├── seeds/
│   └── country_codes.csv
├── tests/
│   └── custom_tests.sql
└── snapshots/
    └── users_snapshot.sql
```

#### Partie 3 : Introduction à Prefect (30 min)

**Prefect vs Airflow**
```
┌────────────────────────────────────────────────────────────────────┐
│                    Prefect vs Airflow                               │
├──────────────────────┬─────────────────────────────────────────────┤
│       Airflow        │              Prefect                        │
├──────────────────────┼─────────────────────────────────────────────┤
│ DAG = fichier séparé │ Flow = décorateur Python                    │
│ Operators spécifiques│ Fonctions Python natives                    │
│ UI lourde            │ UI cloud ou self-hosted                     │
│ Config YAML/env      │ Config Python                               │
│ Scheduler central    │ Agent léger + API                           │
│ Mature, écosystème   │ Moderne, DX soignée                         │
└──────────────────────┴─────────────────────────────────────────────┘
```

**Concepts Prefect 2.x**
```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def extract(source: str) -> dict:
    """Extraction avec retry et cache."""
    # ... logic
    return {"data": [...]}

@task
def transform(data: dict) -> dict:
    """Transformation."""
    return {"processed": [...]}

@task
def load(data: dict, target: str):
    """Chargement."""
    # ... logic

@flow(name="ETL Pipeline", log_prints=True)
def etl_flow(source: str, target: str):
    """Flow principal."""
    raw = extract(source)
    processed = transform(raw)
    load(processed, target)

# Exécution
if __name__ == "__main__":
    etl_flow(source="api", target="warehouse")
```

### 10:15 - 10:30 | ☕ Pause (15 min)

### 10:30 - 12:00 | Démonstration : Setup dbt + Prefect (1h30)

#### Setup dbt avec DuckDB (45 min)

**Pourquoi DuckDB pour les TPs ?**
- Zéro configuration (fichier local)
- Compatible SQL analytique
- Lit directement Parquet
- Parfait pour le prototypage

**Installation**
```bash
# Installer dbt-core + adapter DuckDB
pip install dbt-core dbt-duckdb

# Vérifier
dbt --version
```

**Initialiser le projet**
```bash
cd /path/to/formation
dbt init dbt_training

# Répondre aux questions :
# - database: duckdb
# - path: data/warehouse.duckdb
```

**Configuration profiles.yml**
```yaml
# ~/.dbt/profiles.yml
dbt_training:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{{ env_var('DBT_DATABASE_PATH', 'data/warehouse.duckdb') }}"
      threads: 4
```

**Test connexion**
```bash
cd dbt_training
dbt debug
```

#### Setup Prefect (45 min)

**Installation**
```bash
pip install prefect

# Vérifier
prefect version
```

**Configuration (optionnel pour le TP)**
```bash
# Mode local (pas besoin de serveur)
prefect config set PREFECT_API_URL=""

# OU avec serveur local
prefect server start  # Terminal 1
prefect config set PREFECT_API_URL="http://localhost:4200/api"
```

**Premier flow**
```python
# flows/hello_prefect.py
from prefect import flow, task

@task
def say_hello(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message

@flow(name="hello-flow")
def hello_flow(name: str = "World"):
    result = say_hello(name)
    return result

if __name__ == "__main__":
    hello_flow("Prefect")
```

```bash
python flows/hello_prefect.py
```

### 12:00 - 12:15 | Checkpoint matin (15 min)

**Discussion** :
1. Dans quel cas utiliser dbt plutôt que Python/Pandas ?
2. Avantages de Prefect sur Airflow pour un data engineer ?
3. Comment dbt s'intègre-t-il dans le pipeline global ?

---

## 🍽️ PAUSE DÉJEUNER (12:15 - 13:30)

---

## 🌆 APRÈS-MIDI (3h30)

### 13:30 - 15:00 | TP4.1 : Projet dbt (1h30)

#### Objectif
> Créer un projet dbt qui transforme les données Bronze en tables analytiques Silver/Gold

#### Étape 1 : Configuration sources (15 min)

```yaml
# models/sources.yml
version: 2

sources:
  - name: bronze
    description: "Données brutes ingérées depuis l'API"
    schema: main  # Pour DuckDB
    tables:
      - name: raw_events
        description: "Événements bruts depuis l'API"
        external:
          location: "read_parquet('../data/bronze/**/*.parquet')"
        columns:
          - name: id
            description: "Identifiant unique"
          - name: userId
            description: "ID utilisateur"
          - name: title
            description: "Titre de l'événement"
          - name: body
            description: "Corps du message"
          - name: _ingested_at
            description: "Timestamp d'ingestion"
```

#### Étape 2 : Modèle Staging (25 min)

```sql
-- models/staging/stg_events.sql

{{
    config(
        materialized='view',
        tags=['staging', 'daily']
    )
}}

with source as (
    select * from {{ source('bronze', 'raw_events') }}
),

renamed as (
    select
        -- Identifiants
        id as event_id,
        "userId" as user_id,
        
        -- Contenu
        title as event_title,
        body as event_body,
        
        -- Métadonnées
        _ingested_at as ingested_at,
        
        -- Colonnes calculées
        length(body) as body_length,
        
        -- Audit
        current_timestamp as dbt_updated_at
        
    from source
),

deduplicated as (
    select *,
        row_number() over (
            partition by event_id 
            order by ingested_at desc
        ) as row_num
    from renamed
)

select * from deduplicated
where row_num = 1
```

```yaml
# models/staging/_staging.yml
version: 2

models:
  - name: stg_events
    description: "Événements nettoyés et dédupliqués"
    columns:
      - name: event_id
        description: "Identifiant unique de l'événement"
        tests:
          - unique
          - not_null
      - name: user_id
        description: "ID de l'utilisateur"
        tests:
          - not_null
      - name: event_title
        description: "Titre nettoyé"
        tests:
          - not_null
```

#### Étape 3 : Modèles Marts (30 min)

```sql
-- models/marts/dim_users.sql

{{
    config(
        materialized='table',
        tags=['marts', 'daily']
    )
}}

with events as (
    select * from {{ ref('stg_events') }}
),

user_stats as (
    select
        user_id,
        count(*) as total_events,
        min(ingested_at) as first_event_at,
        max(ingested_at) as last_event_at,
        avg(body_length) as avg_body_length
    from events
    group by user_id
)

select
    user_id,
    total_events,
    first_event_at,
    last_event_at,
    avg_body_length,
    
    -- Classification
    case
        when total_events >= 10 then 'power_user'
        when total_events >= 5 then 'active'
        else 'casual'
    end as user_segment,
    
    -- Audit
    current_timestamp as dbt_updated_at

from user_stats
```

```sql
-- models/marts/fact_daily_events.sql

{{
    config(
        materialized='table',
        tags=['marts', 'daily']
    )
}}

with events as (
    select * from {{ ref('stg_events') }}
),

daily_agg as (
    select
        date_trunc('day', ingested_at) as event_date,
        count(*) as event_count,
        count(distinct user_id) as unique_users,
        avg(body_length) as avg_body_length
    from events
    group by 1
)

select
    event_date,
    event_count,
    unique_users,
    avg_body_length,
    
    -- Métriques dérivées
    event_count::float / nullif(unique_users, 0) as events_per_user,
    
    -- Audit
    current_timestamp as dbt_updated_at

from daily_agg
order by event_date desc
```

#### Étape 4 : Exécution et tests (20 min)

```bash
# Compiler sans exécuter (vérifier le SQL)
dbt compile

# Exécuter tous les modèles
dbt run

# Exécuter uniquement staging
dbt run --select staging.*

# Exécuter un modèle et ses dépendances
dbt run --select +fact_daily_events

# Lancer les tests
dbt test

# Tests sur un modèle spécifique
dbt test --select stg_events
```

### 15:00 - 15:15 | ☕ Pause (15 min)

### 15:15 - 16:30 | TP4.2 : Orchestration dbt avec Prefect (1h15)

#### Flow Prefect pour dbt

```python
# flows/dbt_flow.py
"""
Orchestration dbt avec Prefect.
Exécute dbt run + dbt test avec gestion des erreurs.
"""
import subprocess
from pathlib import Path
from datetime import datetime

from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_training"


@task(retries=2, retry_delay_seconds=30)
def run_dbt_command(command: list[str], project_dir: Path) -> dict:
    """Exécute une commande dbt."""
    logger = get_run_logger()
    
    full_command = ["dbt"] + command + ["--project-dir", str(project_dir)]
    logger.info(f"Running: {' '.join(full_command)}")
    
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    
    # Log output
    if result.stdout:
        logger.info(result.stdout)
    if result.stderr:
        logger.warning(result.stderr)
    
    if result.returncode != 0:
        raise Exception(f"dbt command failed: {result.stderr}")
    
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
    }


@task
def dbt_deps(project_dir: Path) -> dict:
    """Installe les dépendances dbt."""
    return run_dbt_command(["deps"], project_dir)


@task
def dbt_run(project_dir: Path, select: str = None, full_refresh: bool = False) -> dict:
    """Exécute dbt run."""
    command = ["run"]
    if select:
        command.extend(["--select", select])
    if full_refresh:
        command.append("--full-refresh")
    return run_dbt_command(command, project_dir)


@task
def dbt_test(project_dir: Path, select: str = None) -> dict:
    """Exécute dbt test."""
    command = ["test"]
    if select:
        command.extend(["--select", select])
    return run_dbt_command(command, project_dir)


@task
def dbt_docs_generate(project_dir: Path) -> dict:
    """Génère la documentation dbt."""
    return run_dbt_command(["docs", "generate"], project_dir)


@flow(name="dbt-pipeline", log_prints=True)
def dbt_pipeline(
    project_dir: Path = DBT_PROJECT_DIR,
    select: str = None,
    run_tests: bool = True,
    generate_docs: bool = False,
    full_refresh: bool = False,
):
    """
    Pipeline dbt complet.
    
    Args:
        project_dir: Chemin vers le projet dbt
        select: Sélecteur dbt (ex: "staging.*", "+fact_events")
        run_tests: Exécuter les tests après run
        generate_docs: Générer la documentation
        full_refresh: Force full refresh des modèles incrémentiels
    """
    logger = get_run_logger()
    logger.info(f"Starting dbt pipeline at {datetime.now()}")
    
    # 1. Installer les dépendances
    dbt_deps(project_dir)
    
    # 2. Exécuter les modèles
    run_result = dbt_run(
        project_dir, 
        select=select, 
        full_refresh=full_refresh
    )
    
    # 3. Tests (optionnel)
    if run_tests:
        test_result = dbt_test(project_dir, select=select)
        logger.info(f"Tests completed: {test_result}")
    
    # 4. Documentation (optionnel)
    if generate_docs:
        dbt_docs_generate(project_dir)
        logger.info("Documentation generated")
    
    logger.info("dbt pipeline completed successfully")
    return {"status": "success", "run_result": run_result}


# Flow de déploiement avec schedule
@flow(name="daily-dbt-pipeline")
def daily_dbt_pipeline():
    """Pipeline quotidien avec configuration fixe."""
    return dbt_pipeline(
        run_tests=True,
        generate_docs=True,
    )


if __name__ == "__main__":
    # Test local
    dbt_pipeline(run_tests=True, generate_docs=True)
```

#### Alternative : Intégration Airflow

```python
# dags/dbt_dag.py
"""DAG Airflow pour dbt."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_PROJECT_DIR = "/opt/airflow/dbt_training"

default_args = {
    "owner": "data-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_daily",
    default_args=default_args,
    schedule_interval="0 7 * * *",  # Après ingestion (6h)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "transformation"],
) as dag:

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps",
    )

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --select staging.*",
    )

    dbt_test_staging = BashOperator(
        task_id="dbt_test_staging",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --select staging.*",
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --select marts.*",
    )

    dbt_test_marts = BashOperator(
        task_id="dbt_test_marts",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --select marts.*",
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt docs generate",
    )

    # Dependencies
    dbt_deps >> dbt_run_staging >> dbt_test_staging >> dbt_run_marts >> dbt_test_marts >> dbt_docs
```

### 16:30 - 17:00 | TP4.3 : Documentation dbt (30 min)

```bash
# Générer la documentation
cd dbt_training
dbt docs generate

# Servir localement
dbt docs serve --port 8001

# Ouvrir dans le navigateur
open http://localhost:8001
```

**Explorer la documentation** :
1. **Lineage Graph** : Visualisation des dépendances
2. **Model details** : Description, colonnes, tests
3. **Sources** : Connexion aux données brutes
4. **Exposures** : Utilisation par BI/dashboards

### 17:00 - 17:30 | Wrap-up Jour 4 (30 min)

#### Livrables attendus
- [ ] Projet dbt avec 2-3 modèles staging
- [ ] Projet dbt avec 1-2 modèles marts
- [ ] Tests dbt configurés
- [ ] Flow Prefect ou DAG Airflow pour dbt
- [ ] Documentation dbt générée

#### Récapitulatif
```
J4 : dbt & Prefect
├── ELT : Transformation dans le warehouse
├── dbt : Sources, Models, Tests, Macros
├── Architecture : Bronze → Silver → Gold
├── Prefect : Flows, Tasks, Retry, Cache
├── Orchestration : dbt via Prefect/Airflow
└── Documentation : Lineage, Column-level
```

#### Preview Jour 5
> Demain : Industrialisation complète - CI/CD, tests, projet fil rouge

---

## 📚 Ressources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Prefect Documentation](https://docs.prefect.io/)
- [DuckDB + dbt](https://docs.getdbt.com/docs/core/connect-data-platform/duckdb-setup)

## ⚠️ Points d'attention formateur

1. **DuckDB + Parquet** : Bien montrer la lecture directe
2. **profiles.yml** : Ne pas commiter (contient credentials)
3. **Prefect Cloud** : Optionnel, UI locale suffisante pour TP
4. **Tests dbt** : Insister sur leur importance en prod
