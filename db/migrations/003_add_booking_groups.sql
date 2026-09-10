-- =========================================================
-- NexaFlow
-- Migration 003
-- Add booking-level grouping
-- =========================================================

-- ---------------------------------------------------------
-- Booking number sequence
-- ---------------------------------------------------------

CREATE SEQUENCE IF NOT EXISTS sample_booking_number_seq
    START WITH 1
    INCREMENT BY 1;


-- ---------------------------------------------------------
-- Booking header / group
-- One row = one booking request
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_booking_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    booking_number VARCHAR(20)
        NOT NULL
        UNIQUE
        DEFAULT (
            'BK-' ||
            LPAD(
                nextval('sample_booking_number_seq')::TEXT,
                5,
                '0'
            )
        ),

    booked_by VARCHAR(255) NOT NULL,

    team VARCHAR(255),

    purpose VARCHAR(255),

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    notes TEXT,

    booking_status VARCHAR(50)
        NOT NULL
        DEFAULT 'Reserved',

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT sample_booking_groups_date_check
        CHECK (end_date >= start_date)
);


-- ---------------------------------------------------------
-- Link individual sample bookings to booking header
-- ---------------------------------------------------------

ALTER TABLE sample_bookings
ADD COLUMN IF NOT EXISTS booking_group_id UUID;


-- ---------------------------------------------------------
-- Foreign key
-- ---------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'sample_bookings_booking_group_id_fkey'
    ) THEN

        ALTER TABLE sample_bookings
        ADD CONSTRAINT
            sample_bookings_booking_group_id_fkey
        FOREIGN KEY (booking_group_id)
        REFERENCES sample_booking_groups(id)
        ON DELETE RESTRICT;

    END IF;
END $$;


-- ---------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------

CREATE INDEX IF NOT EXISTS
    idx_sample_bookings_booking_group_id
ON sample_bookings(booking_group_id);


CREATE INDEX IF NOT EXISTS
    idx_sample_booking_groups_status_dates
ON sample_booking_groups(
    booking_status,
    start_date,
    end_date
);


CREATE INDEX IF NOT EXISTS
    idx_sample_booking_groups_booking_number
ON sample_booking_groups(booking_number);


-- ---------------------------------------------------------
-- Backfill existing bookings
--
-- Existing booking rows were created before grouping existed.
-- Each old row becomes its own booking group.
--
-- New bookings created after this migration can contain
-- multiple sample_bookings under one booking_group_id.
-- ---------------------------------------------------------

DO $$
DECLARE
    booking_row RECORD;
    new_group_id UUID;
BEGIN

    FOR booking_row IN
        SELECT *
        FROM sample_bookings
        WHERE booking_group_id IS NULL
        ORDER BY start_date, id
    LOOP

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
            COALESCE(
                booking_row.booked_by,
                'Unknown'
            ),
            booking_row.team,
            booking_row.purpose,
            booking_row.start_date,
            booking_row.end_date,
            booking_row.notes,
            booking_row.booking_status
        )
        RETURNING id
        INTO new_group_id;


        UPDATE sample_bookings
        SET booking_group_id = new_group_id
        WHERE id = booking_row.id;

    END LOOP;

END $$;


-- ---------------------------------------------------------
-- All existing records should now have a booking group.
-- ---------------------------------------------------------

ALTER TABLE sample_bookings
ALTER COLUMN booking_group_id
SET NOT NULL;