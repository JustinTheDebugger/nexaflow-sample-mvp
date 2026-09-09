-- ============================================================
-- Migration 002
-- Simplify bookings and add sample request workflow
-- ============================================================


-- ------------------------------------------------------------
-- 1. Existing bookings no longer require approval
-- ------------------------------------------------------------

UPDATE sample_bookings
SET
    booking_status = 'Reserved',
    approval_required = FALSE
WHERE booking_status IN (
    'Pending Approval',
    'Approved'
);


ALTER TABLE sample_bookings
    ALTER COLUMN approval_required
    SET DEFAULT FALSE;


-- ------------------------------------------------------------
-- 2. Sample request status
-- ------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'sample_request_status'
    ) THEN

        CREATE TYPE sample_request_status AS ENUM (
            'Pending Review',
            'Approved',
            'Rejected',
            'Cancelled'
        );

    END IF;
END $$;


-- ------------------------------------------------------------
-- 3. Sample Requests
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_requests (
    id UUID PRIMARY KEY
        DEFAULT gen_random_uuid(),

    product_code VARCHAR(100)
        REFERENCES products(product_code),

    requested_sample_name TEXT,

    category_code VARCHAR(20),

    quantity_required INTEGER
        NOT NULL DEFAULT 1,

    required_from DATE
        NOT NULL,

    required_until DATE
        NOT NULL,

    requested_by TEXT
        NOT NULL,

    requester_email TEXT
        NOT NULL,

    team VARCHAR(100),

    purpose TEXT,

    request_notes TEXT,

    request_status sample_request_status
        NOT NULL
        DEFAULT 'Pending Review',

    reviewed_by TEXT,

    reviewed_at TIMESTAMPTZ,

    operations_email TEXT,

    manager_notes TEXT,

    rejection_reason TEXT,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_sample_request_dates
        CHECK (
            required_until >= required_from
        ),

    CONSTRAINT valid_sample_request_quantity
        CHECK (
            quantity_required > 0
        )
);


-- ------------------------------------------------------------
-- 4. Indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS
    idx_sample_requests_status
ON sample_requests(request_status);


CREATE INDEX IF NOT EXISTS
    idx_sample_requests_dates
ON sample_requests(
    required_from,
    required_until
);


CREATE INDEX IF NOT EXISTS
    idx_sample_requests_product
ON sample_requests(product_code);