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
          AND sm.condition = 'Good'
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
            # Lock selected physical samples
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
            # Validate physical samples
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
            # Final availability check
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
            # Create ONE booking header
            # -------------------------------------------------

            cur.execute(
                """
                INSERT INTO sample_booking_groups (
                    booked_by,
                    team,
                    purpose,
                    start_date,
                    end_date,
                    notes,
                    booking_status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'Reserved'
                )
                RETURNING
                    id,
                    booking_number;
                """,
                (
                    booked_by,
                    team,
                    purpose,
                    start_date,
                    end_date,
                    notes,
                ),
            )

            booking_group = cur.fetchone()

            booking_group_id = booking_group["id"]
            booking_number = booking_group[
                "booking_number"
            ]

            # -------------------------------------------------
            # Create individual sample booking items
            # -------------------------------------------------

            for sample in samples:

                cur.execute(
                    """
                    INSERT INTO sample_bookings (
                        booking_group_id,
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
                        'Reserved',
                        FALSE,
                        %s
                    )
                    RETURNING
                        id,
                        booking_group_id,
                        sample_record_id,
                        booking_status;
                    """,
                    (
                        booking_group_id,
                        sample["id"],
                        booked_by,
                        team,
                        purpose,
                        start_date,
                        end_date,
                        notes,
                    ),
                )

                created_booking = cur.fetchone()

                created_bookings.append(
                    created_booking
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
                            f"{booking_number}. "
                            f"Booked by {booked_by} "
                            f"from "
                            f"{start_date:%d %b %Y} "
                            f"to "
                            f"{end_date:%d %b %Y}. "
                            f"Purpose: {purpose}."
                        ),
                    ),
                )

        conn.commit()

    return {
        "booking_group_id": booking_group_id,
        "booking_number": booking_number,
        "bookings": created_bookings,
    }

