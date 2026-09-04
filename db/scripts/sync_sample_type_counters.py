from db.connection import get_connection


def sync_sample_type_counters():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Create a counter row for every sample type
            # that does not already have one.
            cur.execute(
                """
                INSERT INTO sample_id_counters (
                    sample_type_id,
                    last_number
                )
                SELECT
                    st.id,
                    0
                FROM sample_types st
                LEFT JOIN sample_id_counters sic
                    ON sic.sample_type_id = st.id
                WHERE sic.sample_type_id IS NULL
                ON CONFLICT (sample_type_id)
                DO NOTHING;
                """
            )

            inserted_count = cur.rowcount

            # Retrieve current counter status for verification.
            cur.execute(
                """
                SELECT
                    st.id,
                    st.code,
                    st.name,
                    st.active,
                    sic.last_number
                FROM sample_types st
                LEFT JOIN sample_id_counters sic
                    ON sic.sample_type_id = st.id
                ORDER BY st.id;
                """
            )

            rows = cur.fetchall()

    print(
        f"Sample type counter sync complete. "
        f"Created {inserted_count} missing counter row(s)."
    )

    print("\nSample type counters:")

    for row in rows:
        print(
            f"{row['code']} - {row['name']}"
            f" | active: {row['active']}"
            f" | last number: {row['last_number']}"
        )


if __name__ == "__main__":
    sync_sample_type_counters()