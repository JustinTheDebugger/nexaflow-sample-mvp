-- ============================================================
-- NexaFlow Sample Management MVP
-- Base Schema
-- ============================================================


-- ------------------------------------------------------------
-- 1. Sample Types
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_types (
    id BIGSERIAL PRIMARY KEY,

    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,

    is_bookable BOOLEAN NOT NULL DEFAULT TRUE,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


INSERT INTO sample_types (
    code,
    name,
    is_bookable,
    requires_approval
)
VALUES
    ('SMS', 'Salesman Sample', TRUE, FALSE),
    ('PP', 'Pre-production Sample', TRUE, FALSE),
    ('TSS', 'Trade Show Sample', TRUE, TRUE),
    ('DEV', 'Development Sample', FALSE, FALSE),
    ('TEST', 'Test Sample', FALSE, FALSE),
    ('PTT', 'Prototype Sample', FALSE, FALSE)
ON CONFLICT (code) DO NOTHING;

CREATE TYPE sample_asset_state AS ENUM (
    'Active',
    'Inactive',
    'Damaged',
    'Retired',
    'Lost'
);

-- ------------------------------------------------------------
-- 2. Sample Locations
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_locations (
    id BIGSERIAL PRIMARY KEY,

    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


INSERT INTO sample_locations (
    code,
    name
)
VALUES
    ('S1', 'Storeroom 1'),
    ('S2', 'Storeroom 2'),
    ('S3', 'Storeroom 3'),
    ('X1', 'Exit Floor Pile')
ON CONFLICT (code) DO NOTHING;


-- ------------------------------------------------------------
-- 3. Sample ID Counters
--
-- Each sample TYPE has its own sequence.
--
-- Example:
--
-- SMS-00001-S1
-- SMS-00002-S2
--
-- PP-00001-S1
-- PP-00002-S3
--
-- The location suffix represents the intake/origin location.
-- The sample ID never changes when the asset moves later.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_id_counters (
    sample_type_id BIGINT PRIMARY KEY
        REFERENCES sample_types(id)
        ON DELETE CASCADE,

    last_number INTEGER NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT sample_counter_non_negative
        CHECK (last_number >= 0)
);


INSERT INTO sample_id_counters (
    sample_type_id,
    last_number
)
SELECT
    id,
    0
FROM sample_types
ON CONFLICT (sample_type_id) DO NOTHING;


-- ------------------------------------------------------------
-- 4. Samples
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_id VARCHAR(50) UNIQUE NOT NULL,

    sample_name TEXT NOT NULL,

    category_code VARCHAR(20),

    sample_type_id BIGINT NOT NULL
        REFERENCES sample_types(id),

    origin_location_id BIGINT NOT NULL
        REFERENCES sample_locations(id),

    current_location_id BIGINT
        REFERENCES sample_locations(id),

    source VARCHAR(100) NOT NULL DEFAULT 'Factory',

    received_date DATE NOT NULL,

    current_holder TEXT,

    current_holder_team VARCHAR(100),

    condition VARCHAR(50) NOT NULL DEFAULT 'Good',

    asset_state sample_asset_state NOT NULL DEFAULT 'Active',

    usage_count INTEGER NOT NULL DEFAULT 0,

    last_inspection_date DATE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 5. Sample Events
--
-- Complete operational lifecycle / audit trail.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    event_type VARCHAR(100) NOT NULL,

    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    title TEXT NOT NULL,

    details TEXT,

    actor TEXT,

    team VARCHAR(100),

    previous_location_id BIGINT
        REFERENCES sample_locations(id)
        ON DELETE SET NULL,

    new_location_id BIGINT
        REFERENCES sample_locations(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 6. Sample Bookings
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    booked_by TEXT NOT NULL,

    team VARCHAR(100),

    purpose TEXT,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    booking_status VARCHAR(50)
        NOT NULL DEFAULT 'Reserved',

    approval_required BOOLEAN
        NOT NULL DEFAULT FALSE,

    approved_by TEXT,

    approved_at TIMESTAMPTZ,

    notes TEXT,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_booking_dates
        CHECK (end_date >= start_date)
);


-- ------------------------------------------------------------
-- 7. Sample Condition Reports
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_condition_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    condition VARCHAR(50) NOT NULL,

    severity VARCHAR(50),

    damage_type VARCHAR(100),

    description TEXT,

    reported_by TEXT,

    inspection_date DATE NOT NULL,

    removed_from_use BOOLEAN
        NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 8. Sample Media
--
-- Actual files will later be stored in Supabase Storage.
-- This table stores the relationship and metadata.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    event_id UUID
        REFERENCES sample_events(id)
        ON DELETE SET NULL,

    condition_report_id UUID
        REFERENCES sample_condition_reports(id)
        ON DELETE SET NULL,

    media_type VARCHAR(50) NOT NULL,

    storage_path TEXT NOT NULL,

    file_name TEXT,

    mime_type VARCHAR(100),

    caption TEXT,

    uploaded_by TEXT,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- Sample ↔ Product Relationships
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    product_code VARCHAR(100) NOT NULL,

    relationship_type VARCHAR(50)
        NOT NULL DEFAULT 'Primary',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        sample_record_id,
        product_code
    )
);


-- ------------------------------------------------------------
-- 9. Indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_sample_master_sample_type
    ON sample_master(sample_type_id);


CREATE INDEX IF NOT EXISTS idx_sample_master_origin_location
    ON sample_master(origin_location_id);


CREATE INDEX IF NOT EXISTS idx_sample_master_current_location
    ON sample_master(current_location_id);


CREATE INDEX IF NOT EXISTS idx_sample_events_event_date
    ON sample_events(event_date DESC);


CREATE INDEX IF NOT EXISTS idx_sample_bookings_dates
    ON sample_bookings(start_date, end_date);


CREATE INDEX IF NOT EXISTS idx_sample_products_product_code
    ON sample_products(product_code);


CREATE INDEX IF NOT EXISTS idx_sample_events_sample_record
    ON sample_events(sample_record_id);

CREATE INDEX IF NOT EXISTS idx_sample_bookings_sample_record
    ON sample_bookings(sample_record_id);

CREATE INDEX IF NOT EXISTS idx_condition_reports_sample_record
    ON sample_condition_reports(sample_record_id);

CREATE INDEX IF NOT EXISTS idx_sample_media_sample_record
    ON sample_media(sample_record_id);

CREATE INDEX IF NOT EXISTS idx_sample_products_sample_record
    ON sample_products(sample_record_id);