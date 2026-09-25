-- Swahili Concern Classification System
-- Database Schema
-- Author: Obonyo Paul Rapando, 169688

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO categories (category_name) VALUES
    ('Food Security'),
    ('Health'),
    ('Shelter'),
    ('Safety')
ON CONFLICT DO NOTHING;

-- Residents table
CREATE TABLE IF NOT EXISTS residents (
    resident_id         SERIAL PRIMARY KEY,
    phone_number        VARCHAR(20),
    settlement_village  VARCHAR(100) NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CBOs table
CREATE TABLE IF NOT EXISTS cbos (
    cbo_id              SERIAL PRIMARY KEY,
    organisation_name   VARCHAR(200) NOT NULL,
    focus_category_id   INTEGER REFERENCES categories(category_id),
    contact_email       VARCHAR(200) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Concerns table
CREATE TABLE IF NOT EXISTS concerns (
    concern_id           SERIAL PRIMARY KEY,
    resident_id          INTEGER REFERENCES residents(resident_id),
    audio_file_path      VARCHAR(500),
    transcribed_text     TEXT,
    predicted_category   INTEGER REFERENCES categories(category_id),
    confidence_score     FLOAT,
    is_flagged           BOOLEAN DEFAULT FALSE,
    settlement_village   VARCHAR(100),
    submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routing log table
CREATE TABLE IF NOT EXISTS routing_log (
    log_id             SERIAL PRIMARY KEY,
    concern_id         INTEGER REFERENCES concerns(concern_id),
    cbo_id             INTEGER REFERENCES cbos(cbo_id),
    routing_timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review queue table
CREATE TABLE IF NOT EXISTS review_queue (
    queue_id            SERIAL PRIMARY KEY,
    concern_id          INTEGER REFERENCES concerns(concern_id),
    flagged_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by         INTEGER REFERENCES cbos(cbo_id),
    review_decision     VARCHAR(50),
    corrected_category  INTEGER REFERENCES categories(category_id)
);
