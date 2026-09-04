from pathlib import Path
import sys

from db.connection import get_connection


def run_migration(migration_path: str):
    path = Path(migration_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Migration file not found: {path}"
        )

    sql = path.read_text(
        encoding="utf-8"
    )

    print(
        f"Running migration: {path.name}"
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print(
        "Migration completed successfully."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python -m db.scripts.run_migration "
            "<migration_file>"
        )
        raise SystemExit(1)

    run_migration(
        sys.argv[1]
    )