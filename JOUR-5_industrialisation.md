# Jour 5 — Productionisation, CI/CD & Projet Fil Rouge

> **Durée totale** : 7h  
> **Objectif** : Industrialiser le pipeline complet et le présenter lors d'une soutenance

---

## 🌅 MATIN (3h30)

### 08:30 - 08:45 | Réactivation Jour 4 (15 min)
- Retour sur dbt et Prefect
- Questions sur l'orchestration
- Introduction : "De la démo à la production"

### 08:45 - 10:15 | Bloc Théorique : "De la démo au pipeline exploitable" (1h30)

#### Partie 1 : Qu'est-ce qu'un pipeline "production-ready" ? (20 min)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Production Readiness Checklist                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✅ Versionné (Git)           ✅ Documenté                          │
│  ✅ Testé (unit + intégration) ✅ Observable (logs, metrics)        │
│  ✅ Reproductible (containers) ✅ Sécurisé (secrets, RBAC)          │
│  ✅ Scalable                   ✅ Résilient (retries, alertes)      │
│  ✅ Déployable (CI/CD)         ✅ Maintenable (code review)         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  La question clé :                                          │    │
│  │  "Si vous êtes absent, quelqu'un peut-il :                 │    │
│  │   - Comprendre le pipeline ?                               │    │
│  │   - Le debugger ?                                          │    │
│  │   - Le relancer après un échec ?"                          │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

#### Partie 2 : Structure du repository (25 min)

**Arborescence recommandée**
```
data-pipeline/
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # Tests + Lint
│       ├── cd-staging.yml      # Deploy staging
│       └── cd-prod.yml         # Deploy production
│
├── airflow/
│   ├── dags/
│   │   ├── pipeline_bronze.py
│   │   ├── pipeline_silver.py
│   │   └── dbt_dag.py
│   └── plugins/
│
├── dbt/
│   ├── models/
│   ├── macros/
│   ├── tests/
│   └── dbt_project.yml
│
├── n8n/
│   └── workflows/
│       └── backfill_trigger.json
│
├── prefect/
│   └── flows/
│       └── elt_flow.py
│
├── scripts/
│   ├── ingest_api.py
│   ├── validate_data.py
│   └── utils/
│       └── logging_config.py
│
├── tests/
│   ├── unit/
│   │   └── test_ingest.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── conftest.py
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── Dockerfile.airflow
│
├── docs/
│   ├── architecture.md
│   ├── runbook.md
│   └── adr/                    # Architecture Decision Records
│       └── 001-use-airflow.md
│
├── .env.example
├── .gitignore
├── pyproject.toml              # ou requirements.txt
├── Makefile                    # Commandes utiles
└── README.md
```

**Fichiers de configuration essentiels**

```toml
# pyproject.toml
[project]
name = "data-pipeline"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "apache-airflow>=2.8.0",
    "dbt-core>=1.7.0",
    "dbt-duckdb>=1.7.0",
    "prefect>=2.14.0",
    "pandas>=2.0.0",
    "pyarrow>=14.0.0",
    "requests>=2.31.0",
    "tenacity>=8.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=scripts --cov-report=term-missing"
```

```makefile
# Makefile
.PHONY: install lint test run-airflow run-dbt

install:
	pip install -e ".[dev]"

lint:
	ruff check scripts/ tests/
	ruff format --check scripts/ tests/

format:
	ruff format scripts/ tests/

test:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

run-airflow:
	docker-compose -f infra/docker-compose.yml up -d

stop-airflow:
	docker-compose -f infra/docker-compose.yml down

run-dbt:
	cd dbt && dbt run

test-dbt:
	cd dbt && dbt test

docs-dbt:
	cd dbt && dbt docs generate && dbt docs serve
```

#### Partie 3 : Tests et qualité (25 min)

**Pyramide des tests**
```
                    ┌─────────┐
                   /│ E2E     │\
                  / │ Tests   │ \     Moins nombreux
                 /  └─────────┘  \    Mais couvrent
                /                 \   plus de scope
               /   ┌───────────┐   \
              /    │Integration│    \
             /     │   Tests   │     \
            /      └───────────┘      \
           /                           \
          /      ┌─────────────┐        \
         /       │    Unit     │         \   Plus nombreux
        /        │   Tests     │          \  Rapides
       /         └─────────────┘           \ Ciblés
      ─────────────────────────────────────
```

