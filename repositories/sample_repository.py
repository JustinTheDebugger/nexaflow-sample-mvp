from db.connection import get_connection


# =============================================================================
# REFERENCE DATA
# =============================================================================

def get_sample_types():
    """
    Return all active sample types and their booking and approval rules.
    """
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
    """
    Return all active physical locations available for samples.
    """
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
    """
    Return all active product categories used to classify samples.
    """
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

# =============================================================================
# SAMPLE MASTER & LIFECYCLE
# =============================================================================

def get_samples():
    """
    Return the sample register with joined type, category, location, holder, condition,
    and lifecycle-state details.
    """
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
    """
    Return one sample by its internal record ID with joined type, category, and
    location details.
    """
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
    """
    Return the lifecycle event history for one physical sample, newest first.
    """
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
    """
    Create one or more physical samples, reserve sequential sample IDs safely, and
    record each sample's initial lifecycle event.
    """
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
    """
    Update editable master-data fields for an existing physical sample.
    """
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


def link_sample_product(
    *,
    sample_record_id,
    product_code,
    relationship_type="Primary",
):
    """
    Create or update a product relationship for a physical sample.
    """
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
    """
    Remove a product relationship from a physical sample.
    """
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
    """
    Return active products, optionally filtered by category code, for sample-product
    linking.
    """
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


# =============================================================================
# SAMPLE ↔ PRODUCT LINKS
# =============================================================================

def get_sample_products(sample_record_id):
    """
    Return products linked to a sample, including relationship type and product display
    information.
    """
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
        

# =============================================================================
# SAMPLE AVAILABILITY
# =============================================================================

def get_bookable_samples():
    """
    Return active samples whose sample type is configured as bookable.
    """
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
    """
    Check whether a sample has a conflicting active booking in the requested date
    range.
    """
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
    """
    Return bookable samples with no active booking conflict for the requested date
    range.
    """
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

# =============================================================================
# BOOKINGS & REQUESTS
# =============================================================================

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
    """
    Create a booking for one physical sample after locking it and performing a final
    conflict check.
    """
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

            previous_location_id = (
                sample["current_location_id"]
            )

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
    """
    Return individual sample bookings with sample and current-location details.
    """
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
    """
    Create a new sample request for review and return its ID and initial status.
    """
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
    """
    Return sample requests with linked product names, prioritising requests pending
    review.
    """
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
    """
    Approve a pending sample request and record its review information.
    """
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
    """
    Reject a pending sample request and record the reviewer and rejection reason.
    """
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
    """
    Search active, good-condition, bookable samples while excluding booking conflicts
    for the requested dates.
    """
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
    """
    Create one booking group for multiple physical samples atomically, with validation
    and lifecycle events.
    """
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
    """
    Return booking-group headers and sample counts, optionally filtered by status or
    upcoming dates.
    """
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
    """
    Return a booking-group header together with all physical samples in the booking.
    """
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
    """
    Cancel an active booking group and its reserved items, then record sample lifecycle
    events.
    """
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


# =============================================================================
# SAMPLE RETURNS
# =============================================================================

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
        "Not Returned",
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
                    incomplete_reported,
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
                    NOW(),
                    %s
                )
                ON CONFLICT (
                    booking_item_id
                )
                DO UPDATE SET
                    return_status =
                        EXCLUDED.return_status,
                    condition_on_return =
                        EXCLUDED.condition_on_return,
                    damage_reported =
                        EXCLUDED.damage_reported,
                    incomplete_reported =
                        EXCLUDED.incomplete_reported,
                    checked_by =
                        EXCLUDED.checked_by,
                    checked_at = NOW(),
                    notes =
                        EXCLUDED.notes,
                    updated_at = NOW();
                """,
                (
                    booking_group_id,
                    booking_item["id"],
                    sample_record_id,
                    return_status,
                    return_status,
                    damage_reported,
                    incomplete_reported,
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

                return_location_id = submitted.get(
                    "return_location_id"
                )

                if not return_location_id:
                    raise ValueError(
                        "Return location is required "
                        "for a Good sample."
                    )

                new_location_id = return_location_id


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
                new_location_id = hold_location_id


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
                new_location_id = hold_location_id


            elif return_status == "Not Returned":

                event_type = "SAMPLE_NOT_RETURNED"
                title = "Sample Not Returned"

                details = (
                    "Sample was not returned "
                    "when the booking was closed. "
                    f"Recorded by {checked_by}."
                )

                new_condition = "Unknown"
                new_asset_state = "Lost"
                new_location_id = None

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
                    event_date,
                    title,
                    details,
                    actor,
                    previous_location_id,
                    new_location_id,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    NOW(),
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                );
                """,
                (
                    sample_record_id,
                    event_type,
                    title,
                    details,
                    checked_by.strip(),
                    previous_location_id,
                    new_location_id,
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

# -------------------------------------------------
# Default repair completion to original location
# -------------------------------------------------
def get_issue_previous_location(issue_id):
    """
    Return the sample location immediately before
    it entered the issue/hold workflow.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sl.id,
                    sl.code,
                    sl.name
                FROM sample_issues si

                JOIN sample_events se
                    ON se.sample_record_id =
                       si.sample_record_id

                JOIN sample_locations sl
                    ON sl.id =
                       se.previous_location_id

                WHERE si.id = %s
                  AND se.new_location_id = (
                      SELECT id
                      FROM sample_locations
                      WHERE code = 'H1'
                      LIMIT 1
                  )

                ORDER BY se.event_date DESC
                LIMIT 1;
                """,
                (issue_id,),
            )

            return cur.fetchone()
        

