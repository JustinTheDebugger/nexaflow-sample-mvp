-- ================================================================
-- Refurbished item customer sharing
-- ================================================================
--
-- Adds a non-guessable public token and sharing controls for
-- customer-facing refurbished item views.
--
-- Internal database IDs are never exposed in customer links.
-- ================================================================


ALTER TABLE refurbished_items
ADD COLUMN IF NOT EXISTS public_token UUID;


ALTER TABLE refurbished_items
ADD COLUMN IF NOT EXISTS customer_sharing_enabled BOOLEAN
NOT NULL DEFAULT FALSE;


ALTER TABLE refurbished_items
ADD COLUMN IF NOT EXISTS customer_summary TEXT;


ALTER TABLE refurbished_items
ADD COLUMN IF NOT EXISTS customer_sharing_enabled_at
TIMESTAMPTZ;


ALTER TABLE refurbished_items
ADD COLUMN IF NOT EXISTS customer_sharing_enabled_by TEXT;


-- Generate a token for existing refurbished items.

UPDATE refurbished_items
SET public_token = gen_random_uuid()
WHERE public_token IS NULL;


ALTER TABLE refurbished_items
ALTER COLUMN public_token
SET DEFAULT gen_random_uuid();


ALTER TABLE refurbished_items
ALTER COLUMN public_token
SET NOT NULL;


CREATE UNIQUE INDEX IF NOT EXISTS
idx_refurbished_items_public_token
ON refurbished_items(public_token);