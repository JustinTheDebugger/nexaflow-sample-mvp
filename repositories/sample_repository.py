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


def get_sample_products(sample_record_id):
    query = """
        SELECT
            sp.id,
            sp.product_code,
            sp.relationship_type,
            sp.created_at
        FROM sample_products sp
        WHERE sp.sample_record_id = %s
        ORDER BY
            sp.relationship_type,
            sp.product_code;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (sample_record_id,),
            )
            return cur.fetchall()


def link_sample_product(
    *,
    sample_record_id,
    product_code,
    relationship_type="Primary",
):
    query = """
        INSERT INTO sample_products (
            sample_record_id,
            product_code,
            relationship_type
        )
        VALUES (
            %s,
            %s,
            %s
        )
        ON CONFLICT (
            sample_record_id,
            product_code
        )
        DO UPDATE SET
            relationship_type = EXCLUDED.relationship_type
        RETURNING
            id,
            product_code,
            relationship_type;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    sample_record_id,
                    product_code,
                    relationship_type,
                ),
            )

            return cur.fetchone()


def unlink_sample_product(
    *,
    sample_record_id,
    product_code,
):
    query = """
        DELETE FROM sample_products
        WHERE sample_record_id = %s
          AND product_code = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    sample_record_id,
                    product_code,
                ),
            )


def get_active_products(
    category_code=None,
):
    if category_code:
        query = """
            SELECT
                p.product_code,
                p.product_name,
                p.range_name,

                pm.category_code,

                p.status

            FROM products p

            LEFT JOIN product_master pm
                ON pm.product_code = p.product_code

            WHERE p.status = 'ACTIVE'
              AND pm.category_code = %s

            ORDER BY
                p.product_name;
        """

        params = (
            category_code,
        )

    else:
        query = """
            SELECT
                p.product_code,
                p.product_name,
                p.range_name,

                pm.category_code,

                p.status

            FROM products p

            LEFT JOIN product_master pm
                ON pm.product_code = p.product_code

            WHERE p.status = 'ACTIVE'

            ORDER BY
                p.product_name;
        """

        params = ()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                params,
            )

            return cur.fetchall()


def get_sample_products(sample_record_id):
    query = """
        SELECT
            sp.id,
            sp.product_code,
            sp.relationship_type,
            sp.created_at,

            p.product_name,
            p.range_name

        FROM sample_products sp

        LEFT JOIN products p
            ON p.product_code = sp.product_code

        WHERE sp.sample_record_id = %s

        ORDER BY
            sp.relationship_type,
            p.product_name,
            sp.product_code;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (sample_record_id,),
            )
            return cur.fetchall()
        

