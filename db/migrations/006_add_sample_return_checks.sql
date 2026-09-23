CREATE TABLE IF NOT EXISTS sample_return_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    booking_group_id UUID NOT NULL
        REFERENCES sample_booking_groups(id)
        ON DELETE CASCADE,

    booking_item_id UUID NOT NULL
        REFERENCES sample_bookings(id)
        ON DELETE CASCADE,

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE RESTRICT,

    return_status VARCHAR(50) NOT NULL,

    condition_on_return VARCHAR(50),

    damage_reported BOOLEAN NOT NULL DEFAULT FALSE,
    damage_details TEXT,

    incomplete_reported BOOLEAN NOT NULL DEFAULT FALSE,
    missing_details TEXT,

    checked_by VARCHAR(255) NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_sample_return_check_booking_item
        UNIQUE (booking_item_id),

    CONSTRAINT chk_sample_return_status
        CHECK (
            return_status IN (
                'Good',
                'Damaged',
                'Incomplete',
                'Missing'
            )
        )
);


CREATE INDEX IF NOT EXISTS
idx_sample_return_checks_booking_group
ON sample_return_checks (
    booking_group_id
);


CREATE INDEX IF NOT EXISTS
idx_sample_return_checks_sample
ON sample_return_checks (
    sample_record_id
);