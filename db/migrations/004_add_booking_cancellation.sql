ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(255);

ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;

ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;