-- ============================================================
-- NexaFlow Sample Management MVP
-- DEVELOPMENT RESET ONLY
--
-- WARNING:
-- Deletes all existing sample-management data.
-- ============================================================

DROP TABLE IF EXISTS sample_media CASCADE;
DROP TABLE IF EXISTS sample_condition_reports CASCADE;
DROP TABLE IF EXISTS sample_bookings CASCADE;
DROP TABLE IF EXISTS sample_events CASCADE;
DROP TABLE IF EXISTS sample_products CASCADE;
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS sample_id_counters CASCADE;
DROP TABLE IF EXISTS sample_locations CASCADE;
DROP TABLE IF EXISTS sample_types CASCADE;