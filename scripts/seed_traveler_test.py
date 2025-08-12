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
            "name": "Adventurer",
            "description": "Loves adrenaline, nature, and physical challenges. Not afraid to step out of their comfort zone.",
            "prompt_description": "Prioritize high-impact activities: extreme sports, trekking in remote places, wild nature exploration, and flexible transport options like 4x4 vehicles. Avoid rigid or overly touristy itineraries.",
            "image_url": None,
        },
        {
            "name": "Cultural Explorer",
            "description": "Passionate about history, art, architecture, and local traditions. Enjoys learning on every visit.",
            "prompt_description": "Focus the itinerary on historic centers, museums, art galleries, guided tours, local shows, and traditional cuisine. The pace can be intense but knowledge-focused.",
            "image_url": None,
        },
        {
            "name": "Relaxed Traveler",
            "description": "Seeks to disconnect, rest, and recharge. Prefers destinations and activities that bring peace and tranquility.",
            "prompt_description": "Create itineraries with a gentle pace. Include beach days, spa stays, nature walks without pressure, free afternoons, and quiet dinners. Avoid early mornings and tight schedules.",
            "image_url": None,
        },
        {
            "name": "Gourmet",
            "description": "Main motivation for travel is food. From local markets to Michelin-starred restaurants.",
            "prompt_description": "The trip should revolve around gastronomy. Include reservations at recommended restaurants, food tours, cooking classes, market visits, and tastings of local products (wine, cheese, etc.).",
            "image_url": None,
        },
        {
            "name": "Social & Nightlife",
            "description": "Loves nightlife, meeting people, and being at the center of the action. Travels to have fun and socialize.",
            "prompt_description": "Design a plan that includes recommendations for bars, clubs, events, and neighborhoods with vibrant nightlife. Suggest group activities and hostels or hotels with a good social atmosphere.",
            "image_url": None,
        },
        {
            "name": "Romantic",
            "description": "Travels as a couple seeking special moments, beautiful landscapes, and intimate experiences. Ideal for honeymoons or anniversaries.",
            "prompt_description": "Create an itinerary with candlelit dinners, boutique hotels, scenic walks, activities for two, and moments of privacy. The atmosphere should be special and cared for.",
            "image_url": None,
        },
    ],
    "questions": [
        {
            "order": 1,
            "question": "What is your ideal way to explore a destination?",
            "category": "Exploration Style",
            "multi_select": False,
            "options": [
                {
                    "option": "With a tour that takes me to the most famous places.",
                    "scores": {"Adventurer": -2, "Cultural Explorer": 8, "Relaxed Traveler": 5, "Gourmet": 3, "Social & Nightlife": 4, "Romantic": 6},
                },
                {
                    "option": "Getting lost on alternative routes.",
                    "scores": {"Adventurer": 10, "Cultural Explorer": 6, "Relaxed Traveler": -2, "Gourmet": 4, "Social & Nightlife": 3, "Romantic": 4},
                },
                {
                    "option": "Living like a local, no rush.",
                    "scores": {"Adventurer": 2, "Cultural Explorer": 7, "Relaxed Traveler": 10, "Gourmet": 8, "Social & Nightlife": 5, "Romantic": 8},
                },
            ],
        },
        {
            "order": 2,
            "question": "When you think of the perfect trip, what word comes to mind?",
            "category": "Main Interest",
            "multi_select": False,
            "options": [
                {"option": "Adventure", "scores": {"Adventurer": 10, "Cultural Explorer": 0, "Relaxed Traveler": -5, "Gourmet": -1, "Social & Nightlife": 3, "Romantic": 2}},
                {"option": "Culture", "scores": {"Adventurer": 0, "Cultural Explorer": 10, "Relaxed Traveler": 2, "Gourmet": 4, "Social & Nightlife": 1, "Romantic": 5}},
                {"option": "Relax", "scores": {"Adventurer": -5, "Cultural Explorer": 2, "Relaxed Traveler": 10, "Gourmet": 3, "Social & Nightlife": -2, "Romantic": 8}},
                {"option": "Flavors", "scores": {"Adventurer": 2, "Cultural Explorer": 4, "Relaxed Traveler": 3, "Gourmet": 10, "Social & Nightlife": 5, "Romantic": 6}},
                {"option": "Party", "scores": {"Adventurer": 3, "Cultural Explorer": -2, "Relaxed Traveler": -4, "Gourmet": 2, "Social & Nightlife": 10, "Romantic": 1}},
            ],
        },
        {
            "order": 3,
            "question": "Gastronomy on your trip is...",
            "category": "Gastronomy",
            "multi_select": False,
            "options": [
                {"option": "The main reason for my trip.", "scores": {"Adventurer": 1, "Cultural Explorer": 5, "Relaxed Traveler": 4, "Gourmet": 10, "Social & Nightlife": 5, "Romantic": 7}},
                {"option": "Important, I like to try everything.", "scores": {"Adventurer": 6, "Cultural Explorer": 8, "Relaxed Traveler": 6, "Gourmet": 7, "Social & Nightlife": 6, "Romantic": 8}},
                {"option": "Just a way to recharge energy.", "scores": {"Adventurer": 4, "Cultural Explorer": -3, "Relaxed Traveler": 2, "Gourmet": -5, "Social & Nightlife": 3, "Romantic": 1}},
                {"option": "I prefer cheap and on-the-go options.", "scores": {"Adventurer": 7, "Cultural Explorer": 2, "Relaxed Traveler": 3, "Gourmet": 1, "Social & Nightlife": 6, "Romantic": 2}},
            ],
        },
        {
            "order": 4,
            "question": "What travel pace best identifies you?",
            "category": "Pace",
            "multi_select": False,
            "options": [
                {"option": "Intense: I want to make the most of every second.", "scores": {"Adventurer": 10, "Cultural Explorer": 7, "Relaxed Traveler": -5, "Gourmet": 5, "Social & Nightlife": 8, "Romantic": 2}},
                {"option": "Balanced: mixing activities with leisure.", "scores": {"Adventurer": 5, "Cultural Explorer": 8, "Relaxed Traveler": 6, "Gourmet": 8, "Social & Nightlife": 6, "Romantic": 8}},
                {"option": "Relaxed: improvisation is my motto.", "scores": {"Adventurer": -2, "Cultural Explorer": 3, "Relaxed Traveler": 10, "Gourmet": 6, "Social & Nightlife": 4, "Romantic": 10}},
            ],
        },
        {
            "order": 5,
            "question": "At night, you prefer to...",
            "category": "Nightlife",
            "multi_select": False,
            "options": [
                {"option": "Go out to bars and experience the local scene.", "scores": {"Adventurer": 4, "Cultural Explorer": 3, "Relaxed Traveler": -2, "Gourmet": 4, "Social & Nightlife": 10, "Romantic": 3}},
                {"option": "Have a special, quiet dinner.", "scores": {"Adventurer": 2, "Cultural Explorer": 7, "Relaxed Traveler": 8, "Gourmet": 9, "Social & Nightlife": 3, "Romantic": 10}},
                {"option": "Rest at the hotel for the next day.", "scores": {"Adventurer": 5, "Cultural Explorer": 5, "Relaxed Traveler": 10, "Gourmet": 3, "Social & Nightlife": -3, "Romantic": 6}},
                {"option": "Attend a cultural show or event.", "scores": {"Adventurer": 1, "Cultural Explorer": 9, "Relaxed Traveler": 5, "Gourmet": 6, "Social & Nightlife": 4, "Romantic": 7}},
            ],
        },
        {
            "order": 6,
            "question": "Select the activities that interest you the most (you can choose several):",
            "category": "Direct Interests",
            "multi_select": True,
            "options": [
                {"option": "Beaches", "scores": {"Relaxed Traveler": 5, "Romantic": 3}},
                {"option": "City sightseeing", "scores": {"Cultural Explorer": 7, "Social & Nightlife": 3}},
                {"option": "Outdoor adventures", "scores": {"Adventurer": 8, "Social & Nightlife": 2}},
                {"option": "Festivals/events", "scores": {"Social & Nightlife": 8, "Cultural Explorer": 4}},
                {"option": "Food exploration", "scores": {"Gourmet": 8, "Cultural Explorer": 3}},
                {"option": "Nightlife", "scores": {"Social & Nightlife": 8, "Adventurer": 2}},
                {"option": "Shopping", "scores": {"Social & Nightlife": 5, "Romantic": 4}},
                {"option": "Spa wellness", "scores": {"Relaxed Traveler": 9, "Romantic": 4}},
            ],
        },
    ],
}


