"""
Minimal seed script for Traveler Test data.

Usage (run from repo root or API folder):
  - From API folder:
      python scripts/seed_traveler_test.py

Requires DB env vars (.env) to be set (see env.example).
Idempotent: running multiple times won't duplicate records.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Iterator
from contextlib import contextmanager

import os
import sys

# Ensure project root (one level up from scripts/) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
from models import (
    TravelerType,
    Question,
    QuestionOption,
    QuestionOptionScore,
)
from sqlalchemy.orm import Session
from sqlalchemy import func, and_


@contextmanager
def session_scope() -> Iterator[Session]:
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
        # Update defaults if provided
        updated = False
        for k, v in defaults.items():
            if getattr(tt, k, None) != v and v is not None:
                setattr(tt, k, v)
                updated = True
        if updated:
            db.add(tt)
        return tt
    tt = TravelerType(name=name, **defaults)
    db.add(tt)
    db.flush()
    return tt


def next_question_order(db: Session) -> int:
    max_order = (
        db.query(func.max(Question.order))
        .filter(and_(Question.order.is_not(None), Question.deleted_at.is_(None)))
        .scalar()
    )
    return (max_order or 0) + 1


def get_or_create_question(
    db: Session, question_text: str, order: Optional[int] = None, **defaults
) -> Question:
    q = db.query(Question).filter(
        and_(Question.question == question_text, Question.deleted_at.is_(None))
    ).first()
    if q:
        # Update fields if changed
        updated = False
        if order and q.order != order:
            q.order = order
            updated = True
        for k, v in defaults.items():
            if getattr(q, k, None) != v:
                setattr(q, k, v)
                updated = True
        if updated:
            db.add(q)
        return q
    if order is None:
        order = next_question_order(db)
    q = Question(question=question_text, order=order, **defaults)
    db.add(q)
    db.flush()
    return q


def get_or_create_option(
    db: Session, question: Question, option_text: str, **defaults
) -> QuestionOption:
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
            if getattr(opt, k, None) != v and v is not None:
                setattr(opt, k, v)
                updated = True
        if updated:
            db.add(opt)
        return opt
    opt = QuestionOption(question_id=question.id, option=option_text, **defaults)
    db.add(opt)
    db.flush()
    return opt


def upsert_option_score(
    db: Session, option: QuestionOption, traveler_type: TravelerType, score: int
) -> QuestionOptionScore:
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


def seed_minimal(db: Session) -> Dict[str, int]:
    # Traveler Types
    aventurero = get_or_create_traveler_type(
        db,
        "Aventurero",
        description="Ama la aventura, la naturaleza y actividades al aire libre",
        prompt_description="Prefiere itinerarios con trekking, deportes y destinos naturales.",
        image_url="https://example.com/aventurero.jpg",
    )
    cultural = get_or_create_traveler_type(
        db,
        "Cultural",
        description="Disfruta la historia, museos y experiencias locales",
        prompt_description="Valora visitas guiadas, arte, gastronomía típica y arquitectura.",
        image_url="https://example.com/cultural.jpg",
    )
    relax = get_or_create_traveler_type(
        db,
        "Relax",
        description="Busca descanso, spa y playas tranquilas",
        prompt_description="Prefiere itinerarios con ritmos suaves, playa y bienestar.",
        image_url="https://example.com/relax.jpg",
    )

    # Questions + Options + Scores
    q1 = get_or_create_question(
        db,
        "¿Qué preferís en tus vacaciones?",
        category="preferencias",
    )
    q1_o1 = get_or_create_option(db, q1, "Montaña y trekking")
    q1_o2 = get_or_create_option(db, q1, "Museos y tours")
    q1_o3 = get_or_create_option(db, q1, "Playa y descanso")

    upsert_option_score(db, q1_o1, aventurero, 8)
    upsert_option_score(db, q1_o1, cultural, 2)
    upsert_option_score(db, q1_o1, relax, -2)

    upsert_option_score(db, q1_o2, aventurero, 0)
    upsert_option_score(db, q1_o2, cultural, 8)
    upsert_option_score(db, q1_o2, relax, 2)

    upsert_option_score(db, q1_o3, aventurero, -1)
    upsert_option_score(db, q1_o3, cultural, 2)
    upsert_option_score(db, q1_o3, relax, 8)

    # Another question
    q2 = get_or_create_question(
        db,
        "¿Cómo te movés dentro del destino?",
        category="transporte",
    )
    q2_o1 = get_or_create_option(db, q2, "Alquilo auto y exploro")
    q2_o2 = get_or_create_option(db, q2, "Transporte público y caminatas")
    q2_o3 = get_or_create_option(db, q2, "Traslados privados y taxi")

    upsert_option_score(db, q2_o1, aventurero, 7)
    upsert_option_score(db, q2_o1, cultural, 3)
    upsert_option_score(db, q2_o1, relax, 0)

    upsert_option_score(db, q2_o2, aventurero, 4)
    upsert_option_score(db, q2_o2, cultural, 6)
    upsert_option_score(db, q2_o2, relax, 2)

    upsert_option_score(db, q2_o3, aventurero, 0)
    upsert_option_score(db, q2_o3, cultural, 2)
    upsert_option_score(db, q2_o3, relax, 7)

    # A third question
    q3 = get_or_create_question(
        db,
        "¿Qué ritmo de viaje te identifica?",
        category="ritmo",
    )
    q3_o1 = get_or_create_option(db, q3, "Agenda intensa, muchas actividades")
    q3_o2 = get_or_create_option(db, q3, "Equilibrado, tiempo libre y visitas")
    q3_o3 = get_or_create_option(db, q3, "Tranquilo, sin madrugar")

    upsert_option_score(db, q3_o1, aventurero, 8)
    upsert_option_score(db, q3_o1, cultural, 4)
    upsert_option_score(db, q3_o1, relax, -1)

    upsert_option_score(db, q3_o2, aventurero, 4)
    upsert_option_score(db, q3_o2, cultural, 6)
    upsert_option_score(db, q3_o2, relax, 4)

    upsert_option_score(db, q3_o3, aventurero, -1)
    upsert_option_score(db, q3_o3, cultural, 2)
    upsert_option_score(db, q3_o3, relax, 8)

    db.flush()

    counts = {
        "traveler_types": db.query(TravelerType).filter(TravelerType.deleted_at.is_(None)).count(),
        "questions": db.query(Question).filter(Question.deleted_at.is_(None)).count(),
        "options": db.query(QuestionOption).filter(QuestionOption.deleted_at.is_(None)).count(),
        "scores": db.query(QuestionOptionScore).count(),
    }
    return counts


def main() -> None:
    with session_scope() as db:
        counts = seed_minimal(db)
        print("Seed completed:")
        print(f"  Traveler Types: {counts['traveler_types']}")
        print(f"  Questions:      {counts['questions']}")
        print(f"  Options:        {counts['options']}")
        print(f"  Scores:         {counts['scores']}")


if __name__ == "__main__":
    main()
