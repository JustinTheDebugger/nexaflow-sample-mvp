-- ============================================================
-- Migration 011
-- Refurbished Media
--
-- Extends sample_media so repair/refurbishment photos can be
-- classified and selected for customer-facing use.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Customer-visible flag
-- ------------------------------------------------------------

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS
    customer_visible BOOLEAN
    NOT NULL
    DEFAULT FALSE;


-- ------------------------------------------------------------
-- 2. Refurbished item relationship
-- ------------------------------------------------------------

ALTER TABLE sample_media
ADD COLUMN IF NOT EXISTS
    refurbished_item_id UUID NULL;


-- Add FK separately so migration remains easy to inspect.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'sample_media_refurbished_item_id_fkey'
    ) THEN

        ALTER TABLE sample_media
        ADD CONSTRAINT
            sample_media_refurbished_item_id_fkey
        FOREIGN KEY (
            refurbished_item_id
        )
        REFERENCES refurbished_items(id);

    END IF;
END
$$;


-- ------------------------------------------------------------
-- 3. Index
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS
    idx_sample_media_refurbished_item
ON sample_media (
    refurbished_item_id
);