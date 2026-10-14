CREATE TABLE sigungus
(
    arcode      VARCHAR(10)  NOT NULL PRIMARY KEY,
    sidoname    VARCHAR(50)  NOT NULL,
    sigunname   VARCHAR(50)  NOT NULL,
    synced_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sigungus_sidoname ON sigungus (sidoname);
