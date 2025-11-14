"""
Minimal seed script for Traveler Test data.

Usage (run from repo root or API folder):
  - From API folder:
      python scripts/seed_traveler_test.py

Requires DB env vars (.env) to be set (see env.example).
Idempotent: running multiple times won't duplicate records.
"""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional
import json  # <-- AÑADIDO

# Ensure project root (one level up from scripts/) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# --- INICIO: LÓGICA DE CARGA DE DATOS ---
# Reemplaza el diccionario TRAVELER_TEST_DATA
# Asume que 'seed_data.json' está en la misma carpeta 'scripts'
DATA_FILE_PATH = os.path.join(CURRENT_DIR, "seed_data.json")

try:
    with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
        TRAVELER_TEST_DATA: Dict[str, List[Dict]] = json.load(f)
except FileNotFoundError:
    print(f"Error: No se encontró el archivo de datos 'seed_data.json' en {DATA_FILE_PATH}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: El archivo 'seed_data.json' tiene un formato JSON inválido.")
    sys.exit(1)
except Exception as e:
    print(f"Error inesperado al cargar 'seed_data.json': {e}")
    sys.exit(1)

# --- FIN: LÓGICA DE CARGA DE DATOS ---


# --- Database Models (assuming they are in the 'models' package) ---
from database import SessionLocal
from models import Question, QuestionOption, QuestionOptionScore, TravelerType
from sqlalchemy import and_, func
from sqlalchemy.orm import Session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_traveler_type(db: Session, name: str, **defaults) -> TravelerType:
    tt = db.query(TravelerType).filter(
        and_(TravelerType.name == name, TravelerType.deleted_at.is_(None))
    ).first()
    if tt:
        updated = False
        for k, v in defaults.items():
            # Update even when value is None (e.g., to clear image_url)
            if getattr(tt, k, None) != v:
                setattr(tt, k, v)
                updated = True
        if updated:
            db.add(tt)
        return tt
    tt = TravelerType(name=name, **defaults)
    db.add(tt)
    db.flush()
    return tt


def get_or_create_question(db: Session, question_text: str, **defaults) -> Question:
    q = db.query(Question).filter(
        and_(Question.question == question_text, Question.deleted_at.is_(None))
    ).first()
    if q:
        updated = False
        for k, v in defaults.items():
            # Update even when value is None (e.g., to clear image_url)
            if getattr(q, k, None) != v:
                setattr(q, k, v)
                updated = True
        if updated:
            db.add(q)
        return q
    q = Question(question=question_text, **defaults)
    db.add(q)
    db.flush()
    return q


def get_or_create_option(db: Session, question: Question, option_text: str, **defaults) -> QuestionOption:
    opt = (
        db.query(QuestionOption)
        .filter(
            and_(
                QuestionOption.question_id == question.id,
                QuestionOption.option == option_text,
                QuestionOption.deleted_at.is_(None),
            )
        )
        .first()
    )
    if opt:
        updated = False
        for k, v in defaults.items():
            # Update even when value is None (e.g., to clear image_url)
            if getattr(opt, k, None) != v:
                setattr(opt, k, v)
                updated = True
        if updated:
            db.add(opt)
        return opt
    opt = QuestionOption(question_id=question.id, option=option_text, **defaults)
    db.add(opt)
    db.flush()
    return opt


def upsert_option_score(db: Session, option: QuestionOption, traveler_type: TravelerType, score: int) -> QuestionOptionScore:
    rec = (
        db.query(QuestionOptionScore)
        .filter(
            and_(
                QuestionOptionScore.question_option_id == option.id,
                QuestionOptionScore.traveler_type_id == traveler_type.id,
            )
        )
        .first()
    )
    if rec:
        if rec.score != score:
            rec.score = score
            db.add(rec)
        return rec
    rec = QuestionOptionScore(
        question_option_id=option.id, traveler_type_id=traveler_type.id, score=score
    )
    db.add(rec)
    return rec

