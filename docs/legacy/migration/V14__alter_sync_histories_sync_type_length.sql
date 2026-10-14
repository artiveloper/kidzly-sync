ALTER TABLE sync_histories ALTER COLUMN sync_type TYPE VARCHAR(20);

COMMENT ON COLUMN sync_histories.sync_type IS '동기화 유형 (FULL / DELTA / PLAYGROUND)';
