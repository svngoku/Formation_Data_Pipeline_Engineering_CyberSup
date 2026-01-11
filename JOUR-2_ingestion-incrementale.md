# Jour 2 — n8n + Scripting pour l'ingestion data

> **Durée totale** : 7h  
> **Objectif** : Maîtriser les patterns d'ingestion incrémentale et structurer la logique métier dans des scripts versionnés

---

## 🌅 MATIN (3h30)

### 08:30 - 08:45 | Réactivation Jour 1 (15 min)
- Questions sur les TPs de la veille
- Retour sur les exercices optionnels
- Déblocage si nécessaire

### 08:45 - 10:15 | Bloc Théorique : "Automatiser l'ingestion incrémentale" (1h30)

#### Partie 1 : Patterns d'ingestion (40 min)

**Full Load vs Incremental**
```
┌────────────────────────────────────────────────────────────┐
│                      FULL LOAD                              │
├────────────────────────────────────────────────────────────┤
│  Source ════════════════════════════════════════► Target   │
│         (tout, à chaque run)                               │
│                                                             │
│  ✅ Simple                    ❌ Coûteux en ressources      │
│  ✅ Données toujours fraîches ❌ Lent sur gros volumes      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    INCREMENTAL LOAD                         │
├────────────────────────────────────────────────────────────┤
│  Source ──[Δ depuis last_run]──► Target                    │
│                                                             │
│  Stratégies de watermark:                                  │
│  ┌──────────────────┬────────────────────────────────┐    │
│  │ last_updated_at  │ Colonne timestamp modifiée     │    │
│  │ last_id          │ ID auto-incrémenté             │    │
│  │ cursor/token     │ Token de pagination API        │    │
│  │ hash/checksum    │ Détection de changement        │    │
│  └──────────────────┴────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

**Pagination API**
```python
# Offset/Limit (simple mais problématique si données changent)
GET /api/events?offset=0&limit=100
GET /api/events?offset=100&limit=100

# Cursor-based (recommandé)
GET /api/events?cursor=abc123&limit=100
# Response: { data: [...], next_cursor: "def456" }

# Keyset pagination (performant)
GET /api/events?after_id=1000&limit=100
```

**Gestion des erreurs : Pattern DLQ**
```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│ Source  │────►│  Ingestion  │────►│    Target    │
└─────────┘     └──────┬──────┘     └──────────────┘
                       │ échec
                       ▼
              ┌─────────────────┐
              │  Dead Letter    │  ← Quarantaine
              │     Queue       │  ← Retry manuel
              └─────────────────┘
```

#### Partie 2 : Architecture "n8n + Scripts" (30 min)

**Séparation des responsabilités**
```
┌────────────────────────────────────────────────────────────┐
│                    n8n (Orchestrateur)                      │
├────────────────────────────────────────────────────────────┤
│  • Scheduling (cron, webhooks)                             │
│  • Gestion du state (last_run, watermarks)                 │
│  • Routage et branchements                                 │
│  • Notifications (succès/échec)                            │
│  • Interface visuelle pour ops                             │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                Scripts Python/Bash (Logique)                │
├────────────────────────────────────────────────────────────┤
│  • Appels API avec retry/backoff                           │
│  • Transformation des données                              │
│  • Validation et qualité                                   │
│  • Écriture fichiers (Parquet, CSV)                        │
│  • Logs structurés                                         │
└────────────────────────────────────────────────────────────┘
```

**Avantages scripts versionnés**
| Critère | Script dans n8n | Script Git |
|---------|-----------------|------------|
| Versioning | ❌ | ✅ Git history |
| Tests | ❌ | ✅ pytest/unittest |
| Code review | ❌ | ✅ PR/MR |
| Réutilisation | ❌ | ✅ Import modules |
| IDE support | ❌ | ✅ Autocomplete, lint |

#### Partie 3 : Formats de données (20 min)

**Comparaison formats**
```
┌─────────┬────────────┬────────────┬───────────────┬──────────────┐
│ Format  │ Lisibilité │ Compression│ Schema        │ Use case     │
├─────────┼────────────┼────────────┼───────────────┼──────────────┤
│ JSON    │ ✅ Haute   │ ❌ Aucune  │ ❌ Flexible   │ APIs, debug  │
│ CSV     │ ✅ Haute   │ ❌ Faible  │ ❌ Implicite  │ Export, Excel│
│ Parquet │ ❌ Binaire │ ✅ Forte   │ ✅ Embarqué   │ Analytics    │
│ Avro    │ ❌ Binaire │ ✅ Moyenne │ ✅ Évolutif   │ Streaming    │
└─────────┴────────────┴────────────┴───────────────┴──────────────┘
```

**Pourquoi Parquet pour Bronze/Silver ?**
```python
# Exemple : même dataset
import pandas as pd

