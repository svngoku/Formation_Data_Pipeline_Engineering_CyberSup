#!/usr/bin/env python3
"""
Validation des données ingérées.

Ce script valide les fichiers Parquet selon des règles configurables
et renvoie un code de sortie approprié pour l'orchestration.

Usage:
    python validate_data.py --input-file data/bronze/partition_date=2024-01-01/data.parquet
    python validate_data.py --input-file data.parquet --rules-file validation_rules.json

Exit codes:
    0 - Validation réussie
    1 - Erreurs de validation détectées
    2 - Erreur d'exécution (fichier non trouvé, etc.)
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

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
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure le logging."""
    logger = logging.getLogger("validate_data")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    return logger


logger = setup_logging()

# =============================================================================
# Règles de validation par défaut
# =============================================================================

DEFAULT_RULES: dict[str, Any] = {
    "required_columns": ["id", "_ingested_at"],
    "not_null_columns": ["id"],
    "unique_columns": ["id"],
    "value_ranges": {},
    "min_rows": 1,
    "max_null_percentage": {},
}


# =============================================================================
# Fonctions de validation
# =============================================================================


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
) -> list[str]:
    """Vérifie que toutes les colonnes requises sont présentes."""
    errors = []
    missing = set(required_columns) - set(df.columns)

    if missing:
        errors.append(f"Missing required columns: {sorted(missing)}")

    return errors


def validate_not_null(
    df: pd.DataFrame,
    not_null_columns: list[str],
) -> list[str]:
    """Vérifie qu'il n'y a pas de valeurs nulles dans les colonnes spécifiées."""
    errors = []

    for col in not_null_columns:
        if col not in df.columns:
            continue

        null_count = df[col].isna().sum()
        if null_count > 0:
            errors.append(f"Column '{col}' has {null_count} null values")

    return errors


def validate_unique(
    df: pd.DataFrame,
    unique_columns: list[str],
) -> list[str]:
    """Vérifie l'unicité des valeurs dans les colonnes spécifiées."""
    errors = []

    for col in unique_columns:
        if col not in df.columns:
            continue

        duplicates = df[col].duplicated().sum()
        if duplicates > 0:
            errors.append(f"Column '{col}' has {duplicates} duplicate values")

    return errors


def validate_value_ranges(
    df: pd.DataFrame,
    value_ranges: dict[str, tuple[float, float]],
) -> list[str]:
    """Vérifie que les valeurs sont dans les ranges spécifiés."""
    errors = []

    for col, (min_val, max_val) in value_ranges.items():
        if col not in df.columns:
            continue

        # Ignorer les nulls pour le range check
        valid_values = df[col].dropna()

        out_of_range = valid_values[(valid_values < min_val) | (valid_values > max_val)]
        if len(out_of_range) > 0:
            errors.append(
                f"Column '{col}' has {len(out_of_range)} values "
                f"out of range [{min_val}, {max_val}]"
            )

    return errors


def validate_min_rows(
    df: pd.DataFrame,
    min_rows: int,
) -> list[str]:
    """Vérifie le nombre minimum de lignes."""
    errors = []

    if len(df) < min_rows:
        errors.append(f"Expected at least {min_rows} rows, got {len(df)}")

    return errors


def validate_max_null_percentage(
    df: pd.DataFrame,
    max_null_percentage: dict[str, float],
) -> list[str]:
    """Vérifie le pourcentage maximum de nulls par colonne."""
    errors = []

    for col, max_pct in max_null_percentage.items():
        if col not in df.columns:
            continue

        null_pct = (df[col].isna().sum() / len(df)) * 100
        if null_pct > max_pct:
            errors.append(
                f"Column '{col}' has {null_pct:.1f}% null values "
                f"(max allowed: {max_pct}%)"
            )

    return errors


