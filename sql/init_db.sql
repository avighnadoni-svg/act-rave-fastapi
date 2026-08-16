-- ============================================================
-- ACT RAVE MOCK SOURCE DATABASE
-- PostgreSQL
-- ============================================================

-- ============================================================
-- DROP EXISTING TABLES
-- Child tables first because of foreign keys
-- ============================================================

DROP TABLE IF EXISTS data_query CASCADE;
DROP TABLE IF EXISTS protocol_deviation CASCADE;
DROP TABLE IF EXISTS lab_result CASCADE;
DROP TABLE IF EXISTS adverse_event CASCADE;
DROP TABLE IF EXISTS visit CASCADE;
DROP TABLE IF EXISTS subject CASCADE;
DROP TABLE IF EXISTS site CASCADE;
DROP TABLE IF EXISTS study CASCADE;


-- ============================================================
-- 1. STUDY
-- ============================================================

CREATE TABLE study
(
    study_id         VARCHAR(20) PRIMARY KEY,
    study_name       VARCHAR(200) NOT NULL,
    phase            VARCHAR(20),
    target_subjects  INTEGER,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. SITE
-- ============================================================

CREATE TABLE site
(
    site_id            VARCHAR(20) PRIMARY KEY,
    study_id           VARCHAR(20) NOT NULL,
    country            VARCHAR(100),
    investigator       VARCHAR(100),
    target_enrollment  INTEGER,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_site_study
        FOREIGN KEY (study_id)
        REFERENCES study(study_id)
);


-- ============================================================
-- 3. SUBJECT
-- ============================================================

CREATE TABLE subject
(
    subject_id       VARCHAR(20) PRIMARY KEY,
    study_id         VARCHAR(20) NOT NULL,
    site_id          VARCHAR(20) NOT NULL,
    gender           VARCHAR(10),
    age              INTEGER,
    status           VARCHAR(30),
    enrollment_date  DATE,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_subject_study
        FOREIGN KEY (study_id)
        REFERENCES study(study_id),

    CONSTRAINT fk_subject_site
        FOREIGN KEY (site_id)
        REFERENCES site(site_id)
);


-- ============================================================
-- 4. VISIT
-- ============================================================

CREATE TABLE visit
(
    visit_id       VARCHAR(20) PRIMARY KEY,
    subject_id     VARCHAR(20) NOT NULL,
    visit_name     VARCHAR(100),
    planned_date   DATE,
    actual_date    DATE,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_visit_subject
        FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
);


-- ============================================================
-- 5. ADVERSE EVENT
-- ============================================================

CREATE TABLE adverse_event
(
    ae_id           VARCHAR(20) PRIMARY KEY,
    subject_id      VARCHAR(20) NOT NULL,
    event_term      VARCHAR(200),
    severity        VARCHAR(30),
    serious         VARCHAR(1),
    event_date      DATE,
    reported_date   DATE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ae_subject
        FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
);


-- ============================================================
-- 6. LAB RESULT
-- ============================================================

CREATE TABLE lab_result
(
    lab_id         VARCHAR(20) PRIMARY KEY,
    subject_id     VARCHAR(20) NOT NULL,
    test_name      VARCHAR(100),
    result_value   NUMERIC(12,2),
    normal_low     NUMERIC(12,2),
    normal_high    NUMERIC(12,2),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lab_subject
        FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
);


-- ============================================================
-- 7. PROTOCOL DEVIATION
-- ============================================================

CREATE TABLE protocol_deviation
(
    deviation_id    VARCHAR(20) PRIMARY KEY,
    subject_id      VARCHAR(20) NOT NULL,
    site_id         VARCHAR(20) NOT NULL,
    deviation_type  VARCHAR(200),
    severity        VARCHAR(30),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pd_subject
        FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id),

    CONSTRAINT fk_pd_site
        FOREIGN KEY (site_id)
        REFERENCES site(site_id)
);


-- ============================================================
-- 8. DATA QUERY
-- ============================================================

CREATE TABLE data_query
(
    query_id       VARCHAR(20) PRIMARY KEY,
    subject_id     VARCHAR(20) NOT NULL,
    site_id        VARCHAR(20) NOT NULL,
    opened_date    DATE,
    resolved_date  DATE,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_query_subject
        FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id),

    CONSTRAINT fk_query_site
        FOREIGN KEY (site_id)
        REFERENCES site(site_id)
);


-- ============================================================
-- INDEXES FOR INCREMENTAL EXTRACTION
--
-- FastAPI will later run:
--
-- WHERE updated_at > :updated_since
-- ============================================================

CREATE INDEX idx_study_updated_at
ON study(updated_at);

CREATE INDEX idx_site_updated_at
ON site(updated_at);

CREATE INDEX idx_subject_updated_at
ON subject(updated_at);

CREATE INDEX idx_visit_updated_at
ON visit(updated_at);

CREATE INDEX idx_adverse_event_updated_at
ON adverse_event(updated_at);

CREATE INDEX idx_lab_result_updated_at
ON lab_result(updated_at);

CREATE INDEX idx_protocol_deviation_updated_at
ON protocol_deviation(updated_at);

CREATE INDEX idx_data_query_updated_at
ON data_query(updated_at);


-- ============================================================
-- SEED DATA
-- ============================================================


-- ============================================================
-- STUDY
-- ============================================================

