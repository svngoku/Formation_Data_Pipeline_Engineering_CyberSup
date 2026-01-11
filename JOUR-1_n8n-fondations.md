# Jour 1 — n8n & Fondations de l'Automatisation

> **Durée totale** : 7h  
> **Objectif** : Comprendre l'automatisation low-code et créer des workflows n8n connectés à des scripts

---

## 🌅 MATIN (3h30)

### 08:30 - 08:45 | Accueil & Ice-breaker (15 min)
- Tour de table rapide : prénom, background, attentes
- Présentation du programme de la semaine
- Vérification des prérequis techniques (Docker, Python, IDE)

### 08:45 - 10:15 | Bloc Théorique : "Automatiser sans coder (ou presque)" (1h30)

#### Partie 1 : Concepts fondamentaux (30 min)
| Concept | Explication | Exemple concret |
|---------|-------------|-----------------|
| Événement | Déclencheur d'une action | Nouveau fichier dans S3 |
| Trigger | Mécanisme de détection | Cron, Webhook, Event |
| Job | Unité de travail | Script d'ingestion |
| Pipeline | Enchaînement de jobs | Extract → Transform → Load |

**Points clés à couvrir** :
- Idempotence : "Rejouer sans dupliquer"
- Retries : stratégies exponential backoff
- Timeouts : éviter les jobs zombies

#### Partie 2 : Présentation de n8n (40 min)
```
┌─────────────────────────────────────────────────┐
│                  Architecture n8n                │
├─────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────────┐   │
│  │ Editor  │◄──│ Server  │──►│  Database   │   │
│  │  (Vue)  │   │ (Node)  │   │ (SQLite/PG) │   │
│  └─────────┘   └────┬────┘   └─────────────┘   │
│                     │                           │
│              ┌──────▼──────┐                   │
│              │   Workers   │                   │
│              │  (Node.js)  │                   │
│              └─────────────┘                   │
└─────────────────────────────────────────────────┘
```

**Concepts n8n** :
- Workflow = DAG visuel
- Node = étape (HTTP, Code, IF, etc.)
- Credentials = secrets centralisés
- Executions = historique des runs

#### Partie 3 : Sécurité & bonnes pratiques (20 min)
- ⚠️ **Execute Command** : surface d'attaque, isolation Docker
- 🔐 Gestion des credentials (jamais en clair dans les workflows)
- 🛡️ Principe de moindre privilège

**Slide récapitulative** :
```
┌────────────────────────────────────────────┐
│     Quand utiliser n8n vs Airflow ?        │
├────────────────────────────────────────────┤
│ n8n                  │ Airflow             │
├──────────────────────┼─────────────────────┤
│ Intégrations rapides │ Pipelines data      │
│ Webhooks/APIs        │ Scheduling complexe │
│ Alerting             │ Backfill massif     │
│ Prototypage          │ Production robuste  │
└──────────────────────┴─────────────────────┘
```

### 10:15 - 10:30 | ☕ Pause (15 min)

### 10:30 - 12:00 | Démonstration guidée (1h30)

#### Setup n8n (20 min)
```bash
# Lancer n8n en local
docker-compose up -d n8n

# Vérifier l'accès
open http://localhost:5678
```

#### Premier workflow live-coding (40 min)
**Workflow : "Météo → Email"**

1. **Trigger Cron** : toutes les heures
2. **HTTP Request** : API OpenWeatherMap
3. **Function** : extraire température + conditions
4. **IF** : température < 5°C ?
5. **Email** (simulé) : alerte froid

**Points pédagogiques** :
- Visualisation des données entre nœuds (panneau droit)
- Mode debug pas-à-pas
- Historique des exécutions

#### Exploration interface (30 min)
- Templates marketplace
- Import/Export JSON
- Variables d'environnement
- Logs et troubleshooting

### 12:00 - 12:15 | Checkpoint matin (15 min)
**Quiz rapide** (Mentimeter ou main levée) :
1. Différence trigger cron vs webhook ?
2. Où stocker un API key dans n8n ?
3. Pourquoi éviter Execute Command en prod ?

---

## 🍽️ PAUSE DÉJEUNER (12:15 - 13:30)

---

## 🌆 APRÈS-MIDI (3h30)

### 13:30 - 13:45 | Réactivation (15 min)
- Questions du matin
- Présentation des TPs de l'après-midi

### 13:45 - 15:15 | TP1.1 : Workflow d'ingestion simple (1h30)

#### Contexte
> Récupérer toutes les heures les prix des cryptomonnaies (CoinGecko API gratuite)

#### Étapes guidées

**Étape 1 : Créer le workflow (15 min)**
```
[Cron: 0 * * * *] → [HTTP Request] → [Function] → [Write File]
```

**Étape 2 : Configuration HTTP Request (20 min)**
```
URL: https://api.coingecko.com/api/v3/simple/price
Parameters:
  - ids: bitcoin,ethereum
  - vs_currencies: usd,eur
```