df = pd.read_json("events.json")  # 100 MB
df.to_csv("events.csv")            # 120 MB
df.to_parquet("events.parquet")    # 15 MB  ← 8x plus petit!

# Lecture sélective (column pruning)
pd.read_parquet("events.parquet", columns=["id", "timestamp"])
```

### 10:15 - 10:30 | ☕ Pause (15 min)

### 10:30 - 11:30 | Option : Présentation Node-RED (1h)

> **Note** : Section optionnelle, peut être remplacée par plus de pratique n8n

#### Comparaison rapide n8n vs Node-RED

| Aspect | n8n | Node-RED |
|--------|-----|----------|
| Focus | Automation, integrations | IoT, message flows |
| Interface | Modern, UX soignée | Fonctionnelle |
| Nodes natifs | ~300 (SaaS focus) | ~5000 (hardware focus) |
| Déploiement | Docker, Cloud | Edge, Raspberry Pi |
| Communauté | Startup | IBM, industrie |
| Licence | Fair-code | Apache 2.0 |

#### Démo rapide (30 min)
```bash
docker run -it -p 1880:1880 nodered/node-red
```

**Workflow exemple** :
```
[inject] → [http request] → [json] → [function] → [debug]
```

#### Discussion : Quand choisir Node-RED ? (30 min)
- IoT et edge computing
- Protocoles industriels (MQTT, Modbus)
- Raspberry Pi / embarqué
- Flows temps réel

### 11:30 - 12:00 | Checkpoint matin (30 min)

**Exercice pratique** : Concevoir sur papier
> "Vous devez ingérer des transactions bancaires depuis une API paginée. 
> Dessinez le flow et identifiez : watermark, gestion d'erreur, format de sortie."

**Discussion collective** des solutions proposées.

---

## 🍽️ PAUSE DÉJEUNER (12:00 - 13:30)

---

## 🌆 APRÈS-MIDI (3h30)

### 13:30 - 15:30 | TP2.1 : Ingestion API → Parquet (2h)

#### Contexte
> Ingérer des événements depuis une API paginée (simulation avec JSONPlaceholder ou API publique)

#### Script `ingest_api.py` - Construction guidée

**Étape 1 : Structure de base (20 min)**
```python
#!/usr/bin/env python3
"""
Ingestion incrémentale depuis une API paginée.
Usage: python ingest_api.py --start-date 2024-01-01 --end-date 2024-01-31
"""
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration logging JSON
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest data from API")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="./data/bronze", help="Output directory")
    parser.add_argument("--page-size", type=int, default=100, help="Items per page")
    return parser.parse_args()
```

**Étape 2 : Appels API avec retry (25 min)**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_page(base_url: str, page: int, page_size: int) -> dict:
    """Fetch une page avec retry exponentiel."""
    url = f"{base_url}?_page={page}&_limit={page_size}"
    logger.info(f"Fetching {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    return {
        "data": response.json(),
        "page": page,
        "has_more": len(response.json()) == page_size
    }


def fetch_all_pages(base_url: str, page_size: int = 100) -> list:
    """Récupère toutes les pages."""
    all_data = []
    page = 1
    
    while True:
        result = fetch_page(base_url, page, page_size)
        all_data.extend(result["data"])
        
        if not result["has_more"]:
            break
        page += 1
    
    logger.info(f"Fetched {len(all_data)} records in {page} pages")
    return all_data
```

