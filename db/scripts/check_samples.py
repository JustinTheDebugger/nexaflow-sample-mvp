from db.connection import get_connection


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sample_id,
                    product_name,
                    current_location,
                    operational_status
                FROM samples
                ORDER BY id;
                """
            )

            samples = cur.fetchall()

            cur.execute(
                """
                SELECT
                    sample_id,
                    event_type,
                    title,
                    new_location
                FROM sample_events
                ORDER BY id;
                """
            )

            events = cur.fetchall()

    print("Samples:")
    for sample in samples:
        print(sample)

    print("\nEvents:")
    for event in events:
        print(event)


if __name__ == "__main__":
    main()