def validate(df: pd.DataFrame, rules: dict[str, Any]) -> list[str]:
    """
    Applique toutes les règles de validation.

    Args:
        df: DataFrame à valider
        rules: Dictionnaire des règles de validation

    Returns:
        Liste des erreurs trouvées (vide si tout est OK)
    """
    errors = []

    # Colonnes requises
    errors.extend(
        validate_required_columns(
            df, rules.get("required_columns", [])
        )
    )

    # Pas de nulls
    errors.extend(
        validate_not_null(
            df, rules.get("not_null_columns", [])
        )
    )

    # Unicité
    errors.extend(
        validate_unique(
            df, rules.get("unique_columns", [])
        )
    )

    # Ranges de valeurs
    errors.extend(
        validate_value_ranges(
            df, rules.get("value_ranges", {})
        )
    )

    # Minimum de lignes
    errors.extend(
        validate_min_rows(
            df, rules.get("min_rows", 0)
        )
    )

    # Pourcentage max de nulls
    errors.extend(
        validate_max_null_percentage(
            df, rules.get("max_null_percentage", {})
        )
    )

    return errors


def get_data_profile(df: pd.DataFrame) -> dict[str, Any]:
    """
    Génère un profil basique des données.

    Args:
        df: DataFrame à profiler

    Returns:
        Dictionnaire avec les statistiques
    """
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "null_counts": df.isna().sum().to_dict(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }

    # Stats numériques
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        profile["numeric_stats"] = df[numeric_cols].describe().to_dict()

    return profile


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="Validation des données ingérées",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python validate_data.py --input-file data.parquet
  python validate_data.py --input-file data.parquet --rules-file rules.json
  python validate_data.py --input-file data.parquet --profile

Fichier de règles (JSON):
  {
    "required_columns": ["id", "title"],
    "not_null_columns": ["id"],
    "unique_columns": ["id"],
    "value_ranges": {"userId": [1, 100]},
    "min_rows": 10,
    "max_null_percentage": {"body": 5.0}
  }
        """,
    )

    parser.add_argument(
        "--input-file",
        required=True,
        help="Fichier Parquet à valider",
    )
    parser.add_argument(
        "--rules-file",
        help="Fichier JSON contenant les règles de validation",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Inclure un profil des données dans le résultat",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Mode strict: échoue dès la première erreur",
    )

    return parser.parse_args()


def main() -> None:
    """Point d'entrée principal."""
    args = parse_args()

    # Vérifier que le fichier existe
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        result = {
            "status": "error",
            "error": f"File not found: {input_path}",
            "file": str(input_path),
        }
        print(json.dumps(result, indent=2))
        sys.exit(2)

    # Charger les règles
    if args.rules_file:
        try:
            with open(args.rules_file) as f:
                rules = json.load(f)
            logger.info(f"Loaded rules from {args.rules_file}")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            result = {
                "status": "error",
                "error": f"Failed to load rules file: {e}",
            }
            print(json.dumps(result, indent=2))
            sys.exit(2)
    else:
        rules = DEFAULT_RULES
        logger.info("Using default validation rules")

    try:
        # Lire le fichier
        logger.info(f"Reading file: {input_path}")
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

        # Valider
        errors = validate(df, rules)

        # Construire le résultat
        result: dict[str, Any] = {
            "file": str(input_path),
            "rows": len(df),
            "columns": list(df.columns),
            "validation": "passed" if not errors else "failed",
            "errors": errors,
            "error_count": len(errors),
            "validated_at": datetime.utcnow().isoformat(),
            "rules_applied": list(rules.keys()),
        }

        # Ajouter le profil si demandé
        if args.profile:
            result["profile"] = get_data_profile(df)

        # Afficher le résultat
        print(json.dumps(result, indent=2))

        # Code de sortie
        if errors:
            logger.warning(f"Validation failed with {len(errors)} errors")
            sys.exit(1)
        else:
            logger.info("Validation passed")
            sys.exit(0)

    except Exception as e:
        logger.exception("Validation failed with exception")
        result = {
            "status": "error",
            "error": str(e),
            "file": str(input_path),
        }
        print(json.dumps(result, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
