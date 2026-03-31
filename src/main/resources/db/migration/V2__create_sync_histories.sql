CREATE TABLE sync_histories
(
    id                BIGSERIAL    NOT NULL PRIMARY KEY,
    sync_type         VARCHAR(10)  NOT NULL,
    target_year_month VARCHAR(7),
    status            VARCHAR(10)  NOT NULL DEFAULT 'RUNNING',
    total_count       INTEGER      NOT NULL DEFAULT 0,
    upsert_count      INTEGER      NOT NULL DEFAULT 0,
    closed_count      INTEGER      NOT NULL DEFAULT 0,
    error_message     VARCHAR(2000),
    started_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    finished_at       TIMESTAMP
);

CREATE INDEX idx_sync_histories_sync_type ON sync_histories (sync_type);
CREATE INDEX idx_sync_histories_started_at ON sync_histories (started_at DESC);
