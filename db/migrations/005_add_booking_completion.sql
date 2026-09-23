ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS completed_by VARCHAR(255);

ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE sample_booking_groups
ADD COLUMN IF NOT EXISTS completion_notes TEXT;