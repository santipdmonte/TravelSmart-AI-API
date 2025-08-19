"""
Hard-delete all soft-deleted Traveler Test data to clean the database.

This script removes any rows with deleted_at IS NOT NULL for:
 - questions
 - question_options

Usage (from repo root or API folder):
  Windows PowerShell:
    python scripts/cleanup_soft_deletes.py

Note: Ensure your .env is configured (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME).
NEVER run against production without a backup.
"""

from database import SessionLocal
from models.traveler_test.question import Question
from models.traveler_test.question_option import QuestionOption


def cleanup_soft_deleted() -> dict:
    """Hard-delete all rows where deleted_at is not NULL.

    Returns a dict with counts of deleted rows per table.
    """
    session = SessionLocal()
    report = {"questions": 0, "question_options": 0}
    try:
        # Delete child rows first to respect FK constraints if any
        q1 = session.query(QuestionOption).filter(QuestionOption.deleted_at.is_not(None))
        report["question_options"] = q1.count()
        q1.delete(synchronize_session=False)

        q2 = session.query(Question).filter(Question.deleted_at.is_not(None))
        report["questions"] = q2.count()
        q2.delete(synchronize_session=False)

        session.commit()
        return report
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    stats = cleanup_soft_deleted()
    print("Cleanup complete:")
    for table, count in stats.items():
        print(f"  {table}: deleted {count} rows")
