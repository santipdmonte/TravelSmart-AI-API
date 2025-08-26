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

# Ensure project root (one level up from scripts/) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


"""
PHASE 1: Centralized data structure for the Traveler Test.

NOTES:
- Image URLs are examples from Unsplash (can be replaced with own assets).
- Scores are in the range [-10, 10] (validated by a DB constraint).

Structure:
TRAVELER_TEST_DATA = {
  'traveler_types': [
     { name, description, prompt_description, image_url }
  ],
  'questions': [
     {
        'order': int,
        'question': str,
        'category': str,
        'image_url': str | None,
        'multi_select': bool,
        'options': [
           {
              'option': str,
              'description': str | None,
              'image_url': str | None,
              'scores': { traveler_type_name: int, ... }
           }, ...
        ]
     }, ...
  ]
}
"""

TRAVELER_TEST_DATA: Dict[str, List[Dict]] = {
    "traveler_types": [
        {
            "name": "Aventurero",
            "description": "Amante de la adrenalina, la naturaleza y los desafíos físicos. No teme salir de su zona de confort.",
            "prompt_description": "Priorizar actividades de alto impacto: deportes extremos, trekking en lugares remotos, exploración de naturaleza salvaje y opciones de transporte flexibles. Evitar itinerarios rígidos o demasiado turísticos.",
            "image_url": None,
        },
        {
            "name": "Explorador Cultural",
            "description": "Apasionado por la historia, el arte, la arquitectura y las tradiciones locales. Disfruta aprendiendo en cada visita.",
            "prompt_description": "Enfocar el itinerario en centros históricos, museos, galerías de arte, tours guiados, espectáculos locales y gastronomía tradicional. El ritmo puede ser intenso pero centrado en el conocimiento.",
            "image_url": None,
        },
        {
            "name": "Viajero Relajado",
            "description": "Busca desconectar, descansar y recargar energías. Prefiere destinos y actividades que le aporten paz y tranquilidad.",
            "prompt_description": "Crear itinerarios con un ritmo suave. Incluir días de playa, estancias en spas, paseos por la naturaleza sin presiones, tardes libres y cenas tranquilas. Evitar madrugones y agendas apretadas.",
            "image_url": None,
        },
        {
            "name": "Gourmet",
            "description": "Su principal motivación para viajar es la comida. Desde mercados locales hasta restaurantes con estrellas Michelin.",
            "prompt_description": "El viaje debe girar en torno a la gastronomía. Incluir reservas en restaurantes recomendados, tours de comida, clases de cocina, visitas a mercados y degustaciones de productos locales (vino, queso, etc.).",
            "image_url": None,
        },
        {
            "name": "Social y Nocturno",
            "description": "Le encanta la vida nocturna, conocer gente y estar en el centro de la acción. Viaja para divertirse y socializar.",
            "prompt_description": "Diseñar un plan que incluya recomendaciones de bares, discotecas, eventos y barrios con mucha vida nocturna. Sugerir actividades en grupo y hoteles con buen ambiente social.",
            "image_url": None,
        },
        {
            "name": "Romántico",
            "description": "Viaja en pareja buscando momentos especiales, paisajes hermosos y experiencias íntimas. Ideal para lunas de miel o aniversarios.",
            "prompt_description": "Crear un itinerario con cenas a la luz de las velas, hoteles boutique, paseos panorámicos, actividades para dos y momentos de privacidad. El ambiente debe ser especial y cuidado.",
            "image_url": None,
        },
    ],
    "questions": [
        {
            "order": 1,
            "question": "¿Cuál es tu forma ideal de explorar un destino?",
            "category": "Estilo de Exploración",
            "multi_select": False,
            "options": [
                {
                    "option": "Con un tour que me lleve a los lugares más famosos.",
                    "scores": {"Aventurero": -2, "Explorador Cultural": 8, "Viajero Relajado": 5, "Gourmet": 3, "Social y Nocturno": 4, "Romántico": 6},
                },
                {
                    "option": "Perdiéndome por rutas alternativas.",
                    "scores": {"Aventurero": 10, "Explorador Cultural": 6, "Viajero Relajado": -2, "Gourmet": 4, "Social y Nocturno": 3, "Romántico": 4},
                },
                {
                    "option": "Viviendo como un local, sin prisas.",
                    "scores": {"Aventurero": 2, "Explorador Cultural": 7, "Viajero Relajado": 10, "Gourmet": 8, "Social y Nocturno": 5, "Romántico": 8},
                },
            ],
        },
        {
            "order": 2,
            "question": "Cuando piensas en el viaje perfecto, ¿qué palabra te viene a la mente?",
            "category": "Interés Principal",
            "multi_select": False,
            "options": [
                {"option": "Aventura", "scores": {"Aventurero": 10, "Explorador Cultural": 0, "Viajero Relajado": -5, "Gourmet": -1, "Social y Nocturno": 3, "Romántico": 2}},
                {"option": "Cultura", "scores": {"Aventurero": 0, "Explorador Cultural": 10, "Viajero Relajado": 2, "Gourmet": 4, "Social y Nocturno": 1, "Romántico": 5}},
                {"option": "Relajación", "scores": {"Aventurero": -5, "Explorador Cultural": 2, "Viajero Relajado": 10, "Gourmet": 3, "Social y Nocturno": -2, "Romántico": 8}},
                {"option": "Sabores", "scores": {"Aventurero": 2, "Explorador Cultural": 4, "Viajero Relajado": 3, "Gourmet": 10, "Social y Nocturno": 5, "Romántico": 6}},
                {"option": "Fiesta", "scores": {"Aventurero": 3, "Explorador Cultural": -2, "Viajero Relajado": -4, "Gourmet": 2, "Social y Nocturno": 10, "Romántico": 1}},
                {"option": "Romance", "scores": {"Aventurero": 1, "Explorador Cultural": 5, "Viajero Relajado": 8, "Gourmet": 6, "Social y Nocturno": 2, "Romántico": 10}},
                {"option": "Adrenalina", "scores": {"Aventurero": 10, "Social y Nocturno": 4, "Viajero Relajado": -6, "Romántico": 1}},
            ],
        },
        {
            "order": 3,
            "question": "La gastronomía en tu viaje es...",
            "category": "Gastronomía",
            "multi_select": False,
            "options": [
                {"option": "La razón principal de mi viaje.", "scores": {"Aventurero": 1, "Explorador Cultural": 5, "Viajero Relajado": 4, "Gourmet": 10, "Social y Nocturno": 5, "Romántico": 7}},
                {"option": "Importante, me gusta probar de todo.", "scores": {"Aventurero": 6, "Explorador Cultural": 8, "Viajero Relajado": 6, "Gourmet": 7, "Social y Nocturno": 6, "Romántico": 8}},
                {"option": "Solo una forma de reponer energías.", "scores": {"Aventurero": 4, "Explorador Cultural": -3, "Viajero Relajado": 2, "Gourmet": -5, "Social y Nocturno": 3, "Romántico": 1}},
                {"option": "Prefiero opciones baratas y al paso.", "scores": {"Aventurero": 7, "Explorador Cultural": 2, "Viajero Relajado": 3, "Gourmet": 1, "Social y Nocturno": 6, "Romántico": 2}},
            ],
        },
        {
            "order": 4,
            "question": "¿Qué ritmo de viaje te identifica más?",
            "category": "Ritmo",
            "multi_select": False,
            "options": [
                {"option": "Intenso: quiero aprovechar cada segundo.", "scores": {"Aventurero": 10, "Explorador Cultural": 7, "Viajero Relajado": -5, "Gourmet": 5, "Social y Nocturno": 8, "Romántico": 2}},
                {"option": "Equilibrado: mezclando actividades con ocio.", "scores": {"Aventurero": 5, "Explorador Cultural": 8, "Viajero Relajado": 6, "Gourmet": 8, "Social y Nocturno": 6, "Romántico": 8}},
                {"option": "Relajado: la improvisación es mi lema.", "scores": {"Aventurero": -2, "Explorador Cultural": 3, "Viajero Relajado": 10, "Gourmet": 6, "Social y Nocturno": 4, "Romántico": 10}},
            ],
        },
        {
            "order": 5,
            "question": "Por la noche, prefieres...",
            "category": "Vida Nocturna",
            "multi_select": False,
            "options": [
                {"option": "Salir a bares y vivir la escena local.", "scores": {"Aventurero": 4, "Explorador Cultural": 3, "Viajero Relajado": -2, "Gourmet": 4, "Social y Nocturno": 10, "Romántico": 3}},
                {"option": "Tener una cena especial y tranquila.", "scores": {"Aventurero": 2, "Explorador Cultural": 7, "Viajero Relajado": 8, "Gourmet": 9, "Social y Nocturno": 3, "Romántico": 10}},
                {"option": "Descansar en el hotel para el día siguiente.", "scores": {"Aventurero": 5, "Explorador Cultural": 5, "Viajero Relajado": 10, "Gourmet": 3, "Social y Nocturno": -3, "Romántico": 6}},
                {"option": "Asistir a un espectáculo o evento cultural.", "scores": {"Aventurero": 1, "Explorador Cultural": 9, "Viajero Relajado": 5, "Gourmet": 6, "Social y Nocturno": 4, "Romántico": 7}},
            ],
        },
        {
            "order": 6,
            "question": "Selecciona las actividades que más te interesan (puedes elegir varias):",
            "category": "Intereses Directos",
            "multi_select": True,
            "options": [
                {"option": "Playas", "scores": {"Viajero Relajado": 5, "Romántico": 3}},
                {"option": "Turismo urbano", "scores": {"Explorador Cultural": 7, "Social y Nocturno": 3}},
                {"option": "Aventuras al aire libre", "scores": {"Aventurero": 8, "Social y Nocturno": 2}},
                {"option": "Festivales/eventos", "scores": {"Social y Nocturno": 8, "Explorador Cultural": 4}},
                {"option": "Exploración gastronómica", "scores": {"Gourmet": 8, "Explorador Cultural": 3}},
                {"option": "Vida nocturna", "scores": {"Social y Nocturno": 8, "Aventurero": 2}},
                {"option": "Compras", "scores": {"Social y Nocturno": 5, "Romántico": 4}},
                {"option": "Spa y bienestar", "scores": {"Viajero Relajado": 9, "Romántico": 4}},
            ],
        },
    ],
}


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