def get_bookable_samples():
    query = """
        SELECT
            sm.id,
            sm.sample_id,
            sm.sample_name,
            sm.category_code,
            cm.category_name,

            st.code AS sample_type_code,
            st.name AS sample_type_name,
            st.is_bookable,
            st.requires_approval,

            cl.code AS current_location_code,
            cl.name AS current_location_name,

            sm.asset_state,
            sm.condition,
            sm.current_holder

        FROM sample_master sm

        JOIN sample_types st
            ON st.id = sm.sample_type_id

        LEFT JOIN sample_locations cl
            ON cl.id = sm.current_location_id

        LEFT JOIN category_master cm
            ON cm.category_code = sm.category_code

        WHERE st.is_bookable = TRUE
        AND sm.asset_state = 'Active'

        ORDER BY
            sm.sample_name,
            sm.sample_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
            

def is_sample_available(
    *,
    sample_record_id,
    start_date,
    end_date,
):
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM sample_bookings sb
            WHERE sb.sample_record_id = %s

              AND sb.booking_status IN (
                  'Reserved',
                  'Pending Approval',
                  'Approved'
              )

              AND sb.start_date <= %s
              AND sb.end_date >= %s
        ) AS has_conflict;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    sample_record_id,
                    end_date,
                    start_date,
                ),
            )

            row = cur.fetchone()

    return not row["has_conflict"]


def get_available_samples(
    *,
    start_date,
    end_date,
):
    samples = get_bookable_samples()

    available = []

    for sample in samples:
        if is_sample_available(
            sample_record_id=sample["id"],
            start_date=start_date,
            end_date=end_date,
        ):
            available.append(sample)

    return available

def create_sample_booking(
    *,
    sample_record_id,
    booked_by,
    team,
    purpose,
    start_date,
    end_date,
    notes,
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    sm.sample_id,
                    sm.sample_name,
                    st.requires_approval

                FROM sample_master sm

                JOIN sample_types st
                    ON st.id = sm.sample_type_id

                WHERE sm.id = %s
                FOR UPDATE;
                """,
                (sample_record_id,),
            )

            sample = cur.fetchone()

            if sample is None:
                raise ValueError(
                    "Sample could not be found."
                )

            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM sample_bookings
                    WHERE sample_record_id = %s

                      AND booking_status IN (
                          'Reserved',
                          'Pending Approval',
                          'Approved'
                      )

                      AND start_date <= %s
                      AND end_date >= %s
                ) AS has_conflict;
                """,
                (
                    sample_record_id,
                    end_date,
                    start_date,
                ),
            )

            conflict = cur.fetchone()

            if conflict["has_conflict"]:
                raise ValueError(
                    "This sample is no longer available "
                    "for the selected dates."
                )

            booking_status = "Reserved"

            cur.execute(
                """
                INSERT INTO sample_bookings (
                    sample_record_id,
                    booked_by,
                    team,
                    purpose,
                    start_date,
                    end_date,
                    booking_status,
                    approval_required,
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
                    %s
                )
                RETURNING
                    id,
                    sample_record_id,
                    booking_status;
                """,
                (
                    sample_record_id,
                    booked_by,
                    team,
                    purpose,
                    start_date,
                    end_date,
                    booking_status,
                    False,
                    notes,
                ),
            )

            booking = cur.fetchone()

            cur.execute(
                """
                INSERT INTO sample_events (
                    sample_record_id,
                    event_type,
                    title,
                    details
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    sample_record_id,
                    "BOOKING_CREATED",
                    "Booking Created",
                    (
                        f"Booked by {booked_by} "
                        f"({team}) for {purpose}. "
                        f"{start_date:%d %b %Y} "
                        f"to {end_date:%d %b %Y}. "
                        f"Status: {booking_status}."
                    ),
                ),
            )

            return booking


def get_bookings():
    query = """
        SELECT
            sb.id,
            sb.sample_record_id,
            sb.booked_by,
            sb.team,
            sb.purpose,
            sb.start_date,
            sb.end_date,
            sb.booking_status,
            sb.notes,
            sb.created_at,

            sm.sample_id,
            sm.sample_name,

            sl.code AS location_code,
            sl.name AS location_name

        FROM sample_bookings sb

        JOIN sample_master sm
            ON sm.id = sb.sample_record_id

        LEFT JOIN sample_locations sl
            ON sl.id = sm.current_location_id

        ORDER BY
            sb.start_date,
            sb.created_at;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def cancel_booking(
    *,
    booking_id,
    cancelled_by,
    reason,
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE sample_bookings
                SET
                    booking_status = 'Cancelled',
                    updated_at = NOW()
                WHERE id = %s
                  AND booking_status = 'Reserved'
                RETURNING
                    id,
                    sample_record_id;
                """,
                (booking_id,),
            )

            booking = cur.fetchone()

            if booking is None:
                raise ValueError(
                    "Booking could not be cancelled."
                )

            cur.execute(
                """
                INSERT INTO sample_events (
                    sample_record_id,
                    event_type,
                    title,
                    details
                )
                VALUES (
                    %s,
                    'BOOKING_CANCELLED',
                    'Booking Cancelled',
                    %s
                );
                """,
                (
                    booking["sample_record_id"],
                    (
                        f"Cancelled by {cancelled_by}. "
                        f"Reason: {reason}"
                    ),
                ),
            )

            return booking