def get_booking_groups(
    *,
    status=None,
    upcoming_only=False,
):
    query = """
        SELECT
            sbg.id AS booking_group_id,
            sbg.booking_number,
            sbg.booked_by,
            sbg.team,
            sbg.purpose,
            sbg.start_date,
            sbg.end_date,
            sbg.notes,
            sbg.booking_status,
            sbg.created_at,

            COUNT(sb.id) AS sample_count

        FROM sample_booking_groups sbg

        LEFT JOIN sample_bookings sb
            ON sb.booking_group_id = sbg.id
    """

    params = []
    conditions = []

    if status:
        conditions.append(
            "sbg.booking_status = %s"
        )
        params.append(status)

    if upcoming_only:
        conditions.append(
            "sbg.end_date >= CURRENT_DATE"
        )

    if conditions:
        query += "\nWHERE "
        query += " AND ".join(conditions)

    query += """
        GROUP BY
            sbg.id,
            sbg.booking_number,
            sbg.booked_by,
            sbg.team,
            sbg.purpose,
            sbg.start_date,
            sbg.end_date,
            sbg.notes,
            sbg.booking_status,
            sbg.created_at

        ORDER BY
            sbg.start_date,
            sbg.booking_number;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                params,
            )

            return cur.fetchall()


def get_booking_group_details(
    booking_group_id,
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            # -----------------------------------------
            # Booking header
            # -----------------------------------------

            cur.execute(
                """
                SELECT
                    id AS booking_group_id,
                    booking_number,
                    booked_by,
                    team,
                    purpose,
                    start_date,
                    end_date,
                    notes,
                    booking_status,
                    created_at

                FROM sample_booking_groups

                WHERE id = %s;
                """,
                (booking_group_id,),
            )

            booking = cur.fetchone()

            if not booking:
                return None

            # -----------------------------------------
            # Physical samples
            # -----------------------------------------

            cur.execute(
                """
                SELECT
                    sb.id AS booking_item_id,
                    sb.sample_record_id,
                    sb.booking_status,

                    sm.sample_id,
                    sm.sample_name,

                    st.code AS sample_type_code,
                    st.name AS sample_type_name,

                    sl.code AS location_code,
                    sl.name AS location_name

                FROM sample_bookings sb

                JOIN sample_master sm
                    ON sm.id = sb.sample_record_id

                JOIN sample_types st
                    ON st.id = sm.sample_type_id

                LEFT JOIN sample_locations sl
                    ON sl.id = sm.current_location_id

                WHERE sb.booking_group_id = %s

                ORDER BY
                    sm.sample_name,
                    sm.sample_id;
                """,
                (booking_group_id,),
            )

            samples = cur.fetchall()

            return {
                "booking": booking,
                "samples": samples,
            }

def cancel_booking_group(
    *,
    booking_group_id,
    cancelled_by,
    reason,
):
    if not cancelled_by.strip():
        raise ValueError(
            "Cancelled By is required."
        )

    if not reason.strip():
        raise ValueError(
            "Cancellation reason is required."
        )

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    booking_number,
                    booking_status

                FROM sample_booking_groups

                WHERE id = %s

                FOR UPDATE;
                """,
                (booking_group_id,),
            )

            booking = cur.fetchone()

            if not booking:
                raise ValueError(
                    "Booking could not be found."
                )

            if booking["booking_status"] != "Reserved":
                raise ValueError(
                    (
                        f"{booking['booking_number']} "
                        "is no longer an active booking."
                    )
                )

            cur.execute(
                """
                SELECT
                    sb.sample_record_id,
                    sm.sample_id,
                    sm.sample_name

                FROM sample_bookings sb

                JOIN sample_master sm
                    ON sm.id = sb.sample_record_id

                WHERE sb.booking_group_id = %s
                  AND sb.booking_status = 'Reserved';
                """,
                (booking_group_id,),
            )

            samples = cur.fetchall()

            cur.execute(
                """
                UPDATE sample_booking_groups

                SET
                    booking_status = 'Cancelled',
                    cancelled_by = %s,
                    cancelled_at = NOW(),
                    cancellation_reason = %s,
                    updated_at = NOW()

                WHERE id = %s;
                """,
                (
                    cancelled_by.strip(),
                    reason.strip(),
                    booking_group_id,
                ),
            )

            cur.execute(
                """
                UPDATE sample_bookings

                SET booking_status = 'Cancelled'

                WHERE booking_group_id = %s
                  AND booking_status = 'Reserved';
                """,
                (booking_group_id,),
            )

            for sample in samples:
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
                        sample["sample_record_id"],
                        (
                            f"{booking['booking_number']} "
                            f"cancelled by "
                            f"{cancelled_by.strip()}. "
                            f"Reason: {reason.strip()}."
                        ),
                    ),
                )

        conn.commit()

    return booking["booking_number"]


# RETURN SAMPLE FUNCTIONS