**Tests unitaires Python**
```python
# tests/unit/test_ingest.py
import pytest
from scripts.ingest_api import fetch_page, normalize_response

class TestFetchPage:
    def test_successful_fetch(self, mocker):
        """Test une récupération réussie."""
        mock_response = mocker.Mock()
        mock_response.json.return_value = [{"id": 1}]
        mock_response.raise_for_status.return_value = None
        
        mocker.patch("requests.get", return_value=mock_response)
        
        result = fetch_page("http://api.test", page=1, page_size=10)
        
        assert result["data"] == [{"id": 1}]
        assert result["page"] == 1

    def test_retry_on_failure(self, mocker):
        """Test le retry après échec."""
        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            None,
        ]
        mock_response.json.return_value = [{"id": 1}]
        
        mocker.patch("requests.get", return_value=mock_response)
        
        result = fetch_page("http://api.test", page=1, page_size=10)
        assert result is not None


class TestNormalizeResponse:
    @pytest.mark.parametrize("input_data,expected", [
        ({"bitcoin_usd": 50000}, {"prices": [{"coin": "bitcoin", "usd": 50000}]}),
        ({}, {"prices": []}),
    ])
    def test_normalization(self, input_data, expected):
        """Test la normalisation avec différentes entrées."""
        result = normalize_response(input_data)
        assert result["prices"] == expected["prices"]
```

**Tests d'intégration**
```python
# tests/integration/test_pipeline.py
import subprocess
from pathlib import Path
import pandas as pd
import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data"

class TestIngestPipeline:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Prépare un répertoire temporaire."""
        self.output_dir = tmp_path / "bronze"
        self.output_dir.mkdir()
        yield
        # Cleanup automatique par pytest

    def test_full_ingestion(self):
        """Test le pipeline d'ingestion complet."""
        result = subprocess.run(
            [
                "python", "scripts/ingest_api.py",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-01",
                "--output-dir", str(self.output_dir),
            ],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        
        # Vérifier le fichier créé
        parquet_files = list(self.output_dir.rglob("*.parquet"))
        assert len(parquet_files) == 1
        
        # Vérifier le contenu
        df = pd.read_parquet(parquet_files[0])
        assert len(df) > 0
        assert "id" in df.columns
```

**Tests dbt**
```yaml
# dbt/models/staging/_staging.yml
version: 2

models:
  - name: stg_events
    columns:
      - name: event_id
        tests:
          - unique
          - not_null
      - name: user_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_users')
              field: user_id
      - name: event_title
        tests:
          - not_null
          - dbt_expectations.expect_column_value_lengths_to_be_between:
              min_value: 1
              max_value: 500
```

#### Partie 4 : CI/CD avec GitHub Actions (20 min)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -e ".[dev]"
      
      - name: Run Ruff
        run: ruff check scripts/ tests/
      
      - name: Run MyPy
        run: mypy scripts/ --ignore-missing-imports

  test-unit:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run unit tests
        run: pytest tests/unit -v --cov=scripts --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  test-dbt:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dbt
        run: pip install dbt-core dbt-duckdb
      
      - name: Run dbt compile
        run: |
          cd dbt
          dbt deps
          dbt compile --profiles-dir .
      
      - name: Run dbt tests
        run: |
          cd dbt
          dbt run --profiles-dir . --target ci
          dbt test --profiles-dir . --target ci

  build:
    runs-on: ubuntu-latest
    needs: [test-unit, test-dbt]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t data-pipeline:${{ github.sha }} -f infra/Dockerfile.airflow .
      
      - name: Push to registry
        run: |
          # Push vers votre registry (ECR, GCR, etc.)
          echo "Would push to registry here"
```

### 10:15 - 10:30 | ☕ Pause (15 min)

### 10:30 - 12:00 | Bloc pratique : Industrialisation (1h30)

#### Exercice 1 : Logging structuré (20 min)

```python
# scripts/utils/logging_config.py
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Formateur JSON pour logs structurés."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Ajouter les extras
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        
        # Exception si présente
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Configure le logging structuré."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Handler console
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    return logger


# Utilisation
# logger = setup_logging("ingest_api")
# logger.info("Starting ingestion", extra={"date": "2024-01-01", "source": "api"})
```

#### Exercice 2 : Configuration centralisée (20 min)

```python
# scripts/config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configuration centralisée via variables d'environnement."""
    
    # API
    api_base_url: str = Field(default="https://jsonplaceholder.typicode.com")
    api_timeout: int = Field(default=30)
    api_retries: int = Field(default=3)
    
    # Paths
    data_dir: Path = Field(default=Path("./data"))
    bronze_dir: Path = Field(default=Path("./data/bronze"))
    
    # Database
    db_connection_string: str = Field(default="duckdb:///data/warehouse.duckdb")
    
    # Alerting
    alert_email: str = Field(default="")
    slack_webhook: str = Field(default="")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
