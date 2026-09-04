from db.connection import get_connection


def get_sample_types():
    query = """
        SELECT
            id,
            code,
            name,
            is_bookable,
            requires_approval
        FROM sample_types
        WHERE active = TRUE
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_sample_locations():
    query = """
        SELECT
            id,
            code,
            name
        FROM sample_locations
        WHERE active = TRUE
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_categories():
    query = """
        SELECT
            category_code,
            category_name
        FROM category_master
        WHERE active = TRUE
        ORDER BY category_name;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

def get_samples():
    query = """
        SELECT
            sm.id,
            sm.sample_id,
            sm.sample_name,
            sm.category_code,

            cm.category_name,

            sm.sample_type_id,
            st.code AS sample_type_code,
            st.name AS sample_type_name,
            st.is_bookable,
            st.requires_approval,

            sm.origin_location_id,
            ol.code AS origin_location_code,
            ol.name AS origin_location_name,

            sm.current_location_id,
            cl.code AS current_location_code,
            cl.name AS current_location_name,

            sm.source,
            sm.received_date,

            sm.current_holder,
            sm.current_holder_team,

            sm.condition,
            sm.asset_state,

            sm.usage_count,
            sm.last_inspection_date,

            sm.notes,

            sm.created_at,
            sm.updated_at

        FROM sample_master sm

        JOIN sample_types st
            ON st.id = sm.sample_type_id

        JOIN sample_locations ol
            ON ol.id = sm.origin_location_id

        LEFT JOIN sample_locations cl
            ON cl.id = sm.current_location_id

        LEFT JOIN category_master cm
            ON cm.category_code = sm.category_code

        ORDER BY
            sm.created_at DESC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_sample_by_record_id(sample_record_id):
    query = """
        SELECT
            sm.id,
            sm.sample_id,
            sm.sample_name,
            sm.category_code,

            cm.category_name,

            sm.sample_type_id,
            st.code AS sample_type_code,
            st.name AS sample_type_name,
            st.is_bookable,
            st.requires_approval,

            sm.origin_location_id,
            ol.code AS origin_location_code,
            ol.name AS origin_location_name,

            sm.current_location_id,
            cl.code AS current_location_code,
            cl.name AS current_location_name,

            sm.source,
            sm.received_date,

            sm.current_holder,
            sm.current_holder_team,

            sm.condition,
            sm.asset_state,

            sm.usage_count,
            sm.last_inspection_date,

            sm.notes,
            sm.created_at,
            sm.updated_at

        FROM sample_master sm

        JOIN sample_types st
            ON st.id = sm.sample_type_id

        JOIN sample_locations ol
            ON ol.id = sm.origin_location_id

        LEFT JOIN sample_locations cl
            ON cl.id = sm.current_location_id

        LEFT JOIN category_master cm
            ON cm.category_code = sm.category_code

        WHERE sm.id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (sample_record_id,),
            )

            return cur.fetchone()


def get_sample_events(sample_record_id):
    query = """
        SELECT
            se.id,
            se.event_type,
            se.event_date,
            se.title,
            se.details,
            se.actor,
            se.team,

            pl.code AS previous_location_code,
            pl.name AS previous_location_name,

            nl.code AS new_location_code,
            nl.name AS new_location_name

        FROM sample_events se

        LEFT JOIN sample_locations pl
            ON pl.id = se.previous_location_id

        LEFT JOIN sample_locations nl
            ON nl.id = se.new_location_id

        WHERE se.sample_record_id = %s

        ORDER BY
            se.event_date DESC,
            se.created_at DESC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (sample_record_id,),
            )

            return cur.fetchall()
            

def create_samples(
    *,
    sample_name,
    category_code,
    sample_type_id,
    sample_type_code,
    location_id,
    location_code,
    source,
    received_date,
    condition,
    notes,
    quantity,
):
    if quantity < 1:
        raise ValueError(
            "Quantity must be at least 1."
        )

    created_samples = []

    with get_connection() as conn:
        with conn.cursor() as cur:

            # -------------------------------------------------
            # Lock the counter for this sample type.
            #
            # This prevents two users from generating the
            # same sample number at the same time.
            # -------------------------------------------------

            cur.execute(
                """
                SELECT last_number
                FROM sample_id_counters
                WHERE sample_type_id = %s
                FOR UPDATE;
                """,
                (sample_type_id,),
            )

            counter = cur.fetchone()

            if counter is None:
                raise ValueError(
                    f"No sample ID counter exists for "
                    f"sample type {sample_type_code}."
                )

            current_number = counter[
                "last_number"
            ]

            new_last_number = (
                current_number + quantity
            )

            # -------------------------------------------------
            # Reserve the required sequence numbers.
            # -------------------------------------------------

            cur.execute(
                """
                UPDATE sample_id_counters
                SET
                    last_number = %s,
                    updated_at = NOW()
                WHERE sample_type_id = %s;
                """,
                (
                    new_last_number,
                    sample_type_id,
                ),
            )

            # -------------------------------------------------
            # Create one physical asset record per sample.
            # -------------------------------------------------

            for batch_index, number in enumerate(
                range(
                    current_number + 1,
                    new_last_number + 1,
                ),
                start=1,
            ):
                sample_id = (
                    f"{sample_type_code}-"
                    f"{number:05d}"
                )

                numbered_sample_name = (
                    f"{sample_name} - "
                    f"{batch_index:02d}"
                )

                cur.execute(
                    """
                    INSERT INTO sample_master (
                        sample_id,
                        sample_name,
                        category_code,
                        sample_type_id,
                        origin_location_id,
                        current_location_id,
                        source,
                        received_date,
                        current_holder,
                        current_holder_team,
                        condition,
                        asset_state,
                        usage_count,
                        last_inspection_date,
                        notes
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        sample_id,
                        sample_name;
                    """,
                    (
                        sample_id,
                        numbered_sample_name,
                        category_code,
                        sample_type_id,
                        location_id,
                        location_id,
                        source,
                        received_date,
                        "Storage",
                        "Operations",
                        condition,
                        "Active",
                        0,
                        received_date,
                        notes,
                    ),
                )

                created_sample = cur.fetchone()

                # ---------------------------------------------
                # Create the initial lifecycle event.
                #
                # IMPORTANT:
                # Use the internal UUID from sample_master.id,
                # NOT the human-readable sample_id.
                # ---------------------------------------------

                cur.execute(
                    """
                    INSERT INTO sample_events (
                        sample_record_id,
                        event_type,
                        title,
                        details,
                        new_location_id
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        created_sample["id"],
                        "SAMPLE_RECEIVED",
                        f"Received from {source}",
                        (
                            f"Sample created in NexaFlow. "
                            f"Initial location: "
                            f"{location_code}."
                        ),
                        location_id,
                    ),
                )

                created_samples.append(
                    created_sample
                )

    return created_samples


def update_sample_details(
    *,
    sample_record_id,
    sample_name,
    sample_type_id,
    category_code,
    source,
    notes,
):
    query = """
        UPDATE sample_master
        SET
            sample_name = %s,
            sample_type_id = %s,
            category_code = %s,
            source = %s,
            notes = %s,
            updated_at = NOW()
        WHERE id = %s
        RETURNING
            id,
            sample_id,
            sample_name;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    sample_name,
                    sample_type_id,
                    category_code,
                    source,
                    notes,
                    sample_record_id,
                ),
            )

            updated_sample = cur.fetchone()

            if updated_sample is None:
                raise ValueError(
                    "Sample could not be found."
                )

            return updated_sample