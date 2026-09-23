-- =========================================================
-- Migration 009
-- Add temporary hold location for samples requiring
-- repair, replenishment, or operational follow-up.
-- =========================================================

INSERT INTO sample_locations (
    code,
    name,
    active
)
SELECT
    'H1',
    'Repair / Hold Area',
    TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM sample_locations
    WHERE code = 'H1'
);