settings = Settings()
```

```bash
# .env.example
API_BASE_URL=https://jsonplaceholder.typicode.com
API_TIMEOUT=30
DATA_DIR=./data
DB_CONNECTION_STRING=duckdb:///data/warehouse.duckdb
ALERT_EMAIL=team@company.com
SLACK_WEBHOOK=https://hooks.slack.com/...
```

#### Exercice 3 : Runbook (30 min)

```markdown
# docs/runbook.md

# Runbook - Data Pipeline

## Vue d'ensemble

Ce document décrit les procédures opérationnelles pour le pipeline de données.

## Architecture

```
[n8n: Triggers/Backfill] 
        ↓
[Airflow: Orchestration quotidienne]
        ↓
[Scripts Python: Ingestion/Validation]
        ↓
[dbt: Transformations]
        ↓
[DuckDB: Warehouse]
```

## Procédures courantes

### Relancer un DAG en échec

1. Accéder à Airflow UI : http://localhost:8080
2. Naviguer vers le DAG en échec
3. Identifier la task en échec (rouge)
4. Vérifier les logs de la task
5. Corriger le problème si nécessaire
6. Click droit sur la task → "Clear" → Confirm

### Backfill historique

```bash
# Via CLI Airflow
airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  pipeline_bronze

# Via n8n (webhook)
curl -X POST http://localhost:5678/webhook/backfill \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-01-01", "end_date": "2024-01-31"}'
```

### Rafraîchir les modèles dbt

```bash
# Full refresh d'un modèle
dbt run --select stg_events --full-refresh

# Reconstruire tout
dbt run --full-refresh
dbt test
```

## Alertes et escalade

| Alerte | Sévérité | Action |
|--------|----------|--------|
| Ingestion échouée | Medium | Vérifier API source, relancer |
| Validation échouée | High | Investiguer données, quarantaine |
| dbt tests échoués | High | Vérifier qualité données |
| Pipeline > 2h | Medium | Vérifier performances |

## Contacts

- On-call Data : data-oncall@company.com
- Slack : #data-alerts
```

#### Exercice 4 : Configuration CI (20 min)

- Créer le fichier `.github/workflows/ci.yml` (voir section précédente)
- Commit et push
- Vérifier l'exécution sur GitHub

---

## 🍽️ PAUSE DÉJEUNER (12:00 - 13:30)

---

## 🌆 APRÈS-MIDI : PROJET FIL ROUGE & SOUTENANCES (3h30)

### 13:30 - 15:30 | Consolidation du projet (2h)

#### Checklist de consolidation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHECKLIST PROJET FIL ROUGE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📁 Structure repo                                                  │
│  [ ] Arborescence propre                                            │
│  [ ] .gitignore configuré                                           │
│  [ ] .env.example présent                                           │
│  [ ] README complet                                                 │
│                                                                      │
│  🔧 Scripts                                                         │
│  [ ] ingest_api.py fonctionnel                                     │
│  [ ] validate_data.py avec règles                                  │
│  [ ] Logs structurés                                               │
│  [ ] Configuration externalisée                                     │
│                                                                      │
│  📊 n8n                                                             │
│  [ ] Workflow d'ingestion exporté                                  │
│  [ ] Workflow backfill (optionnel)                                 │
│  [ ] Credentials configurés                                        │
│                                                                      │
│  🎯 Airflow                                                         │
│  [ ] DAG pipeline_bronze                                           │
│  [ ] Variables configurées                                         │
│  [ ] Retry/Error handling                                          │
│                                                                      │
│  🔄 dbt                                                             │
│  [ ] Au moins 2 modèles staging                                    │
│  [ ] Au moins 1 modèle mart                                        │
│  [ ] Tests configurés                                              │
│  [ ] Documentation générée                                         │
│                                                                      │
│  🐳 Infrastructure                                                  │
│  [ ] docker-compose fonctionnel                                    │
│  [ ] Instructions de démarrage                                     │
│                                                                      │
│  📝 Documentation                                                   │
│  [ ] README avec setup                                             │
│  [ ] Runbook basique                                               │
│  [ ] Architecture documentée                                        │
│                                                                      │
│  ✅ Tests                                                           │
│  [ ] Au moins 2 tests unitaires                                    │
│  [ ] Tests dbt passent                                             │
│                                                                      │
│  🚀 CI/CD (bonus)                                                   │
│  [ ] GitHub Actions configuré                                      │
│  [ ] Lint automatique                                              │
└─────────────────────────────────────────────────────────────────────┘
```

