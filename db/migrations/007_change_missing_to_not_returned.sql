-- =========================================================
-- Migration 007
-- Rename return outcome "Missing" to "Not Returned"
-- =========================================================

-- ---------------------------------------------------------
-- 1. Drop existing return status constraint
-- ---------------------------------------------------------

ALTER TABLE sample_return_checks
DROP CONSTRAINT IF EXISTS chk_sample_return_status;


-- ---------------------------------------------------------
-- 2. Convert any existing return records
-- ---------------------------------------------------------

UPDATE sample_return_checks
SET return_status = 'Not Returned'
WHERE return_status = 'Missing';


-- ---------------------------------------------------------
-- 3. Add revised constraint
-- ---------------------------------------------------------

ALTER TABLE sample_return_checks
ADD CONSTRAINT chk_sample_return_status
CHECK (
    return_status IN (
        'Good',
        'Damaged',
        'Incomplete',
        'Not Returned'
    )
);