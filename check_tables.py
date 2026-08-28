from database import get_connection


def check_tables():
    sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name LIKE 'sample%'
        ORDER BY table_name;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    print("NexaFlow sample tables:")

    for row in rows:
        print("-", row["table_name"])


if __name__ == "__main__":
    check_tables()