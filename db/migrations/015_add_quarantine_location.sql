-- Migration 015
-- Add inspection / quarantine location for damaged samples.

INSERT INTO sample_locations (
    code,
    name
)
SELECT
    'Q1',
    'Inspection / Quarantine'
WHERE NOT EXISTS (
    SELECT 1
    FROM sample_locations
    WHERE code = 'Q1'
);