def seed_traveler_test(db: Session) -> Dict[str, int]:
    """Seed DB from the TRAVELER_TEST_DATA structure (idempotent/upsert)."""
    db.flush()

    traveler_type_objs: Dict[str, TravelerType] = {}
    for tt_data in TRAVELER_TEST_DATA.get("traveler_types", []):
        name = tt_data["name"].strip()
        defaults = {k: v for k, v in tt_data.items() if k != "name"}
        # Always keep images null
        defaults["image_url"] = None
        traveler_type_objs[name] = get_or_create_traveler_type(db, name, **defaults)

    for q_data in TRAVELER_TEST_DATA.get("questions", []):
        question_text = q_data["question"].strip()
        q_defaults = {
            "order": q_data.get("order"),
            "category": q_data.get("category"),
            # Always keep images null
            "image_url": None,
            "multi_select": q_data.get("multi_select", False),
        }
        q_obj = get_or_create_question(db, question_text, **q_defaults)

        for opt_data in q_data.get("options", []):
            option_text = opt_data["option"].strip()
            opt_defaults = {
                "description": opt_data.get("description"),
                # Always keep images null
                "image_url": None,
            }
            opt_obj = get_or_create_option(db, q_obj, option_text, **opt_defaults)

            for tt_name, score in opt_data.get("scores", {}).items():
                tt_obj = traveler_type_objs.get(tt_name)
                if not tt_obj:
                    print(f"Warning: Traveler type '{tt_name}' not found for option '{option_text}'. Skipping score.")
                    continue
                if not -10 <= score <= 10:
                    raise ValueError(f"Score out of range for '{option_text}' -> '{tt_name}': {score}")
                upsert_option_score(db, opt_obj, tt_obj, int(score))

    db.flush()
    counts = {
        "traveler_types": db.query(TravelerType).filter(TravelerType.deleted_at.is_(None)).count(),
        "questions": db.query(Question).filter(Question.deleted_at.is_(None)).count(),
        "options": db.query(QuestionOption).filter(QuestionOption.deleted_at.is_(None)).count(),
        "scores": db.query(QuestionOptionScore).count(),
    }
    return counts


def prune_not_listed(db: Session) -> Dict[str, int]:
    """Soft-delete records that are not listed in TRAVELER_TEST_DATA."""
    now = datetime.now(timezone.utc)
    pruned_counts = {"traveler_types": 0, "questions": 0}

    keep_tt_names = {tt["name"].strip() for tt in TRAVELER_TEST_DATA.get("traveler_types", [])}
    for tt in db.query(TravelerType).filter(TravelerType.deleted_at.is_(None), TravelerType.name.notin_(keep_tt_names)):
        tt.deleted_at = now
        db.add(tt)
        pruned_counts["traveler_types"] += 1

    keep_q_text = {q["question"].strip() for q in TRAVELER_TEST_DATA.get("questions", [])}
    for q in db.query(Question).filter(Question.deleted_at.is_(None), Question.question.notin_(keep_q_text)):
        q.deleted_at = now
        db.add(q)
        pruned_counts["questions"] += 1

    db.flush()
    return pruned_counts


def main() -> None:
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Seed or prune Traveler Test data.")
    parser.add_argument("--prune", action="store_true", help="Soft-delete records not listed in TRAVELER_TEST_DATA before seeding.")
    args = parser.parse_args()

    with session_scope() as db:
        if args.prune:
            pruned = prune_not_listed(db)
            print("Pruning (soft-delete) complete:")
            print(f"  - Pruned Traveler Types: {pruned['traveler_types']}")
            print(f"  - Pruned Questions: {pruned['questions']}")

        counts = seed_traveler_test(db)
        print("Seeding complete:")
        print(f"  - Traveler Types: {counts['traveler_types']}")
        print(f"  - Questions: {counts['questions']}")
        print(f"  - Options: {counts['options']}")
        print(f"  - Scores: {counts['scores']}")


if __name__ == "__main__":
    main()