#### Travail en binôme

**Répartition des tâches suggérée** :

| Binôme membre 1 | Binôme membre 2 |
|-----------------|-----------------|
| Scripts Python + tests | DAGs Airflow |
| Projet dbt | Workflow n8n |
| Documentation | Infrastructure Docker |
| README | Runbook |

### 15:30 - 15:45 | ☕ Pause (15 min)

### 15:45 - 17:15 | Soutenances (1h30)

#### Format soutenance (par groupe)

**Durée : 15-20 minutes par groupe**

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Structure Soutenance                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📌 Introduction (2 min)                                            │
│     • Présentation du groupe                                        │
│     • Objectif du pipeline                                          │
│                                                                      │
│  🖥️ Démo live (8-10 min)                                           │
│     • Workflow n8n : trigger, exécution, logs                      │
│     • DAG Airflow : vue graphe, exécution, XCom                    │
│     • dbt : run, test, documentation                               │
│     • Données : montrer Bronze → Silver → Gold                     │
│                                                                      │
│  🏗️ Architecture (3 min)                                           │
│     • Schéma global                                                 │
│     • Choix techniques justifiés                                    │
│                                                                      │
│  ❓ Questions (5 min)                                               │
│     • Gestion des erreurs ?                                         │
│     • Comment backfiller ?                                          │
│     • Scalabilité ?                                                 │
│     • Améliorations futures ?                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Grille d'évaluation

| Critère | Points | Description |
|---------|--------|-------------|
| **Pipeline fonctionnel** | /30 | Les composants s'exécutent sans erreur |
| **Qualité du code** | /20 | Lisibilité, structure, bonnes pratiques |
| **Gestion des erreurs** | /15 | Retry, logging, alerting |
| **Documentation** | /15 | README, runbook, dbt docs |
| **Présentation** | /10 | Clarté, démo fluide |
| **Réponses aux questions** | /10 | Compréhension, pertinence |

### 17:15 - 17:30 | Clôture de la formation (15 min)

#### Récapitulatif des 5 jours

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Parcours de la semaine                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  J1: n8n & Fondations                                               │
│      └─► Automatisation low-code, triggers, premiers workflows     │
│                                                                      │
│  J2: Ingestion Incrémentale                                         │
│      └─► Patterns, scripts Python, validation, Parquet             │
│                                                                      │
│  J3: Orchestration Airflow                                          │
│      └─► DAGs, operators, scheduling, backfill                     │
│                                                                      │
│  J4: dbt & Prefect                                                  │
│      └─► Transformations SQL, ELT moderne, orchestration Python    │
│                                                                      │
│  J5: Industrialisation                                              │
│      └─► CI/CD, tests, documentation, projet complet               │
│                                                                      │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  Vous savez maintenant :                                            │
│  ✅ Construire un pipeline data de bout en bout                    │
│  ✅ Choisir les bons outils selon le contexte                      │
│  ✅ Écrire du code testable et maintenable                         │
│  ✅ Industrialiser avec CI/CD                                      │
│  ✅ Documenter pour la production                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Pour aller plus loin

| Sujet | Ressources |
|-------|------------|
| Airflow avancé | Astronomer Academy, Apache Airflow docs |
| dbt avancé | dbt Learn, Analytics Engineering with dbt |
| Data mesh | Zhamak Dehghani's book |
| DataOps | DataOps Cookbook |
| Streaming | Kafka, Flink, Spark Streaming |
| Orchestration moderne | Dagster, Mage, Kestra |

#### Feedback

- Distribuer formulaire d'évaluation
- Discussion ouverte : points forts, améliorations
- Échange de contacts LinkedIn/GitHub

---

## 📚 Ressources finales

### Livres recommandés
- "Fundamentals of Data Engineering" - Joe Reis & Matt Housley
- "The Data Warehouse Toolkit" - Ralph Kimball
- "Data Pipelines Pocket Reference" - James Densmore

### Certifications
- dbt Analytics Engineering Certification
- Astronomer Airflow Certification
- Google Cloud Professional Data Engineer

### Communautés
- dbt Slack Community
- Apache Airflow Slack
- Data Engineering subreddit

---

## ⚠️ Points d'attention formateur

1. **Timing soutenances** : Prévoir du buffer entre les groupes
2. **Problèmes techniques** : Avoir un backup démo enregistré
3. **Évaluation** : Rester bienveillant, valoriser les efforts
4. **Feedback** : Collecter à chaud, plus sincère