def create_sample_request(
    *,
    product_code,
    requested_sample_name,
    category_code,
    quantity_required,
    required_from,
    required_until,
    requested_by,
    requester_email,
    team,
    purpose,
    request_notes,
):
    query = """
        INSERT INTO sample_requests (
            product_code,
            requested_sample_name,
            category_code,
            quantity_required,
            required_from,
            required_until,
            requested_by,
            requester_email,
            team,
            purpose,
            request_notes
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s
        )
        RETURNING
            id,
            request_status;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    product_code,
                    requested_sample_name,
                    category_code,
                    quantity_required,
                    required_from,
                    required_until,
                    requested_by,
                    requester_email,
                    team,
                    purpose,
                    request_notes,
                ),
            )

            return cur.fetchone()


def get_sample_requests():
    query = """
        SELECT
            sr.*,
            p.product_name

        FROM sample_requests sr

        LEFT JOIN products p
            ON p.product_code = sr.product_code

        ORDER BY
            CASE
                WHEN sr.request_status = 'Pending Review'
                THEN 0
                ELSE 1
            END,
            sr.created_at DESC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def approve_sample_request(
    *,
    request_id,
    reviewed_by,
    operations_email,
    manager_notes,
):
    query = """
        UPDATE sample_requests
        SET
            request_status = 'Approved',
            reviewed_by = %s,
            reviewed_at = NOW(),
            operations_email = %s,
            manager_notes = %s,
            rejection_reason = NULL,
            updated_at = NOW()
        WHERE id = %s
          AND request_status = 'Pending Review'
        RETURNING *;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    reviewed_by,
                    operations_email,
                    manager_notes,
                    request_id,
                ),
            )

            request = cur.fetchone()

            if request is None:
                raise ValueError(
                    "Request could not be approved."
                )

            return request


def reject_sample_request(
    *,
    request_id,
    reviewed_by,
    rejection_reason,
):
    query = """
        UPDATE sample_requests
        SET
            request_status = 'Rejected',
            reviewed_by = %s,
            reviewed_at = NOW(),
            rejection_reason = %s,
            updated_at = NOW()
        WHERE id = %s
          AND request_status = 'Pending Review'
        RETURNING *;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    reviewed_by,
                    rejection_reason,
                    request_id,
                ),
            )

            request = cur.fetchone()

            if request is None:
                raise ValueError(
                    "Request could not be rejected."
                )

            return request

