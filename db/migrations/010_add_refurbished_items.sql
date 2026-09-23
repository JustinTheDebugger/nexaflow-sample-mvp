-- ============================================================
-- Migration 010
-- Refurbished Items
--
-- Creates the inventory structure for physical samples that
-- leave the sample pool and become refurbished saleable stock.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Add Refurbished Stock location
-- ------------------------------------------------------------

INSERT INTO sample_locations (
    code,
    name,
    active
)
VALUES (
    'R1',
    'Refurbished Stock Area',
    TRUE
)
ON CONFLICT (code)
DO NOTHING;


-- ------------------------------------------------------------
-- 2. Refurbished ID counter
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS refurbished_id_counters (
    id BIGSERIAL PRIMARY KEY,

    last_number INTEGER NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Ensure one counter row exists.

INSERT INTO refurbished_id_counters (
    last_number
)
SELECT 0
WHERE NOT EXISTS (
    SELECT 1
    FROM refurbished_id_counters
);


-- ------------------------------------------------------------
-- 3. Refurbished Items
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS refurbished_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    refurbished_id VARCHAR(20)
        NOT NULL UNIQUE,

    source_sample_record_id UUID
        NOT NULL
        REFERENCES sample_master(id),

    product_id UUID NULL,

    condition_grade VARCHAR(10) NULL,

    refurbished_status VARCHAR(50)
        NOT NULL DEFAULT 'Available',

    location_id BIGINT NULL
        REFERENCES sample_locations(id),

    conversion_notes TEXT NULL,

    converted_by TEXT NOT NULL,

    converted_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    sale_price NUMERIC(12, 2) NULL,

    reserved_at TIMESTAMPTZ NULL,

    sold_at TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    CONSTRAINT refurbished_items_status_check
        CHECK (
            refurbished_status IN (
                'Available',
                'Reserved',
                'Sold',
                'Written Off'
            )
        ),

    CONSTRAINT refurbished_items_grade_check
        CHECK (
            condition_grade IS NULL
            OR condition_grade IN (
                'A',
                'B',
                'C'
            )
        ),

    CONSTRAINT refurbished_items_sale_price_check
        CHECK (
            sale_price IS NULL
            OR sale_price >= 0
        )
);


-- ------------------------------------------------------------
-- 4. Prevent the same sample being converted twice
-- ------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_refurbished_items_source_sample
ON refurbished_items (
    source_sample_record_id
);


-- ------------------------------------------------------------
-- 5. Useful inventory indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS
    idx_refurbished_items_status
ON refurbished_items (
    refurbished_status
);


CREATE INDEX IF NOT EXISTS
    idx_refurbished_items_location
ON refurbished_items (
    location_id
);


CREATE INDEX IF NOT EXISTS
    idx_refurbished_items_converted_at
ON refurbished_items (
    converted_at DESC
);