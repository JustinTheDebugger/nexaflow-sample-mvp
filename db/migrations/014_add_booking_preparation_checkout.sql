-- ============================================================
-- Migration 014
-- Sample booking preparation and checkout workflow
--
-- Adds:
--   1. C1 Collection / Dispatch Area
--   2. Item-level preparation status
--   3. Replacement sample tracking
--   4. Missing-item preparation notes
--   5. Booking-group preparation / checkout timestamps
--
-- Workflow:
--   Reserved
--     -> Preparing
--     -> Ready for Collection
--     -> Checked Out
--     -> Completed
--
-- Missing samples do not block preparation.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Collection / Dispatch location
-- ------------------------------------------------------------

INSERT INTO sample_locations (
    code,
    name
)
SELECT
    'C1',
    'Collection / Dispatch Area'
WHERE NOT EXISTS (
    SELECT 1
    FROM sample_locations
    WHERE code = 'C1'
);


-- ------------------------------------------------------------
-- 2. Item-level preparation fields
-- ------------------------------------------------------------

ALTER TABLE sample_bookings
    ADD COLUMN IF NOT EXISTS preparation_status
        VARCHAR(30) NOT NULL DEFAULT 'Not Prepared',

    ADD COLUMN IF NOT EXISTS prepared_at
        TIMESTAMPTZ,

    ADD COLUMN IF NOT EXISTS missing_reported_at
        TIMESTAMPTZ,

    ADD COLUMN IF NOT EXISTS missing_note
        TEXT,

    ADD COLUMN IF NOT EXISTS replacement_sample_record_id
        UUID;


-- Replacement must reference a real sample.
ALTER TABLE sample_bookings
    DROP CONSTRAINT IF EXISTS
        sample_bookings_replacement_sample_record_id_fkey;

ALTER TABLE sample_bookings
    ADD CONSTRAINT
        sample_bookings_replacement_sample_record_id_fkey
    FOREIGN KEY (
        replacement_sample_record_id
    )
    REFERENCES sample_master(id)
    ON DELETE RESTRICT;


-- ------------------------------------------------------------
-- 3. Booking-group lifecycle timestamps
-- ------------------------------------------------------------

ALTER TABLE sample_booking_groups
    ADD COLUMN IF NOT EXISTS preparation_started_at
        TIMESTAMPTZ,

    ADD COLUMN IF NOT EXISTS ready_for_collection_at
        TIMESTAMPTZ,

    ADD COLUMN IF NOT EXISTS checked_out_at
        TIMESTAMPTZ;


-- ------------------------------------------------------------
-- 4. Useful index for replacement lookups
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS
    idx_sample_bookings_replacement_sample
ON sample_bookings (
    replacement_sample_record_id
);