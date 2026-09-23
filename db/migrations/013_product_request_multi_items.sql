-- ============================================================
-- Migration 013
-- Product Request multi-item structure
--
-- Current database state:
-- - sample_requests already has request_number
-- - no existing Product Request records
-- - sample_request_counters does not exist
-- - sample_request_items does not exist
-- ============================================================


-- ------------------------------------------------------------
-- 1. Product Request number counter
-- ------------------------------------------------------------

CREATE TABLE sample_request_counters (
    id BIGSERIAL PRIMARY KEY,

    counter_name VARCHAR(50)
        NOT NULL
        UNIQUE,

    last_number INTEGER
        NOT NULL
        DEFAULT 0,

    updated_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW()
);


INSERT INTO sample_request_counters (
    counter_name,
    last_number
)
VALUES (
    'PRODUCT_REQUEST',
    0
);


-- ------------------------------------------------------------
-- 2. Create Product Request items
--
-- One request can contain multiple products.
-- ------------------------------------------------------------

CREATE TABLE sample_request_items (
    id UUID PRIMARY KEY
        DEFAULT gen_random_uuid(),

    request_id UUID NOT NULL
        REFERENCES sample_requests(id)
        ON DELETE CASCADE,

    product_code VARCHAR NOT NULL
        REFERENCES products(product_code),

    product_name TEXT NOT NULL,

    quantity_required INTEGER
        NOT NULL
        DEFAULT 1,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT valid_sample_request_item_quantity
        CHECK (quantity_required > 0),

    CONSTRAINT unique_product_per_sample_request
        UNIQUE (
            request_id,
            product_code
        )
);


CREATE INDEX idx_sample_request_items_request_id
ON sample_request_items(request_id);


CREATE INDEX idx_sample_request_items_product_code
ON sample_request_items(product_code);


-- ------------------------------------------------------------
-- 3. Remove old single-product fields from request header
--
-- There are no existing Product Request records,
-- so no data migration is required.
-- ------------------------------------------------------------

ALTER TABLE sample_requests
DROP CONSTRAINT IF EXISTS
    sample_requests_product_code_fkey;


ALTER TABLE sample_requests
DROP COLUMN product_code;

ALTER TABLE sample_requests
DROP COLUMN requested_sample_name;

ALTER TABLE sample_requests
DROP COLUMN category_code;

ALTER TABLE sample_requests
DROP COLUMN quantity_required;

ALTER TABLE sample_requests
DROP COLUMN request_notes;


-- ------------------------------------------------------------
-- 4. Requester profile fields
--
-- These remain available for future authentication/profile
-- integration but are not required when creating a request.
-- ------------------------------------------------------------

ALTER TABLE sample_requests
ALTER COLUMN requester_email DROP NOT NULL;