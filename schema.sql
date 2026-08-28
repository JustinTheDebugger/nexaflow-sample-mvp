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
    ('DEV', 'Development Sample', FALSE, FALSE)
ON CONFLICT (code) DO NOTHING;


CREATE TABLE IF NOT EXISTS samples (
    id BIGSERIAL PRIMARY KEY,
    sample_id VARCHAR(50) UNIQUE NOT NULL,

    product_name TEXT NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    category VARCHAR(100),

    sample_type_id BIGINT NOT NULL
        REFERENCES sample_types(id),

    source VARCHAR(100),
    received_date DATE,

    current_location TEXT,
    current_holder TEXT,
    current_holder_team VARCHAR(100),

    condition VARCHAR(50) NOT NULL DEFAULT 'Good',
    operational_status VARCHAR(50) NOT NULL DEFAULT 'Available',

    usage_count INTEGER NOT NULL DEFAULT 0,
    last_inspection_date DATE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS sample_events (
    id BIGSERIAL PRIMARY KEY,

    sample_id VARCHAR(50) NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    event_type VARCHAR(100) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    title TEXT NOT NULL,
    details TEXT,

    actor TEXT,
    team VARCHAR(100),

    previous_location TEXT,
    new_location TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS sample_bookings (
    id BIGSERIAL PRIMARY KEY,

    sample_id VARCHAR(50) NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    booked_by TEXT NOT NULL,
    team VARCHAR(100),

    purpose TEXT,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    booking_status VARCHAR(50) NOT NULL DEFAULT 'Reserved',

    approval_required BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_booking_dates
        CHECK (end_date >= start_date)
);


CREATE TABLE IF NOT EXISTS sample_condition_reports (
    id BIGSERIAL PRIMARY KEY,

    sample_id VARCHAR(50) NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    condition VARCHAR(50) NOT NULL,
    severity VARCHAR(50),
    damage_type VARCHAR(100),

    description TEXT,

    reported_by TEXT,
    inspection_date DATE NOT NULL,

    removed_from_use BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS sample_media (
    id BIGSERIAL PRIMARY KEY,

    sample_id VARCHAR(50) NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    event_id BIGINT
        REFERENCES sample_events(id)
        ON DELETE SET NULL,

    condition_report_id BIGINT
        REFERENCES sample_condition_reports(id)
        ON DELETE SET NULL,

    media_type VARCHAR(50) NOT NULL,

    storage_path TEXT NOT NULL,
    file_name TEXT,
    mime_type VARCHAR(100),

    caption TEXT,
    uploaded_by TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_samples_sample_type
    ON samples(sample_type_id);


CREATE INDEX IF NOT EXISTS idx_sample_events_sample_id
    ON sample_events(sample_id);


CREATE INDEX IF NOT EXISTS idx_sample_events_event_date
    ON sample_events(event_date DESC);


CREATE INDEX IF NOT EXISTS idx_sample_bookings_sample_id
    ON sample_bookings(sample_id);


CREATE INDEX IF NOT EXISTS idx_sample_bookings_dates
    ON sample_bookings(start_date, end_date);


CREATE INDEX IF NOT EXISTS idx_condition_reports_sample_id
    ON sample_condition_reports(sample_id);


CREATE INDEX IF NOT EXISTS idx_sample_media_sample_id
    ON sample_media(sample_id);