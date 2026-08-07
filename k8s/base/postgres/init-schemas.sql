-- Kept in sync with db/init/001_schemas.sql (used for local docker-compose).
-- Duplicated here because kustomize's configMapGenerator cannot reference
-- files outside its own kustomization root.
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS orders;
CREATE SCHEMA IF NOT EXISTS notifications;