def complete_booking_return(
    *,
    booking_group_id,
    checked_by,
    return_items,
):
    """
    Complete the return for an entire booking atomically.

    Every physical sample in the booking must have a return
    status before the booking can be completed.

    Non-good returns automatically create a Sample Issue.
    """

    allowed_statuses = {
        "Good",
        "Damaged",
        "Incomplete",
        "Not Returned",
    }

    if not checked_by or not checked_by.strip():
        raise ValueError(
            "Checked By is required."
        )

    if not return_items:
        raise ValueError(
            "No return items were provided."
        )

    checked_by = checked_by.strip()

    # -------------------------------------------------
    # Validate submitted return items
    # -------------------------------------------------

    submitted_item_ids = set()

    for item in return_items:
        booking_item_id = str(
            item["booking_item_id"]
        )

        if booking_item_id in submitted_item_ids:
            raise ValueError(
                "A booking item was submitted more than once."
            )

        submitted_item_ids.add(
            booking_item_id
        )

        return_status = item["return_status"]

        if return_status not in allowed_statuses:
            raise ValueError(
                (
                    "Invalid return status for "
                    f"booking item {booking_item_id}."
                )
            )

    # -------------------------------------------------
    # Begin transaction
    # -------------------------------------------------

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:

                # -----------------------------------------
                # Get Repair / Hold Area
                # -----------------------------------------

                cur.execute(
                    """
                    SELECT id
                    FROM sample_locations
                    WHERE code = 'H1'
                    AND active = TRUE
                    LIMIT 1;
                    """
                )

                hold_location = cur.fetchone()

                if not hold_location:
                    raise ValueError(
                        "Repair / Hold Area (H1) could not be found."
                    )

                hold_location_id = hold_location["id"]

                # -----------------------------------------
                # Lock booking group
                # -----------------------------------------

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
                    (
                        booking_group_id,
                    ),
                )

                booking = cur.fetchone()

                if not booking:
                    raise ValueError(
                        "Booking could not be found."
                    )

                if (
                    booking["booking_status"]
                    != "Reserved"
                ):
                    raise ValueError(
                        (
                            f"Booking "
                            f"{booking['booking_number']} "
                            "is no longer Reserved."
                        )
                    )

                # -----------------------------------------
                # Lock booking items
                # -----------------------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        sample_record_id,
                        booking_status
                    FROM sample_bookings
                    WHERE booking_group_id = %s
                    ORDER BY id
                    FOR UPDATE;
                    """,
                    (
                        booking_group_id,
                    ),
                )

                booking_items = cur.fetchall()

                if not booking_items:
                    raise ValueError(
                        (
                            "This booking does not contain "
                            "any sample items."
                        )
                    )

                # -----------------------------------------
                # Validate all items were submitted
                # -----------------------------------------

                expected_item_ids = {
                    str(item["id"])
                    for item in booking_items
                }

                if (
                    submitted_item_ids
                    != expected_item_ids
                ):
                    raise ValueError(
                        (
                            "Every sample in the booking "
                            "must have a return condition "
                            "before the return can be completed."
                        )
                    )

                submitted_by_item = {
                    str(
                        item["booking_item_id"]
                    ): item
                    for item in return_items
                }

                # -----------------------------------------
                # Process each physical sample
                # -----------------------------------------

                for booking_item in booking_items:

                    booking_item_id = str(
                        booking_item["id"]
                    )

                    sample_record_id = (
                        booking_item[
                            "sample_record_id"
                        ]
                    )

                    # -----------------------------------------
                    # Lock sample and preserve current location
                    # -----------------------------------------

                    cur.execute(
                        """
                        SELECT
                            current_location_id
                        FROM sample_master
                        WHERE id = %s
                        FOR UPDATE;
                        """,
                        (
                            sample_record_id,
                        ),
                    )

                    sample = cur.fetchone()

                    if not sample:
                        raise ValueError(
                            "Sample could not be found."
                        )

                    previous_location_id = (
                        sample["current_location_id"]
                    )




                    if (
                        booking_item[
                            "booking_status"
                        ]
                        != "Reserved"
                    ):
                        raise ValueError(
                            (
                                "One or more booking items "
                                "are no longer Reserved."
                            )
                        )

                    submitted = (
                        submitted_by_item[
                            booking_item_id
                        ]
                    )

                    submitted_sample_id = str(
                        submitted[
                            "sample_record_id"
                        ]
                    )

                    if (
                        submitted_sample_id
                        != str(sample_record_id)
                    ):
                        raise ValueError(
                            (
                                "Return sample does not "
                                "match the booking item."
                            )
                        )

                    return_status = (
                        submitted[
                            "return_status"
                        ]
                    )

                    notes = submitted.get(
                        "notes"
                    )

                    clean_notes = (
                        notes.strip()
                        if (
                            notes
                            and notes.strip()
                        )
                        else None
                    )

                    damage_reported = (
                        return_status
                        == "Damaged"
                    )

                    incomplete_reported = (
                        return_status
                        == "Incomplete"
                    )

                    # -----------------------------------------
                    # Determine resulting sample state
                    # -----------------------------------------

                    if return_status == "Good":

                        event_type = (
                            "SAMPLE_RETURNED"
                        )

                        title = (
                            "Sample Returned"
                        )

                        details = (
                            "Return inspection "
                            f"completed by {checked_by}. "
                            "Condition: Good."
                        )

                        new_condition = "Good"
                        new_asset_state = "Active"

                        return_location_id = submitted.get(
                            "return_location_id"
                        )

                        if not return_location_id:
                            raise ValueError(
                                (
                                    "A return location is required "
                                    "for samples returned in Good condition."
                                )
                            )

                        new_location_id = return_location_id

                    elif return_status == "Damaged":

                        event_type = (
                            "DAMAGE_REPORTED"
                        )

                        title = (
                            "Damage Reported"
                        )

                        details = (
                            "Return inspection "
                            f"completed by {checked_by}. "
                            "Condition: Damaged."
                        )

                        new_condition = "Damaged"
                        new_asset_state = "Damaged"

                        new_location_id = hold_location_id

                    elif return_status == "Incomplete":

                        event_type = (
                            "INCOMPLETE_RETURN"
                        )

                        title = (
                            "Incomplete Return"
                        )

                        details = (
                            "Return inspection "
                            f"completed by {checked_by}. "
                            "Condition: Incomplete."
                        )

                        new_condition = "Incomplete"
                        new_asset_state = "Inactive"

                        new_location_id = hold_location_id

                    else:

                        event_type = (
                            "SAMPLE_NOT_RETURNED"
                        )

                        title = (
                            "Sample Not Returned"
                        )

                        details = (
                            "Sample was not returned "
                            "when the booking was closed. "
                            f"Recorded by {checked_by}."
                        )

                        new_condition = "Unknown"
                        new_asset_state = "Lost"

                        new_location_id = None

                    # Add optional notes to the event.
                    if clean_notes:
                        details += (
                            f" Notes: {clean_notes}"
                        )

                    # -----------------------------------------
                    # Save return inspection
                    # -----------------------------------------

                    cur.execute(
                        """
                        INSERT INTO sample_return_checks (
                            booking_group_id,
                            booking_item_id,
                            sample_record_id,
                            return_status,
                            condition_on_return,
                            damage_reported,
                            incomplete_reported,
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
                            NOW(),
                            %s
                        )
                        ON CONFLICT (
                            booking_item_id
                        )
                        DO UPDATE SET
                            return_status =
                                EXCLUDED.return_status,
                            condition_on_return =
                                EXCLUDED.condition_on_return,
                            damage_reported =
                                EXCLUDED.damage_reported,
                            incomplete_reported =
                                EXCLUDED.incomplete_reported,
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
                            booking_item["id"],
                            sample_record_id,
                            return_status,
                            return_status,
                            damage_reported,
                            incomplete_reported,
                            checked_by,
                            clean_notes,
                        ),
                    )

                    # IMPORTANT:
                    # Fetch RETURNING id immediately.
                    return_check_row = (
                        cur.fetchone()
                    )

                    if not return_check_row:
                        raise RuntimeError(
                            (
                                "Could not retrieve "
                                "return check ID."
                            )
                        )

                    return_check_id = (
                        return_check_row["id"]
                    )

                    # -----------------------------------------
                    # Record return event
                    # -----------------------------------------

                    cur.execute(
                        """
                        INSERT INTO sample_events (
                            sample_record_id,
                            event_type,
                            event_date,
                            title,
                            details,
                            actor,
                            previous_location_id,
                            new_location_id,
                            created_at
                        )
                        VALUES (
                            %s,
                            %s,
                            NOW(),
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            NOW()
                        );
                        """,
                        (
                            sample_record_id,
                            event_type,
                            title,
                            details,
                            checked_by,
                            previous_location_id,
                            new_location_id,
                        ),
                    )

                    # -----------------------------------------
                    # Create Sample Issue when required
                    # -----------------------------------------

                    if return_status in {
                        "Damaged",
                        "Incomplete",
                        "Not Returned",
                    }:

                        cur.execute(
                            """
                            SELECT id
                            FROM sample_issues
                            WHERE return_check_id = %s
                              AND issue_status NOT IN (
                                  'Resolved',
                                  'Retired',
                                  'Converted to Refurbished'
                              )
                            LIMIT 1;
                            """,
                            (
                                return_check_id,
                            ),
                        )

                        existing_issue = (
                            cur.fetchone()
                        )

                        if not existing_issue:

                            cur.execute(
                                """
                                INSERT INTO sample_issues (
                                    sample_record_id,
                                    booking_group_id,
                                    return_check_id,
                                    issue_type,
                                    issue_status,
                                    description,
                                    reported_by,
                                    reported_at
                                )
                                VALUES (
                                    %s,
                                    %s,
                                    %s,
                                    %s,
                                    'Open',
                                    %s,
                                    %s,
                                    NOW()
                                );
                                """,
                                (
                                    sample_record_id,
                                    booking_group_id,
                                    return_check_id,
                                    return_status,
                                    clean_notes,
                                    checked_by,
                                ),
                            )

                    # -----------------------------------------
                    # Update physical sample
                    # -----------------------------------------

                    cur.execute(
                        """
                        UPDATE sample_master
                        SET
                            condition = %s,
                            asset_state = %s,
                            current_location_id = %s,
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            new_condition,
                            new_asset_state,
                            new_location_id,
                            sample_record_id,
                        ),
                    )

                    # -----------------------------------------
                    # Complete booking item
                    # -----------------------------------------

                    cur.execute(
                        """
                        UPDATE sample_bookings
                        SET
                            booking_status = 'Completed',
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            booking_item["id"],
                        ),
                    )

                    # -----------------------------------------
                    # Record booking completion event
                    # -----------------------------------------

                    cur.execute(
                        """
                        INSERT INTO sample_events (
                            sample_record_id,
                            event_type,
                            event_date,
                            title,
                            details,
                            actor,
                            created_at
                        )
                        VALUES (
                            %s,
                            'BOOKING_COMPLETED',
                            NOW(),
                            'Booking Completed',
                            %s,
                            %s,
                            NOW()
                        );
                        """,
                        (
                            sample_record_id,
                            (
                                f"Booking "
                                f"{booking['booking_number']} "
                                "completed after return "
                                f"inspection by {checked_by}."
                            ),
                            checked_by,
                        ),
                    )

                # -----------------------------------------
                # Complete booking group
                # -----------------------------------------

                cur.execute(
                    """
                    UPDATE sample_booking_groups
                    SET
                        booking_status = 'Completed',
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        booking_group_id,
                    ),
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

    return {
        "booking_number": (
            booking["booking_number"]
        ),
        "booking_status": "Completed",
        "sample_count": len(
            booking_items
        ),
    }


def get_sample_issues(
    *,
    include_closed=False,
):
    """
    Return sample issues with sample and booking details.

    By default, only issues that still require attention
    are returned.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            where_clause = ""

            if not include_closed:
                where_clause = """
                    WHERE si.issue_status NOT IN (
                        'Resolved',
                        'Retired',
                        'Converted to Refurbished'
                    )
                """

            cur.execute(
                f"""
                SELECT
                    si.id AS issue_id,
                    si.sample_record_id,
                    si.booking_group_id,
                    si.return_check_id,
                    si.issue_type,
                    si.issue_status,
                    si.description,
                    si.reported_by,
                    si.reported_at,
                    si.assigned_to,
                    si.resolution_action,
                    si.resolution_notes,
                    si.resolved_by,
                    si.resolved_at,

                    sm.sample_id,
                    sm.sample_name,
                    sm.condition,
                    sm.asset_state,

                    st.code AS sample_type_code,
                    st.name AS sample_type_name,

                    sl.code AS location_code,
                    sl.name AS location_name,

                    sbg.booking_number

                FROM sample_issues si

                JOIN sample_master sm
                    ON sm.id = si.sample_record_id

                JOIN sample_types st
                    ON st.id = sm.sample_type_id

                LEFT JOIN sample_locations sl
                    ON sl.id = sm.current_location_id

                LEFT JOIN sample_booking_groups sbg
                    ON sbg.id = si.booking_group_id

                {where_clause}

                ORDER BY
                    si.reported_at DESC,
                    sm.sample_name;
                """
            )

            return cur.fetchall()


# -----------------------------------------
# Sample Issue Details
# -----------------------------------------

def get_sample_issue_details(issue_id):
    """
    Return the full detail for one sample issue.

    Includes:
    - issue information
    - sample information
    - sample type
    - current location
    - booking information
    - return-check information
    """

    if not issue_id:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    si.id AS issue_id,
                    si.sample_record_id,
                    si.booking_group_id,
                    si.return_check_id,
                    si.issue_type,
                    si.issue_status,
                    si.description,
                    si.reported_by,
                    si.reported_at,
                    si.assigned_to,
                    si.resolution_action,
                    si.resolution_notes,
                    si.resolved_by,
                    si.resolved_at,

                    sm.sample_id,
                    sm.sample_name,
                    sm.condition,
                    sm.asset_state,
                    sm.current_holder,
                    sm.current_holder_team,
                    sm.received_date,
                    sm.notes AS sample_notes,

                    st.code AS sample_type_code,
                    st.name AS sample_type_name,

                    sl.code AS location_code,
                    sl.name AS location_name,

                    sbg.booking_number,
                    sbg.booked_by,
                    sbg.team AS booking_team,
                    sbg.purpose AS booking_purpose,
                    sbg.start_date AS booking_start_date,
                    sbg.end_date AS booking_end_date,

                    src.return_status,
                    src.condition_on_return,
                    src.notes AS return_notes,
                    src.checked_by,
                    src.checked_at

                FROM sample_issues si

                JOIN sample_master sm
                    ON sm.id = si.sample_record_id

                LEFT JOIN sample_types st
                    ON st.id = sm.sample_type_id

                LEFT JOIN sample_locations sl
                    ON sl.id = sm.current_location_id

                LEFT JOIN sample_booking_groups sbg
                    ON sbg.id = si.booking_group_id

                LEFT JOIN sample_return_checks src
                    ON src.id = si.return_check_id

                WHERE si.id = %s

                LIMIT 1;
                """,
                (issue_id,),
            )

            return cur.fetchone()



def add_sample_issue_media(
    *,
    sample_record_id,
    issue_id,
    original_filename,
    storage_path,
    uploaded_by,
    caption=None,
    media_type="Damage",
    storage_provider="local",
):
    """
    Add metadata for a photo or file attached
    to a sample issue.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sample_media (
                    sample_record_id,
                    issue_id,
                    media_type,
                    storage_provider,
                    storage_path,
                    original_filename,
                    caption,
                    uploaded_by,
                    uploaded_at,
                    created_at
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
                    NOW(),
                    NOW()
                )
                RETURNING id;
                """,
                (
                    sample_record_id,
                    issue_id,
                    media_type,
                    storage_provider,
                    storage_path,
                    original_filename,
                    caption,
                    uploaded_by,
                ),
            )

            row = cur.fetchone()
            conn.commit()

            return row["id"]

# -----------------------------------------
# Add photos
# -----------------------------------------
def get_sample_issue_media(issue_id):
    """
    Return all media attached to one sample issue.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    sample_record_id,
                    issue_id,
                    media_type,
                    storage_provider,
                    storage_path,
                    original_filename,
                    caption,
                    uploaded_by,
                    uploaded_at
                FROM sample_media
                WHERE issue_id = %s
                ORDER BY uploaded_at DESC;
                """,
                (issue_id,),
            )

            return cur.fetchall()

# -----------------------------------------
# Repair Sample Repair
# -----------------------------------------

def start_sample_repair(
    *,
    issue_id,
    started_by,
    repair_notes=None,
):
    """
    Start repair work for a damaged sample issue.

    Creates a repair record and moves the issue
    to Under Repair.
    """

    if not started_by or not started_by.strip():
        raise ValueError(
            "Started by is required."
        )

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:

                #
                # Lock issue
                #

                cur.execute(
                    """
                    SELECT
                        id,
                        sample_record_id,
                        issue_type,
                        issue_status
                    FROM sample_issues
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (issue_id,),
                )

                issue = cur.fetchone()

                if not issue:
                    raise ValueError(
                        "Sample issue could not be found."
                    )

                if issue["issue_type"] != "Damaged":
                    raise ValueError(
                        "Only damaged samples can "
                        "be sent for repair."
                    )

                if issue["issue_status"] != "Open":
                    raise ValueError(
                        "This issue is no longer open."
                    )

                #
                # Prevent duplicate active repair
                #

                cur.execute(
                    """
                    SELECT id
                    FROM sample_repairs
                    WHERE issue_id = %s
                      AND repair_status IN (
                          'Pending',
                          'In Progress'
                      )
                    LIMIT 1;
                    """,
                    (issue_id,),
                )

                if cur.fetchone():
                    raise ValueError(
                        "An active repair already "
                        "exists for this issue."
                    )

                #
                # Create repair
                #

                cur.execute(
                    """
                    INSERT INTO sample_repairs (
                        issue_id,
                        sample_record_id,
                        repair_status,
                        repair_notes,
                        repair_started_by,
                        repair_started_at,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        'In Progress',
                        %s,
                        %s,
                        NOW(),
                        NOW(),
                        NOW()
                    )
                    RETURNING id;
                    """,
                    (
                        issue_id,
                        issue["sample_record_id"],
                        repair_notes.strip()
                        if repair_notes
                        else None,
                        started_by.strip(),
                    ),
                )

                repair = cur.fetchone()

                #
                # Update issue
                #

                cur.execute(
                    """
                    UPDATE sample_issues
                    SET
                        issue_status = 'Under Repair',
                        assigned_to = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        started_by.strip(),
                        issue_id,
                    ),
                )

                #
                # Record repair-started event
                #

                cur.execute(
                    """
                    INSERT INTO sample_events (
                        sample_record_id,
                        event_type,
                        event_date,
                        title,
                        details,
                        actor,
                        created_at
                    )
                    VALUES (
                        %s,
                        'REPAIR_STARTED',
                        NOW(),
                        'Repair started',
                        %s,
                        %s,
                        NOW()
                    );
                    """,
                    (
                        issue["sample_record_id"],
                        (
                            repair_notes.strip()
                            if repair_notes
                            else "Sample sent for repair."
                        ),
                        started_by.strip(),
                    ),
                )

                conn.commit()

                return repair["id"]

        except Exception:
            conn.rollback()
            raise

# -----------------------------------------
# Retire Sample
# -----------------------------------------
def retire_sample_from_issue(
    *,
    issue_id,
    retired_by,
    reason=None,
):
    """
    Retire a sample directly from an open issue.
    """

    if not retired_by or not retired_by.strip():
        raise ValueError(
            "Retired by is required."
        )

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        sample_record_id,
                        issue_status
                    FROM sample_issues
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (issue_id,),
                )

                issue = cur.fetchone()

                if not issue:
                    raise ValueError(
                        "Sample issue could not be found."
                    )

                if issue["issue_status"] != "Open":
                    raise ValueError(
                        "Only an open issue can "
                        "be retired directly."
                    )

                resolution_notes = (
                    reason.strip()
                    if reason
                    else None
                )

                #
                # Retire physical sample
                #

                cur.execute(
                    """
                    UPDATE sample_master
                    SET
                        asset_state = 'Retired',
                        current_location_id = NULL,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        issue["sample_record_id"],
                    ),
                )

                #
                # Close issue
                #

                cur.execute(
                    """
                    UPDATE sample_issues
                    SET
                        issue_status = 'Retired',
                        resolution_action = 'Retire',
                        resolution_notes = %s,
                        resolved_by = %s,
                        resolved_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        resolution_notes,
                        retired_by.strip(),
                        issue_id,
                    ),
                )

                #
                # Record retirement event
                #

                cur.execute(
                    """
                    INSERT INTO sample_events (
                        sample_record_id,
                        event_type,
                        event_date,
                        title,
                        details,
                        actor,
                        created_at
                    )
                    VALUES (
                        %s,
                        'SAMPLE_RETIRED',
                        NOW(),
                        'Sample retired',
                        %s,
                        %s,
                        NOW()
                    );
                    """,
                    (
                        issue["sample_record_id"],
                        (
                            resolution_notes
                            or "Sample retired from issue workflow."
                        ),
                        retired_by.strip(),
                    ),
                )

                conn.commit()

        except Exception:
            conn.rollback()
            raise

# -----------------------------------------
# Retrieve Samples with Issue
# -----------------------------------------
def get_sample_issue_repair(issue_id):
    """
    Return the most recent repair record for an issue.
    """

    if not issue_id:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id AS repair_id,
                    issue_id,
                    sample_record_id,
                    repair_status,
                    repair_notes,
                    repair_started_by,
                    repair_started_at,
                    repair_completed_by,
                    repair_completed_at,
                    completion_notes,
                    final_disposition,
                    created_at,
                    updated_at
                FROM sample_repairs
                WHERE issue_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (issue_id,),
            )

            return cur.fetchone()


# -----------------------------------------
# Complete Sample Repair
# -----------------------------------------
def complete_sample_repair(
    *,
    issue_id,
    completed_by,
    completion_notes,
    final_disposition,
    return_location_id=None,
):
    """
    Complete a sample repair and apply the final disposition.

    Supported dispositions:
    - Return to Sample Pool
    - Convert to Refurbished
    - Retire
    """

    if not completed_by or not completed_by.strip():
        raise ValueError(
            "Completed by is required."
        )

    if not completion_notes or not completion_notes.strip():
        raise ValueError(
            "Completion notes are required."
        )

    allowed_dispositions = (
        "Return to Sample Pool",
        "Convert to Refurbished",
        "Retire",
    )

    if final_disposition not in allowed_dispositions:
        raise ValueError(
            "Invalid final disposition."
        )

    if (
        final_disposition == "Return to Sample Pool"
        and not return_location_id
    ):
        raise ValueError(
            "Return location is required."
        )

    completed_by = completed_by.strip()
    completion_notes = completion_notes.strip()

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:

                # -----------------------------------------
                # Lock issue
                # -----------------------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        sample_record_id,
                        issue_type,
                        issue_status
                    FROM sample_issues
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (issue_id,),
                )

                issue = cur.fetchone()

                if not issue:
                    raise ValueError(
                        "Sample issue could not be found."
                    )

                if issue["issue_type"] != "Damaged":
                    raise ValueError(
                        "This issue is not a damaged "
                        "sample repair."
                    )

                if issue["issue_status"] != "Under Repair":
                    raise ValueError(
                        "This issue is not currently "
                        "under repair."
                    )

                # -----------------------------------------
                # Lock active repair
                # -----------------------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        issue_id,
                        sample_record_id,
                        repair_status
                    FROM sample_repairs
                    WHERE issue_id = %s
                      AND repair_status IN (
                          'Pending',
                          'In Progress'
                      )
                    ORDER BY created_at DESC
                    LIMIT 1
                    FOR UPDATE;
                    """,
                    (issue_id,),
                )

                repair = cur.fetchone()

                if not repair:
                    raise ValueError(
                        "No active repair could be found "
                        "for this issue."
                    )

                # -----------------------------------------
                # Lock sample and preserve H1 location
                # -----------------------------------------

                cur.execute(
                    """
                    SELECT
                        current_location_id
                    FROM sample_master
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (
                        issue["sample_record_id"],
                    ),
                )

                sample = cur.fetchone()

                if not sample:
                    raise ValueError(
                        "Sample could not be found."
                    )

                previous_location_id = (
                    sample["current_location_id"]
                )

                # -----------------------------------------
                # Validate return location
                # -----------------------------------------

                if (
                    final_disposition
                    == "Return to Sample Pool"
                ):
                    cur.execute(
                        """
                        SELECT
                            id,
                            code,
                            name
                        FROM sample_locations
                        WHERE id = %s
                          AND active = TRUE
                        LIMIT 1;
                        """,
                        (return_location_id,),
                    )

                    return_location = cur.fetchone()

                    if not return_location:
                        raise ValueError(
                            "Return location could "
                            "not be found."
                        )

                    if return_location["code"] == "H1":
                        raise ValueError(
                            "H1 cannot be used as the "
                            "final sample location."
                        )

                # -----------------------------------------
                # Complete repair record
                # -----------------------------------------

                cur.execute(
                    """
                    UPDATE sample_repairs
                    SET
                        repair_status = 'Completed',
                        repair_completed_by = %s,
                        repair_completed_at = NOW(),
                        completion_notes = %s,
                        final_disposition = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        completed_by,
                        completion_notes,
                        final_disposition,
                        repair["id"],
                    ),
                )

                # -----------------------------------------
                # Apply final disposition
                # -----------------------------------------

                if (
                    final_disposition
                    == "Return to Sample Pool"
                ):

                    cur.execute(
                        """
                        UPDATE sample_master
                        SET
                            condition = 'Good',
                            asset_state = 'Active',
                            current_location_id = %s,
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            return_location_id,
                            issue["sample_record_id"],
                        ),
                    )

                    issue_status = "Resolved"

                    resolution_action = (
                        "Return to Sample Pool"
                    )

                    event_type = (
                        "SAMPLE_RESTORED"
                    )

                    event_title = (
                        "Sample Restored"
                    )

                    new_location_id = (
                        return_location_id
                    )

                elif (
                    final_disposition
                    == "Convert to Refurbished"
                ):

                    # Temporary behaviour until the
                    # refurbished_items module is added.

                    cur.execute(
                        """
                        UPDATE sample_master
                        SET
                            asset_state = 'Retired',
                            current_location_id = NULL,
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            issue["sample_record_id"],
                        ),
                    )

                    issue_status = (
                        "Converted to Refurbished"
                    )

                    resolution_action = (
                        "Convert to Refurbished"
                    )

                    event_type = (
                        "SAMPLE_CONVERTED_TO_REFURBISHED"
                    )

                    event_title = (
                        "Converted to Refurbished"
                    )

                    new_location_id = None

                else:

                    cur.execute(
                        """
                        UPDATE sample_master
                        SET
                            asset_state = 'Retired',
                            current_location_id = NULL,
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            issue["sample_record_id"],
                        ),
                    )

                    issue_status = "Retired"
                    resolution_action = "Retire"

                    event_type = (
                        "SAMPLE_RETIRED"
                    )

                    event_title = (
                        "Sample Retired"
                    )

                    new_location_id = None

                # -----------------------------------------
                # Close issue
                # -----------------------------------------

                cur.execute(
                    """
                    UPDATE sample_issues
                    SET
                        issue_status = %s,
                        resolution_action = %s,
                        resolution_notes = %s,
                        resolved_by = %s,
                        resolved_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        issue_status,
                        resolution_action,
                        completion_notes,
                        completed_by,
                        issue_id,
                    ),
                )

                # -----------------------------------------
                # Record lifecycle event
                # -----------------------------------------

                cur.execute(
                    """
                    INSERT INTO sample_events (
                        sample_record_id,
                        event_type,
                        event_date,
                        title,
                        details,
                        actor,
                        previous_location_id,
                        new_location_id,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        NOW(),
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NOW()
                    );
                    """,
                    (
                        issue["sample_record_id"],
                        event_type,
                        event_title,
                        completion_notes,
                        completed_by,
                        previous_location_id,
                        new_location_id,
                    ),
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

    return {
        "issue_id": issue_id,
        "repair_id": repair["id"],
        "issue_status": issue_status,
        "final_disposition": final_disposition,
    }