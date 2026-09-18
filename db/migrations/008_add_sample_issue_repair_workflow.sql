-- =========================================================
-- Migration 008
-- Sample issue and repair workflow
-- =========================================================


-- ---------------------------------------------------------
-- 1. Sample Issues
-- One operational issue can be raised from a return,
-- inspection, or later manual report.
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE RESTRICT,

    booking_group_id UUID
        REFERENCES sample_booking_groups(id)
        ON DELETE SET NULL,

    return_check_id UUID
        REFERENCES sample_return_checks(id)
        ON DELETE SET NULL,

    issue_type VARCHAR(50) NOT NULL,

    issue_status VARCHAR(50) NOT NULL
        DEFAULT 'Open',

    description TEXT,

    reported_by VARCHAR(255),
    reported_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    assigned_to VARCHAR(255),

    resolution_action VARCHAR(50),
    resolution_notes TEXT,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT chk_sample_issue_type
        CHECK (
            issue_type IN (
                'Damaged',
                'Incomplete',
                'Not Returned'
            )
        ),

    CONSTRAINT chk_sample_issue_status
        CHECK (
            issue_status IN (
                'Open',
                'Under Review',
                'Under Repair',
                'Resolved',
                'Retired',
                'Converted to Refurbished'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    idx_sample_issues_sample_record
ON sample_issues(sample_record_id);


CREATE INDEX IF NOT EXISTS
    idx_sample_issues_status
ON sample_issues(issue_status);


-- ---------------------------------------------------------
-- 2. Repair Records
-- Separate repair work from the issue itself.
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_repairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    issue_id UUID NOT NULL
        REFERENCES sample_issues(id)
        ON DELETE RESTRICT,

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE RESTRICT,

    repair_status VARCHAR(50) NOT NULL
        DEFAULT 'Pending',

    repair_notes TEXT,

    repair_started_by VARCHAR(255),
    repair_started_at TIMESTAMPTZ,

    repair_completed_by VARCHAR(255),
    repair_completed_at TIMESTAMPTZ,

    completion_notes TEXT,

    final_disposition VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT chk_sample_repair_status
        CHECK (
            repair_status IN (
                'Pending',
                'In Progress',
                'Completed',
                'Cancelled'
            )
        ),

    CONSTRAINT chk_sample_repair_disposition
        CHECK (
            final_disposition IS NULL
            OR final_disposition IN (
                'Return to Sample Pool',
                'Convert to Refurbished',
                'Retire'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    idx_sample_repairs_issue
ON sample_repairs(issue_id);


CREATE INDEX IF NOT EXISTS
    idx_sample_repairs_sample
ON sample_repairs(sample_record_id);


-- ---------------------------------------------------------
-- 3. Sample Media
-- Stores metadata only.
-- Actual images will live in object storage.
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS sample_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sample_record_id UUID NOT NULL
        REFERENCES sample_master(id)
        ON DELETE CASCADE,

    booking_group_id UUID
        REFERENCES sample_booking_groups(id)
        ON DELETE SET NULL,

    issue_id UUID
        REFERENCES sample_issues(id)
        ON DELETE SET NULL,

    media_type VARCHAR(50) NOT NULL
        DEFAULT 'General',

    storage_provider VARCHAR(50),
    storage_path TEXT NOT NULL,

    original_filename TEXT,
    caption TEXT,

    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT chk_sample_media_type
        CHECK (
            media_type IN (
                'General',
                'Damage',
                'Repair',
                'Condition'
            )
        )
);

-- ---------------------------------------------------------
-- Add issue workflow fields to an existing sample_media
-- table when sample_media was created by an earlier
-- migration.
-- ---------------------------------------------------------

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS booking_group_id UUID
    REFERENCES sample_booking_groups(id)
    ON DELETE SET NULL;

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS issue_id UUID
    REFERENCES sample_issues(id)
    ON DELETE SET NULL;

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS media_type VARCHAR(50)
    DEFAULT 'General';

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50);

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS storage_path TEXT;

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS original_filename TEXT;

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS caption TEXT;

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS uploaded_by VARCHAR(255);

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ
    DEFAULT NOW();
    

CREATE INDEX IF NOT EXISTS
    idx_sample_media_sample
ON sample_media(sample_record_id);


CREATE INDEX IF NOT EXISTS
    idx_sample_media_issue
ON sample_media(issue_id);