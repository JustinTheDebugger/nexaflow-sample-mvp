from pathlib import Path

from database import get_connection


def setup_database():
    schema_path = Path("schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

    print("Database schema created successfully.")


if __name__ == "__main__":
    setup_database()