# Mapping of renames from old Spanish names to new English names
TRAVELER_TYPE_RENAMES = {
    "Aventurero": "Adventurer",
    "Cultural": "Cultural Explorer",
    "Relax": "Relaxed Traveler",
}

# --- Database Models (assuming they are in the 'models' package) ---
from database import SessionLocal
from models import Question, QuestionOption, QuestionOptionScore, TravelerType
from sqlalchemy import and_, func
from sqlalchemy.orm import Session


def _apply_traveler_type_renames(db: Session) -> None:
    """Rename existing types according to TRAVELER_TYPE_RENAMES, merging data."""
    from models.traveler_test.user_traveler_test import UserTravelerTest

    for old_name, new_name in TRAVELER_TYPE_RENAMES.items():
        if old_name == new_name:
            continue

        old_obj = db.query(TravelerType).filter(TravelerType.name == old_name, TravelerType.deleted_at.is_(None)).first()
        if not old_obj:
            continue

        target_obj = db.query(TravelerType).filter(TravelerType.name == new_name, TravelerType.deleted_at.is_(None)).first()
        if not target_obj:
            old_obj.name = new_name
            db.add(old_obj)
            print(f"Renamed TravelerType '{old_name}' to '{new_name}'.")
            continue

        scores = db.query(QuestionOptionScore).filter(QuestionOptionScore.traveler_type_id == old_obj.id).all()
        for sc in scores:
            dup = db.query(QuestionOptionScore).filter(
                QuestionOptionScore.question_option_id == sc.question_option_id,
                QuestionOptionScore.traveler_type_id == target_obj.id,
            ).first()
            if dup:
                db.delete(sc)
            else:
                sc.traveler_type_id = target_obj.id
                db.add(sc)
        
        uts = db.query(UserTravelerTest).filter(UserTravelerTest.traveler_type_id == old_obj.id).all()
        for ut in uts:
            ut.traveler_type_id = target_obj.id
            db.add(ut)

        old_obj.deleted_at = datetime.now(timezone.utc)
        db.add(old_obj)
        print(f"Merged TravelerType '{old_name}' into '{new_name}' and soft-deleted the old one.")


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


