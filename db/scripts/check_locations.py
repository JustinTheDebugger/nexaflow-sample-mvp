from db.connection import get_connection


with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                code,
                name
            FROM sample_locations
            WHERE active = TRUE
            ORDER BY id;
            """
        )

        locations = cur.fetchall()


for location in locations:
    print(
        location["code"],
        "-",
        location["name"],
    )