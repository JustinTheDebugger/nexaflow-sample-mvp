from pathlib import Path

from db.connection import get_connection


def reset_database():
    reset_sql = Path(
        "db/reset_sample_schema.sql"
    ).read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(reset_sql)

    print("Sample schema reset successfully.")


if __name__ == "__main__":
    reset_database()