INSERT INTO study
(
    study_id,
    study_name,
    phase,
    target_subjects
)
VALUES
(
    'ONC101',
    'Oncology Trial 101',
    'III',
    2000
);


-- ============================================================
-- SITE
-- ============================================================

INSERT INTO site
(
    site_id,
    study_id,
    country,
    investigator,
    target_enrollment
)
VALUES
('SITE01', 'ONC101', 'USA',     'Smith',  100),
('SITE02', 'ONC101', 'INDIA',   'Kumar',  120),
('SITE03', 'ONC101', 'UK',      'John',    90),
('SITE04', 'ONC101', 'GERMANY', 'Muller', 110),
('SITE05', 'ONC101', 'INDIA',   'Reddy',  100);


-- ============================================================
-- SUBJECT
-- ============================================================

INSERT INTO subject
(
    subject_id,
    study_id,
    site_id,
    gender,
    age,
    status,
    enrollment_date
)
VALUES
('SUB001', 'ONC101', 'SITE01', 'F', 52, 'ACTIVE',    '2026-01-05'),
('SUB002', 'ONC101', 'SITE01', 'M', 61, 'ACTIVE',    '2026-01-07'),
('SUB003', 'ONC101', 'SITE02', 'F', 47, 'ACTIVE',    '2026-01-10'),
('SUB004', 'ONC101', 'SITE02', 'M', 55, 'WITHDRAWN', '2026-01-12'),
('SUB005', 'ONC101', 'SITE03', 'F', 63, 'ACTIVE',    '2026-01-15');


-- ============================================================
-- VISIT
-- ============================================================

INSERT INTO visit
(
    visit_id,
    subject_id,
    visit_name,
    planned_date,
    actual_date
)
VALUES
('V001', 'SUB001', 'VISIT_1', '2026-02-01', '2026-02-01'),
('V002', 'SUB002', 'VISIT_1', '2026-02-01', '2026-02-06'),
('V003', 'SUB003', 'VISIT_1', '2026-02-03', '2026-02-03'),
('V004', 'SUB004', 'VISIT_1', '2026-02-04', NULL),
('V005', 'SUB005', 'VISIT_1', '2026-02-05', '2026-02-08');


-- ============================================================
-- ADVERSE EVENT
-- ============================================================

INSERT INTO adverse_event
(
    ae_id,
    subject_id,
    event_term,
    severity,
    serious,
    event_date,
    reported_date
)
VALUES
('AE001', 'SUB001', 'Nausea',      'MILD',     'N', '2026-02-01', '2026-02-01'),
('AE002', 'SUB002', 'Liver Injury', 'SEVERE',   'Y', '2026-02-02', '2026-02-05'),
('AE003', 'SUB003', 'Headache',     'MILD',     'N', '2026-02-03', '2026-02-03'),
('AE004', 'SUB004', 'Neutropenia',  'SEVERE',   'Y', '2026-02-04', '2026-02-04'),
('AE005', 'SUB005', 'Fever',        'MODERATE', 'N', '2026-02-05', '2026-02-08');


-- ============================================================
-- LAB RESULT
-- ============================================================

INSERT INTO lab_result
(
    lab_id,
    subject_id,
    test_name,
    result_value,
    normal_low,
    normal_high
)
VALUES
('L001', 'SUB001', 'ALT', 38,  10, 40),
('L002', 'SUB002', 'ALT', 125, 10, 40),
('L003', 'SUB003', 'ALT', 32,  10, 40),
('L004', 'SUB004', 'WBC', 2.1, 4,  11),
('L005', 'SUB005', 'ALT', 47,  10, 40);


-- ============================================================
-- PROTOCOL DEVIATION
-- ============================================================

INSERT INTO protocol_deviation
(
    deviation_id,
    subject_id,
    site_id,
    deviation_type,
    severity
)
VALUES
('PD001', 'SUB002', 'SITE01', 'Visit Window',     'MAJOR'),
('PD002', 'SUB004', 'SITE02', 'Missed Visit',     'MAJOR'),
('PD003', 'SUB004', 'SITE02', 'Medication Error', 'CRITICAL'),
('PD004', 'SUB005', 'SITE03', 'Visit Window',     'MINOR');


-- ============================================================
-- DATA QUERY
-- ============================================================

INSERT INTO data_query
(
    query_id,
    subject_id,
    site_id,
    opened_date,
    resolved_date
)
VALUES
('Q001', 'SUB001', 'SITE01', '2026-02-01', '2026-02-02'),
('Q002', 'SUB002', 'SITE01', '2026-02-02', '2026-02-10'),
('Q003', 'SUB004', 'SITE02', '2026-02-04', NULL),
('Q004', 'SUB005', 'SITE03', '2026-02-05', '2026-02-07');


-- ============================================================
-- VERIFY RECORD COUNTS
-- ============================================================

SELECT 'study' AS table_name, COUNT(*) AS record_count
FROM study

UNION ALL

SELECT 'site', COUNT(*)
FROM site

UNION ALL

SELECT 'subject', COUNT(*)
FROM subject

UNION ALL

SELECT 'visit', COUNT(*)
FROM visit

UNION ALL

SELECT 'adverse_event', COUNT(*)
FROM adverse_event

UNION ALL

SELECT 'lab_result', COUNT(*)
FROM lab_result

UNION ALL

SELECT 'protocol_deviation', COUNT(*)
FROM protocol_deviation

UNION ALL

SELECT 'data_query', COUNT(*)
FROM data_query

ORDER BY table_name;