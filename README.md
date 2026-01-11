# 🚀 Formation Data Pipeline - Starter Kit

> Pipeline de données de bout en bout avec n8n, Airflow, dbt et Prefect

[![CI](https://github.com/your-org/data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/data-pipeline/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![dbt](https://img.shields.io/badge/dbt-1.7+-orange.svg)](https://www.getdbt.com/)

## 📋 Prérequis

- **Docker** et **Docker Compose** (v2+)
- **Python 3.11+**
- **Git**
- **8 GB RAM** minimum (Airflow est gourmand)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Architecture Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐     ┌─────────────┐     ┌─────────┐     ┌──────────┐  │
│  │   API   │────►│   n8n       │────►│ Airflow │────►│   dbt    │  │
│  │ Source  │     │ (triggers)  │     │ (orch)  │     │ (transf) │  │
│  └─────────┘     └─────────────┘     └────┬────┘     └────┬─────┘  │
│                                           │                │        │
│                         ┌─────────────────┴────────────────┘        │
│                         ▼                                            │
│                  ┌─────────────┐                                     │
│                  │   DuckDB    │                                     │
│                  │  Warehouse  │                                     │
│                  └─────────────┘                                     │
│                                                                       │
│  Data Flow:                                                          │
│  [Bronze: raw Parquet] → [Silver: cleaned] → [Gold: aggregated]    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Cloner et configurer

```bash
git clone https://github.com/your-org/data-pipeline.git
cd data-pipeline

# Copier la configuration
cp .env.example .env

# Installer les dépendances Python
pip install -e ".[dev]"
```

### 2. Lancer l'infrastructure

```bash
# Démarrer tous les services
docker-compose -f infra/docker-compose.yml up -d

# Vérifier les services
docker-compose -f infra/docker-compose.yml ps
```

### 3. Accéder aux interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **n8n** | http://localhost:5678 | (créer au premier accès) |
| **Airflow** | http://localhost:8080 | admin / admin |
| **dbt Docs** | http://localhost:8001 | - |

### 4. Premier test

```bash
# Exécuter le script d'ingestion
python scripts/ingest_api.py --start-date 2024-01-01 --end-date 2024-01-01

# Valider les données
python scripts/validate_data.py --input-file data/bronze/partition_date=2024-01-01/*.parquet

# Lancer dbt
cd dbt && dbt run && dbt test
```

## 📁 Structure du projet

```
data-pipeline/
├── 📂 airflow/
│   └── dags/                # DAGs Airflow
├── 📂 dbt/                  # Projet dbt
│   ├── models/
│   │   ├── staging/         # Silver layer
│   │   └── marts/           # Gold layer
│   └── dbt_project.yml
├── 📂 docs/                 # Documentation détaillée
│   ├── JOUR-1_*.md
│   ├── JOUR-2_*.md
│   ├── ...
│   └── runbook.md
├── 📂 infra/                # Docker & infra
├── 📂 n8n/                  # Workflows n8n
├── 📂 prefect/              # Flows Prefect
├── 📂 scripts/              # Scripts Python
├── 📂 tests/                # Tests unitaires/intégration
├── .env.example
├── Makefile
├── pyproject.toml
└── README.md                # Ce fichier
```

## 🛠️ Commandes utiles

```bash
# --- Infrastructure ---
make run-airflow          # Démarrer Airflow
make stop-airflow         # Arrêter Airflow

# --- Développement ---
make lint                 # Vérifier le code
make format               # Formater le code
make test                 # Tests unitaires
make test-integration     # Tests d'intégration

# --- dbt ---
make run-dbt              # Exécuter les modèles
make test-dbt             # Lancer les tests dbt
make docs-dbt             # Générer et servir la doc
```

## 📅 Programme de la formation

| Jour | Thème | Contenu |
|------|-------|---------|
| **J1** | n8n & Fondations | Automatisation low-code, triggers, workflows |
| **J2** | Ingestion | Patterns incrémentaux, scripts Python, Parquet |
| **J3** | Airflow | DAGs, operators, scheduling, backfill |
| **J4** | dbt & Prefect | Transformations SQL, ELT, orchestration Python |
| **J5** | Production | CI/CD, tests, documentation, projet final |

## 🔧 Configuration

### Variables d'environnement (.env)

```bash
# API
API_BASE_URL=https://jsonplaceholder.typicode.com
API_TIMEOUT=30

# Paths
DATA_DIR=./data
DBT_DATABASE_PATH=./data/warehouse.duckdb

# Alerting (optionnel)
SLACK_WEBHOOK=
ALERT_EMAIL=
```

### Profil dbt (~/.dbt/profiles.yml)

```yaml
dbt_training:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "data/warehouse.duckdb"
      threads: 4
```

## 📊 Livrables attendus

À la fin de la formation, votre repo doit contenir :

- [ ] Scripts d'ingestion et validation fonctionnels
- [ ] Workflow n8n exporté
- [ ] DAG Airflow opérationnel
- [ ] Projet dbt avec tests
- [ ] Documentation complète
- [ ] CI/CD configuré (bonus)

## 🆘 Troubleshooting

### Airflow ne démarre pas
```bash
# Vérifier les logs
docker-compose -f infra/docker-compose.yml logs airflow-scheduler

# Réinitialiser la base
docker-compose -f infra/docker-compose.yml down -v
docker-compose -f infra/docker-compose.yml up -d
```

### dbt ne trouve pas les sources
```bash
# Vérifier le chemin dans sources.yml
# S'assurer que les fichiers Parquet existent
ls -la data/bronze/
```

### n8n "Execute Command" échoue
```bash
# Vérifier que le script est exécutable
docker exec n8n chmod +x /home/node/scripts/*.py

# Tester manuellement
docker exec n8n python3 /home/node/scripts/ingest_api.py --help
```

## 📚 Ressources

- [Documentation n8n](https://docs.n8n.io/)
- [Apache Airflow](https://airflow.apache.org/docs/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Prefect Documentation](https://docs.prefect.io/)
- [DuckDB](https://duckdb.org/docs/)

## 👥 Contributeurs

Formation créée par [Votre Nom] - [votre-email@example.com]

## 📄 License

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.