**Étape 3 : Écriture Parquet partitionné (25 min)**
```python
def write_parquet(data: list, output_dir: str, partition_date: str):
    """Écrit les données en Parquet partitionné par date."""
    if not data:
        logger.warning("No data to write")
        return
    
    df = pd.DataFrame(data)
    
    # Ajouter métadonnées
    df["_ingested_at"] = datetime.utcnow().isoformat()
    df["_source"] = "api"
    df["_partition_date"] = partition_date
    
    # Créer répertoire partitionné
    output_path = Path(output_dir) / f"partition_date={partition_date}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Écrire avec timestamp pour idempotence
    filename = f"data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet"
    filepath = output_path / filename
    
    df.to_parquet(filepath, index=False, compression="snappy")
    logger.info(f"Written {len(df)} records to {filepath}")
    
    return str(filepath)
```

**Étape 4 : Main et orchestration (20 min)**
```python
def main():
    args = parse_args()
    
    logger.info(f"Starting ingestion: {args.start_date} to {args.end_date}")
    
    # API exemple (JSONPlaceholder)
    base_url = "https://jsonplaceholder.typicode.com/posts"
    
    try:
        data = fetch_all_pages(base_url, args.page_size)
        output_file = write_parquet(data, args.output_dir, args.start_date)
        
        # Sortie JSON pour n8n
        result = {
            "status": "success",
            "records_count": len(data),
            "output_file": output_file,
            "ingestion_date": datetime.utcnow().isoformat()
        }
        print(json.dumps(result))
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        result = {"status": "error", "error": str(e)}
        print(json.dumps(result))
        raise


if __name__ == "__main__":
    main()
```

**Étape 5 : Intégration n8n (30 min)**

Workflow n8n :
```
[Schedule Trigger] → [Set Variables] → [Execute Command] → [Parse JSON] → [IF Success] → [Log/Notify]
                                                                              ↓ Error
                                                                         [Error Notify]
```

Configuration Execute Command :
```bash
python3 /scripts/ingest_api.py \
  --start-date {{ $json.start_date }} \
  --end-date {{ $json.end_date }} \
  --output-dir /data/bronze
```

### 15:30 - 15:45 | ☕ Pause (15 min)

### 15:45 - 16:45 | TP2.2 : Contrôle qualité (1h)

#### Script `validate_data.py`

