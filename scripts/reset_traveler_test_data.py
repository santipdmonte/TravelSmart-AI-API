"""
Reset Traveler Test data to the canonical set defined in scripts/seed_traveler_test.py.

This script will:
  1) Hard-delete data in FK-safe order:
       - question_option_scores
       - user_answers
       - question_options
       - questions
  2) Reseed from TRAVELER_TEST_DATA via seed_from_data()

Usage (from API folder):
  python scripts/reset_traveler_test_data.py

CAUTION: This permanently deletes existing data in the listed tables.
Make sure your .env points to the intended database before running.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Dict

# Ensure project root (one level up from scripts/) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
from models.traveler_test.question import Question
from models.traveler_test.question_option import QuestionOption
from models.traveler_test.question_option_score import QuestionOptionScore
from models.traveler_test.user_answers import UserAnswer


def hard_delete_test_data() -> Dict[str, int]:
    """Hard-delete all traveler test data in FK-safe order.

    Returns a dict of deleted counts by table.
    """
    session = SessionLocal()
    report = {
        "question_option_scores": 0,
        "user_answers": 0,
        "question_options": 0,
        "questions": 0,
    }
    try:
        # 1) QuestionOptionScore
        q1 = session.query(QuestionOptionScore)
        report["question_option_scores"] = q1.count()
        q1.delete(synchronize_session=False)

        # 2) UserAnswer
        q2 = session.query(UserAnswer)
        report["user_answers"] = q2.count()
        q2.delete(synchronize_session=False)

        # 3) QuestionOption
        q3 = session.query(QuestionOption)
        report["question_options"] = q3.count()
        q3.delete(synchronize_session=False)

        # 4) Question
        q4 = session.query(Question)
        report["questions"] = q4.count()
        q4.delete(synchronize_session=False)

        session.commit()
        return report
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    deleted = hard_delete_test_data()
    print("Hard-delete complete:")
    for table, count in deleted.items():
        print(f"  - {table}: deleted {count} rows")

    # Reseed from canonical data
    session = SessionLocal()
    try:
        session.commit()
        print("\nReseed complete from TRAVELER_TEST_DATA:")
        print("\nTraveler Test data reset successfully.")
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