def get_booking_return_checks(
    booking_group_id,
):
    query = """
        SELECT
            src.id,
            src.booking_group_id,
            src.booking_item_id,
            src.sample_record_id,
            src.return_status,
            src.condition_on_return,
            src.damage_reported,
            src.damage_details,
            src.incomplete_reported,
            src.missing_details,
            src.checked_by,
            src.checked_at,
            src.notes,
            sm.sample_id,
            sm.sample_name

        FROM sample_return_checks src

        JOIN sample_master sm
            ON sm.id = src.sample_record_id

        WHERE src.booking_group_id = %s

        ORDER BY
            sm.sample_name,
            sm.sample_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (booking_group_id,),
            )
            return cur.fetchall()

def save_sample_return_check(
    *,
    booking_group_id,
    booking_item_id,
    sample_record_id,
    return_status,
    checked_by,
    condition_on_return=None,
    damage_details=None,
    missing_details=None,
    notes=None,
):

    allowed_statuses = {
        "Good",
        "Damaged",
        "Incomplete",
        "Missing",
    }

    if return_status not in allowed_statuses:
        raise ValueError(
            "Invalid return status."
        )

    if not checked_by or not checked_by.strip():
        raise ValueError(
            "Checked By is required."
        )

    checked_by = checked_by.strip()

    clean_notes = (
        notes.strip()
        if notes and notes.strip()
        else None
    )

    damage_reported = (
        return_status == "Damaged"
    )

    incomplete_reported = (
        return_status == "Incomplete"
    )

    with get_connection() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # Validate booking item
            # -------------------------------------------------

            cur.execute(
                """
                SELECT
                    sb.id,
                    sb.booking_group_id,
                    sb.sample_record_id,
                    sb.booking_status
                FROM sample_bookings sb
                WHERE sb.id = %s
                  AND sb.booking_group_id = %s
                  AND sb.sample_record_id = %s
                FOR UPDATE;
                """,
                (
                    booking_item_id,
                    booking_group_id,
                    sample_record_id,
                ),
            )

            booking_item = cur.fetchone()

            if not booking_item:
                raise ValueError(
                    "Booking item could not be found."
                )

            if (
                booking_item["booking_status"]
                != "Reserved"
            ):
                raise ValueError(
                    "This booking item is not Reserved."
                )

            # -------------------------------------------------
            # Save / update inspection
            # -------------------------------------------------

            cur.execute(
                """
                INSERT INTO sample_return_checks (
                    booking_group_id,
                    booking_item_id,
                    sample_record_id,
                    return_status,
                    condition_on_return,
                    damage_reported,
                    damage_details,
                    incomplete_reported,
                    missing_details,
                    checked_by,
                    checked_at,
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
                    NOW(),
                    %s
                )
                ON CONFLICT (booking_item_id)
                DO UPDATE SET
                    return_status =
                        EXCLUDED.return_status,
                    condition_on_return =
                        EXCLUDED.condition_on_return,
                    damage_reported =
                        EXCLUDED.damage_reported,
                    damage_details =
                        EXCLUDED.damage_details,
                    incomplete_reported =
                        EXCLUDED.incomplete_reported,
                    missing_details =
                        EXCLUDED.missing_details,
                    checked_by =
                        EXCLUDED.checked_by,
                    checked_at = NOW(),
                    notes =
                        EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id;
                """,
                (
                    booking_group_id,
                    booking_item_id,
                    sample_record_id,
                    return_status,
                    condition_on_return,
                    damage_reported,
                    None,
                    incomplete_reported,
                    None,
                    checked_by,
                    clean_notes,
                ),
            )

            return_check = cur.fetchone()

            # -------------------------------------------------
            # Determine return outcome
            # -------------------------------------------------

            if return_status == "Good":

                event_type = "SAMPLE_RETURNED"
                title = "Sample Returned"

                details = (
                    f"Return inspection completed by "
                    f"{checked_by}. "
                    f"Condition: Good."
                )

                new_condition = "Good"
                new_asset_state = "Active"

            elif return_status == "Damaged":

                event_type = "DAMAGE_REPORTED"
                title = "Damage Reported"

                details = (
                    f"Return inspection completed by "
                    f"{checked_by}. "
                    f"Condition: Damaged."
                )

                new_condition = "Damaged"
                new_asset_state = "Damaged"

            elif return_status == "Incomplete":

                event_type = "INCOMPLETE_RETURN"
                title = "Incomplete Return"

                details = (
                    f"Return inspection completed by "
                    f"{checked_by}. "
                    f"Condition: Incomplete."
                )

                new_condition = "Incomplete"
                new_asset_state = "Inactive"

            elif return_status == "Missing":

                event_type = "SAMPLE_MISSING"
                title = "Sample Missing"

                details = (
                    f"Sample reported missing during "
                    f"return inspection by "
                    f"{checked_by}."
                )

                new_condition = "Missing"
                new_asset_state = "Lost"

            # -------------------------------------------------
            # Append optional notes
            # -------------------------------------------------

            if clean_notes:
                details += (
                    f" Notes: {clean_notes}"
                )

            # -------------------------------------------------
            # Record sample event
            # -------------------------------------------------

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
                    event_type,
                    title,
                    details,
                ),
            )

            # -------------------------------------------------
            # Update current sample condition/state
            # -------------------------------------------------

            cur.execute(
                """
                UPDATE sample_master
                SET
                    condition = %s,
                    asset_state = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    new_condition,
                    new_asset_state,
                    sample_record_id,
                ),
            )

        conn.commit()

    return {
        "return_check_id": return_check["id"],
        "return_status": return_status,
        "condition": new_condition,
        "asset_state": new_asset_state,
    }