```python
#!/usr/bin/env python3
"""
Validation des données ingérées.
Exit code 0 = OK, 1 = Erreurs trouvées
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Parquet file to validate")
    parser.add_argument("--rules-file", help="JSON file with validation rules")
    return parser.parse_args()


def validate(df: pd.DataFrame, rules: dict) -> list:
    """Applique les règles de validation."""
    errors = []
    
    # Règle 1 : Colonnes requises
    required_cols = rules.get("required_columns", [])
    missing = set(required_cols) - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {missing}")
    
    # Règle 2 : Pas de nulls sur certaines colonnes
    not_null_cols = rules.get("not_null_columns", [])
    for col in not_null_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} null values")
    
    # Règle 3 : Valeurs dans un range
    ranges = rules.get("value_ranges", {})
    for col, (min_val, max_val) in ranges.items():
        if col in df.columns:
            out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
            if len(out_of_range) > 0:
                errors.append(f"Column '{col}' has {len(out_of_range)} values out of range [{min_val}, {max_val}]")
    
    # Règle 4 : Unicité
    unique_cols = rules.get("unique_columns", [])
    for col in unique_cols:
        if col in df.columns:
            duplicates = df[col].duplicated().sum()
            if duplicates > 0:
                errors.append(f"Column '{col}' has {duplicates} duplicate values")
    
    # Règle 5 : Minimum de lignes
    min_rows = rules.get("min_rows", 0)
    if len(df) < min_rows:
        errors.append(f"Expected at least {min_rows} rows, got {len(df)}")
    
    return errors


def main():
    args = parse_args()
    
    # Règles par défaut
    default_rules = {
        "required_columns": ["id", "_ingested_at"],
        "not_null_columns": ["id"],
        "unique_columns": ["id"],
        "min_rows": 1
    }
    
    # Charger règles custom si fournies
    if args.rules_file:
        with open(args.rules_file) as f:
            rules = json.load(f)
    else:
        rules = default_rules
    
    # Lire et valider
    df = pd.read_parquet(args.input_file)
    errors = validate(df, rules)
    
    # Résultat
    result = {
        "file": args.input_file,
        "rows": len(df),
        "columns": list(df.columns),
        "validation": "passed" if not errors else "failed",
        "errors": errors
    }
    
    print(json.dumps(result, indent=2))
    
    if errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

#### Fichier de règles `validation_rules.json`
```json
{
  "required_columns": ["id", "title", "body", "_ingested_at"],
  "not_null_columns": ["id", "title"],
  "unique_columns": ["id"],
  "value_ranges": {
    "userId": [1, 100]
  },
  "min_rows": 10
}
```

#### Intégration dans n8n
- Ajouter après ingestion
- Brancher vers notification si échec

### 16:45 - 17:15 | TP2.3 : Backfill (30 min)

#### Ajout mode backfill au workflow n8n

**Concept** :
```
┌─────────────────────────────────────────────────────────────┐
│                      Mode Backfill                           │
├─────────────────────────────────────────────────────────────┤
│  Paramètres:                                                 │
│    - start_date: 2024-01-01                                 │
│    - end_date: 2024-03-31                                   │
│    - mode: backfill                                         │
│                                                              │
│  Logique:                                                    │
│    Pour chaque jour dans [start_date, end_date]:            │
│      - Vérifier si partition existe déjà                    │
│      - Si non, ingérer                                      │
│      - Si oui, skip (idempotence)                          │
└─────────────────────────────────────────────────────────────┘
```

**Script helper `generate_dates.py`** :
```python
#!/usr/bin/env python3
"""Génère la liste des dates pour backfill."""
import argparse
import json
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()
    
    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    print(json.dumps({"dates": dates}))

if __name__ == "__main__":
    main()
```

**Workflow n8n backfill** :
```
[Manual Trigger] → [Set Params] → [Execute: generate_dates.py] → [Split In Batches] → [Execute: ingest_api.py] → [Validate]
```

### 17:15 - 17:30 | Wrap-up Jour 2 (15 min)

#### Livrables attendus
- [ ] Script `ingest_api.py` fonctionnel
- [ ] Script `validate_data.py` avec règles
- [ ] Workflow n8n ingestion incrémentale
- [ ] Données bronze en Parquet
- [ ] Documentation dans README

#### Récapitulatif
```
J2 : Ingestion Incrémentale
├── Patterns : Full vs Incrémental, Watermarks
├── Architecture : n8n orchestrateur, Scripts logique
├── Formats : JSON → Parquet (compression, schema)
├── Scripts : ingest_api.py, validate_data.py
├── Qualité : Validation, DLQ, Alerting
└── Ops : Backfill, Idempotence
```

#### Preview Jour 3
> Demain : Airflow ! DAGs, Operators, scheduling production-grade

---

## 📚 Ressources

- [Tenacity (retry library)](https://tenacity.readthedocs.io/)
- [Pandas Parquet](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html)
- [JSONPlaceholder API](https://jsonplaceholder.typicode.com/)

## ⚠️ Points d'attention formateur

1. **pyarrow** : S'assurer qu'il est installé (`pip install pyarrow`)
2. **Permissions Docker** : Scripts doivent être exécutables
3. **Partitionnement** : Expliquer le pattern Hive `partition_date=YYYY-MM-DD`
4. **Logs JSON** : Montrer comment les parser (jq, etc.)
