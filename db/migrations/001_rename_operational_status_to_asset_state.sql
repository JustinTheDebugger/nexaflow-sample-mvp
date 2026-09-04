-- ============================================================
-- Migration 001
-- Convert operational_status to controlled asset_state
-- ============================================================

-- 1. Rename the existing column
ALTER TABLE sample_master
    RENAME COLUMN operational_status TO asset_state;


-- 2. Convert existing values before introducing the enum
UPDATE sample_master
SET asset_state = 'Active'
WHERE asset_state = 'Available';


UPDATE sample_master
SET asset_state = 'Active'
WHERE asset_state IS NULL;


-- 3. Create controlled asset-state enum
CREATE TYPE sample_asset_state AS ENUM (
    'Active',
    'Inactive',
    'Damaged',
    'Retired',
    'Lost'
);


-- 4. Remove the old VARCHAR default before changing type
ALTER TABLE sample_master
    ALTER COLUMN asset_state DROP DEFAULT;


-- 5. Convert VARCHAR column to the enum
ALTER TABLE sample_master
    ALTER COLUMN asset_state
    TYPE sample_asset_state
    USING asset_state::sample_asset_state;


-- 6. Set the new default
ALTER TABLE sample_master
    ALTER COLUMN asset_state
    SET DEFAULT 'Active'::sample_asset_state;


-- 7. Keep asset state required
ALTER TABLE sample_master
    ALTER COLUMN asset_state SET NOT NULL;