def get_or_create_question(db: Session, question_text: str, **defaults) -> Question:
    q = db.query(Question).filter(
        and_(Question.question == question_text, Question.deleted_at.is_(None))
    ).first()
    if q:
        updated = False
        for k, v in defaults.items():
            if getattr(q, k, None) != v and v is not None:
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


def seed_from_data(db: Session) -> Dict[str, int]:
    """Seed DB from the TRAVELER_TEST_DATA structure (idempotent/upsert)."""
    _apply_traveler_type_renames(db)
    db.flush()

    traveler_type_objs: Dict[str, TravelerType] = {}
    for tt_data in TRAVELER_TEST_DATA.get("traveler_types", []):
        name = tt_data["name"].strip()
        defaults = {k: v for k, v in tt_data.items() if k != "name"}
        traveler_type_objs[name] = get_or_create_traveler_type(db, name, **defaults)

    for q_data in TRAVELER_TEST_DATA.get("questions", []):
        question_text = q_data["question"].strip()
        q_defaults = {
            "order": q_data.get("order"),
            "category": q_data.get("category"),
            "image_url": q_data.get("image_url"),
            "multi_select": q_data.get("multi_select", False),
        }
        q_obj = get_or_create_question(db, question_text, **q_defaults)

        for opt_data in q_data.get("options", []):
            option_text = opt_data["option"].strip()
            opt_defaults = {
                "description": opt_data.get("description"),
                "image_url": opt_data.get("image_url"),
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

        counts = seed_from_data(db)
        print("\nTraveler Test seed completed from TRAVELER_TEST_DATA:")
        print(f"  - Active Traveler Types: {counts['traveler_types']}")
        print(f"  - Active Questions:      {counts['questions']}")
        print(f"  - Active Options:        {counts['options']}")
        print(f"  - Total Scores:          {counts['scores']}")


if __name__ == "__main__":
    main()