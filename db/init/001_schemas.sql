-- Schema-per-service layout inside a single Postgres instance.
-- Deliberately one instance (not DB-per-service) so a Postgres outage
-- realistically takes down every business service at once.
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS orders;
CREATE SCHEMA IF NOT EXISTS notifications;