**Étape 3 : Transformation (25 min)**
```javascript
// Nœud Function
const timestamp = new Date().toISOString();
const data = items[0].json;

return [{
  json: {
    timestamp,
    bitcoin_usd: data.bitcoin.usd,
    ethereum_usd: data.ethereum.usd,
    bitcoin_eur: data.bitcoin.eur,
    ethereum_eur: data.ethereum.eur
  }
}];
```

**Étape 4 : Écriture fichier (15 min)**
- Nœud "Write Binary File" ou "Execute Command" avec append

**Étape 5 : Error Handling (15 min)**
- Ajouter un nœud "Error Trigger"
- Brancher vers notification (log ou webhook)

#### Checkpoint TP1.1
- [ ] Workflow exécutable manuellement
- [ ] Données écrites dans un fichier JSON/CSV
- [ ] Gestion d'erreur basique

### 15:15 - 15:30 | ☕ Pause (15 min)

### 15:30 - 17:00 | TP1.2 : n8n + Scripts externes (1h30)

#### Contexte
> Appeler un script Python de normalisation depuis n8n

#### Script fourni : `normalize_data.py`
```python
#!/usr/bin/env python3
"""
Normalise les données crypto en entrée.
Usage: cat data.json | python normalize_data.py
"""
import sys
import json
from datetime import datetime

def normalize(data: dict) -> dict:
    """Ajoute des champs calculés et normalise."""
    return {
        "ingested_at": datetime.utcnow().isoformat(),
        "source": "coingecko",
        "prices": [
            {"coin": "bitcoin", "usd": data.get("bitcoin_usd"), "eur": data.get("bitcoin_eur")},
            {"coin": "ethereum", "usd": data.get("ethereum_usd"), "eur": data.get("ethereum_eur")}
        ],
        "metadata": {
            "original_timestamp": data.get("timestamp"),
            "schema_version": "1.0"
        }
    }

if __name__ == "__main__":
    input_data = json.load(sys.stdin)
    output = normalize(input_data)
    print(json.dumps(output, indent=2))
```

#### Étapes

**Étape 1 : Préparer l'environnement (15 min)**
```bash
# Copier le script dans le volume n8n
docker cp scripts/normalize_data.py n8n:/home/node/scripts/
docker exec n8n chmod +x /home/node/scripts/normalize_data.py
```

**Étape 2 : Modifier le workflow (30 min)**
```
[...précédent...] → [Execute Command] → [Parse JSON] → [Write File]
```

Configuration Execute Command :
```bash
echo '{{ JSON.stringify($json) }}' | python3 /home/node/scripts/normalize_data.py
```

**Étape 3 : Parser la sortie (20 min)**
- Nœud "JSON Parse" ou "Function" pour structurer
- Validation du schéma de sortie

**Étape 4 : Discussion architecture (25 min)**

| Approche | Avantages | Inconvénients |
|----------|-----------|---------------|
| Script dans n8n | Rapide, visuel | Non versionné, difficile à tester |
| Script Git + Execute Command | Versionné, testable | Déploiement manuel, sécurité |
| Script en microservice | Isolé, scalable | Complexité infra |

**Recommandation** : Scripts dans Git, appelés via Execute Command pour le prototypage, puis migrer vers Airflow/Prefect en production.

### 17:00 - 17:30 | Wrap-up Jour 1 (30 min)

#### Récapitulatif
```
┌─────────────────────────────────────────────────────┐
│                    Ce qu'on a appris                │
├─────────────────────────────────────────────────────┤
│ ✅ Concepts d'automatisation (triggers, jobs)       │
│ ✅ Architecture et interface n8n                    │
│ ✅ Premier workflow d'ingestion                     │
│ ✅ Intégration scripts Python                       │
│ ✅ Bonnes pratiques sécurité                        │
└─────────────────────────────────────────────────────┘
```

#### Livrables attendus
- [ ] 1 workflow n8n exporté (`workflow_crypto.json`)
- [ ] 1 script Python (`normalize_data.py`)
- [ ] 1 README expliquant le flux

#### Preview Jour 2
> Demain : Ingestion incrémentale, patterns avancés, validation des données

#### Exercice optionnel (soir)
- Ajouter une 3ème crypto au workflow
- Implémenter un filtre "alerte si variation > 5%"

---

## 📚 Ressources

- [Documentation n8n](https://docs.n8n.io/)
- [Templates n8n](https://n8n.io/workflows/)
- [API CoinGecko](https://www.coingecko.com/en/api/documentation)

## ⚠️ Points d'attention formateur

1. **Timing serré** : Adapter selon le niveau du groupe
2. **Docker issues** : Avoir un plan B (instance cloud n8n)
3. **API rate limits** : CoinGecko limite à 10-50 req/min
4. **Execute Command** : Insister sur les risques en prod
