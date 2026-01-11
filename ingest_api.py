#!/usr/bin/env python3
"""
Ingestion incrémentale depuis une API paginée.

Ce script récupère des données depuis une API, les transforme,
et les écrit en format Parquet partitionné par date.

Usage:
    python ingest_api.py --start-date 2024-01-01 --end-date 2024-01-31
    python ingest_api.py --start-date 2024-01-01 --end-date 2024-01-01 --output-dir ./data/bronze
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# =============================================================================
# Configuration du logging
# =============================================================================


class JsonFormatter(logging.Formatter):
    """Formateur JSON pour logs structurés."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure le logging."""
    logger = logging.getLogger("ingest_api")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    return logger


logger = setup_logging()

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_API_URL = "https://jsonplaceholder.typicode.com/posts"
DEFAULT_OUTPUT_DIR = "./data/bronze"
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 3


# =============================================================================
# Fonctions d'ingestion
# =============================================================================


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
)
def fetch_page(
    base_url: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Récupère une page de données depuis l'API avec retry exponentiel.

    Args:
        base_url: URL de base de l'API
        page: Numéro de page (1-indexed)
        page_size: Nombre d'éléments par page
        timeout: Timeout en secondes

    Returns:
        Dict avec 'data', 'page', 'has_more'

    Raises:
        requests.RequestException: En cas d'erreur après tous les retries
    """
    url = f"{base_url}?_page={page}&_limit={page_size}"
    logger.info(f"Fetching page {page}", extra={"url": url})

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    data = response.json()

    return {
        "data": data,
        "page": page,
        "has_more": len(data) == page_size,
    }


def fetch_all_pages(
    base_url: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """
    Récupère toutes les pages de données.

    Args:
        base_url: URL de base de l'API
        page_size: Nombre d'éléments par page
        max_pages: Limite optionnelle du nombre de pages

    Returns:
        Liste de tous les enregistrements
    """
    all_data = []
    page = 1

    while True:
        result = fetch_page(base_url, page, page_size)
        all_data.extend(result["data"])

        logger.info(
            f"Fetched page {page}",
            extra={"records": len(result["data"]), "total": len(all_data)},
        )

        if not result["has_more"]:
            break

        if max_pages and page >= max_pages:
            logger.warning(f"Reached max_pages limit: {max_pages}")
            break

        page += 1

    logger.info(f"Fetched {len(all_data)} records in {page} pages")
    return all_data


def transform_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transforme les données brutes.

    Ajoute des métadonnées et normalise le schéma.

    Args:
        data: Liste des enregistrements bruts

    Returns:
        Liste des enregistrements transformés
    """
    ingested_at = datetime.utcnow().isoformat()

    transformed = []
    for record in data:
        transformed.append(
            {
                # Champs originaux
                "id": record.get("id"),
                "userId": record.get("userId"),
                "title": record.get("title"),
                "body": record.get("body"),
                # Métadonnées
                "_ingested_at": ingested_at,
                "_source": "jsonplaceholder",
                "_schema_version": "1.0",
            }
        )

    return transformed


def write_parquet(
    data: list[dict[str, Any]],
    output_dir: str,
    partition_date: str,
) -> str | None:
    """
    Écrit les données en Parquet partitionné par date.

    Args:
        data: Liste des enregistrements à écrire
        output_dir: Répertoire de sortie
        partition_date: Date de partition (YYYY-MM-DD)

    Returns:
        Chemin du fichier créé, ou None si pas de données
    """
    if not data:
        logger.warning("No data to write")
        return None

    df = pd.DataFrame(data)

    # Ajouter la colonne de partition
    df["_partition_date"] = partition_date

    # Créer le répertoire partitionné (style Hive)
    output_path = Path(output_dir) / f"partition_date={partition_date}"
    output_path.mkdir(parents=True, exist_ok=True)

    # Nom de fichier avec timestamp pour idempotence
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"data_{timestamp}.parquet"
    filepath = output_path / filename

    # Écrire le Parquet avec compression
    df.to_parquet(filepath, index=False, compression="snappy")

    logger.info(
        f"Written {len(df)} records",
        extra={"filepath": str(filepath), "size_mb": filepath.stat().st_size / 1024 / 1024},
    )

    return str(filepath)


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="Ingestion incrémentale depuis une API paginée",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ingest_api.py --start-date 2024-01-01 --end-date 2024-01-01
  python ingest_api.py --start-date 2024-01-01 --end-date 2024-01-31 --output-dir ./bronze
        """,
    )

    parser.add_argument(
        "--start-date",
        required=True,
        help="Date de début (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="Date de fin (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Répertoire de sortie (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"URL de l'API (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Éléments par page (default: {DEFAULT_PAGE_SIZE})",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limite du nombre de pages (optionnel)",
    )

    return parser.parse_args()


def main() -> None:
    """Point d'entrée principal."""
    args = parse_args()

    logger.info(
        "Starting ingestion",
        extra={
            "start_date": args.start_date,
            "end_date": args.end_date,
            "output_dir": args.output_dir,
        },
    )

    try:
        # 1. Récupérer les données
        raw_data = fetch_all_pages(
            args.api_url,
            page_size=args.page_size,
            max_pages=args.max_pages,
        )

        # 2. Transformer
        transformed_data = transform_data(raw_data)

        # 3. Écrire en Parquet
        output_file = write_parquet(
            transformed_data,
            args.output_dir,
            args.start_date,
        )

        # 4. Résultat JSON pour orchestrateur (n8n/Airflow)
        result = {
            "status": "success",
            "records_count": len(transformed_data),
            "output_file": output_file,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "ingestion_timestamp": datetime.utcnow().isoformat(),
        }

        # Sortie standard = JSON pour l'orchestrateur
        print(json.dumps(result))

    except Exception as e:
        logger.exception("Ingestion failed")

        result = {
            "status": "error",
            "error": str(e),
            "start_date": args.start_date,
            "end_date": args.end_date,
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == "__main__":
    main()