def search_available_samples(
    *,
    search_text,
    start_date,
    end_date,
    limit=25,
):
    search_pattern = f"%{search_text.strip()}%"

    query = """
        SELECT DISTINCT
            sm.id AS sample_record_id,
            sm.sample_id,
            sm.sample_name,
            sm.asset_state,

            st.code AS sample_type_code,
            st.name AS sample_type_name,

            sl.code AS location_code,
            sl.name AS location_name

        FROM sample_master sm

        JOIN sample_types st
            ON st.id = sm.sample_type_id

        LEFT JOIN sample_locations sl
            ON sl.id = sm.current_location_id

        LEFT JOIN sample_products sp
            ON sp.sample_record_id = sm.id

        WHERE sm.asset_state = 'Active'

          AND st.is_bookable = TRUE

          AND (
                sm.sample_id ILIKE %s
                OR sm.sample_name ILIKE %s
                OR sp.product_code ILIKE %s
          )

          AND NOT EXISTS (
              SELECT 1

              FROM sample_bookings sb

              WHERE sb.sample_record_id = sm.id

                AND sb.booking_status = 'Reserved'

                AND sb.start_date <= %s

                AND sb.end_date >= %s
          )

        ORDER BY
            sm.sample_name,
            sm.sample_id

        LIMIT %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    end_date,
                    start_date,
                    limit,
                ),
            )

            return cur.fetchall()

def create_sample_bookings(
    *,
    sample_record_ids,
    booked_by,
    team,
    purpose,
    start_date,
    end_date,
    notes,
):
    if not sample_record_ids:
        raise ValueError(
            "At least one sample must be selected."
        )

    if end_date < start_date:
        raise ValueError(
            "Required Until cannot be before Required From."
        )

    created_bookings = []

    with get_connection() as conn:
        with conn.cursor() as cur:

            # -------------------------------------------------
            # Lock all selected physical sample records
            # -------------------------------------------------

            cur.execute(
                """
                SELECT
                    sm.id,
                    sm.sample_id,
                    sm.sample_name,
                    sm.asset_state,
                    st.is_bookable

                FROM sample_master sm

                JOIN sample_types st
                    ON st.id = sm.sample_type_id

                WHERE sm.id = ANY(%s::uuid[])

                FOR UPDATE;
                """,
                (sample_record_ids,),
            )

            samples = cur.fetchall()

            if len(samples) != len(sample_record_ids):
                raise ValueError(
                    "One or more selected samples "
                    "could not be found."
                )

            # -------------------------------------------------
            # Validate sample state
            # -------------------------------------------------

            for sample in samples:
                if sample["asset_state"] != "Active":
                    raise ValueError(
                        (
                            f"{sample['sample_name']} "
                            f"({sample['sample_id']}) "
                            f"is no longer active."
                        )
                    )

                if not sample["is_bookable"]:
                    raise ValueError(
                        (
                            f"{sample['sample_name']} "
                            f"({sample['sample_id']}) "
                            f"is not bookable."
                        )
                    )

            # -------------------------------------------------
            # Recheck date availability inside transaction
            # -------------------------------------------------

            cur.execute(
                """
                SELECT
                    sb.sample_record_id,
                    sm.sample_id,
                    sm.sample_name

                FROM sample_bookings sb

                JOIN sample_master sm
                    ON sm.id = sb.sample_record_id

                WHERE sb.sample_record_id
                    = ANY(%s::uuid[])

                  AND sb.booking_status = 'Reserved'

                  AND sb.start_date <= %s

                  AND sb.end_date >= %s;
                """,
                (
                    sample_record_ids,
                    end_date,
                    start_date,
                ),
            )

            conflicts = cur.fetchall()

            if conflicts:
                conflict_names = ", ".join(
                    (
                        f"{row['sample_name']} "
                        f"({row['sample_id']})"
                    )
                    for row in conflicts
                )

                raise ValueError(
                    (
                        "The following sample(s) are no longer "
                        f"available: {conflict_names}"
                    )
                )

            # -------------------------------------------------
            # Create bookings
            # -------------------------------------------------

            for sample in samples:
                cur.execute(
                    """
                    INSERT INTO sample_bookings (
                        sample_record_id,
                        booked_by,
                        team,
                        purpose,
                        start_date,
                        end_date,
                        booking_status,
                        approval_required,
                        notes
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'Reserved',
                        FALSE,
                        %s
                    )
                    RETURNING
                        id,
                        sample_record_id,
                        booking_status;
                    """,
                    (
                        sample["id"],
                        booked_by,
                        team,
                        purpose,
                        start_date,
                        end_date,
                        notes,
                    ),
                )

                booking = cur.fetchone()

                created_bookings.append(
                    booking
                )

                # ---------------------------------------------
                # Lifecycle event
                # ---------------------------------------------

                cur.execute(
                    """
                    INSERT INTO sample_events (
                        sample_record_id,
                        event_type,
                        title,
                        details
                    )
                    VALUES (
                        %s,
                        'BOOKING_CREATED',
                        'Sample Booked',
                        %s
                    );
                    """,
                    (
                        sample["id"],
                        (
                            f"Booked by {booked_by} "
                            f"from {start_date:%d %b %Y} "
                            f"to {end_date:%d %b %Y}. "
                            f"Purpose: {purpose}."
                        ),
                    ),
                )

        conn.commit()

    return created_bookings