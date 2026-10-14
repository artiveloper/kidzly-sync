CREATE TABLE daycares
(
    stcode        VARCHAR(20)  NOT NULL PRIMARY KEY,
    arcode        VARCHAR(10)  NOT NULL,
    sidoname      VARCHAR(50),
    sigunguname   VARCHAR(50),
    crname        VARCHAR(100) NOT NULL,
    crtypename    VARCHAR(50),
    crstatusname  VARCHAR(20),
    zipcode       VARCHAR(10),
    craddr        VARCHAR(200),
    crtelno       VARCHAR(20),
    crfaxno       VARCHAR(20),
    crhome        VARCHAR(200),
    la            VARCHAR(20),
    lo            VARCHAR(20),
    crcapat       INTEGER,
    crchcnt       INTEGER,
    nrtrroomcnt   INTEGER,
    nrtrroomsize  NUMERIC(10, 2),
    plgrdco       INTEGER,
    cctvinstlcnt  INTEGER,
    chcrtescnt    INTEGER,
    class_cnt_tot INTEGER,
    child_cnt_tot INTEGER,
    em_cnt_tot    INTEGER,
    ew_cnt_tot    INTEGER,
    crrepname     VARCHAR(50),
    crcnfmdt      VARCHAR(10),
    crstdate      VARCHAR(10),
    synced_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_daycares_arcode ON daycares (arcode);
CREATE INDEX idx_daycares_crstatusname ON daycares (crstatusname);
