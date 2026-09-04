from pathlib import Path

from db.connection import get_connection


def setup_database():
    schema_sql = Path(
        "db/schema.sql"
    ).read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

    print("Database schema created successfully.")


if __name__ == "__main__":
    setup_database()