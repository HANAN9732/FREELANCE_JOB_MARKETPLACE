-- ----------------------------------------------------------------------------
-- USERS
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id                      CHAR(36)        NOT NULL PRIMARY KEY,
    name                    VARCHAR(150)    NOT NULL,
    email                   VARCHAR(255)    NOT NULL,
    password_hash           VARCHAR(255)    NOT NULL,
    role                    ENUM('user','admin') NOT NULL DEFAULT 'user',
    bio                     TEXT            NULL,
    avatar_path             VARCHAR(500)    NULL,
    rating                  DECIMAL(3,2)    NOT NULL DEFAULT 0.00,
    reviews_received_count  INT UNSIGNED    NOT NULL DEFAULT 0,
    profile_completeness    TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- 0-100 (%)
    is_suspended            BOOLEAN         NOT NULL DEFAULT FALSE,
    suspended_at            TIMESTAMP       NULL,

    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMP       NULL,

    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_rating (rating),
    FULLTEXT INDEX ft_users_name_bio (name, bio)
) 

-- ----------------------------------------------------------------------------
-- REFRESH TOKENS (needed for JWT refresh-token flow + revocation on logout)
-- ----------------------------------------------------------------------------
CREATE TABLE refresh_tokens (
    id            CHAR(36)   NOT NULL PRIMARY KEY,
    user_id       CHAR(36)   NOT NULL,
    token_hash    VARCHAR(255) NOT NULL,   -- store a hash, never the raw token
    expires_at    TIMESTAMP  NOT NULL,
    revoked_at    TIMESTAMP  NULL,
    created_at    TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_refresh_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_refresh_user (user_id),
    UNIQUE KEY uq_refresh_token_hash (token_hash)
) 

-- ----------------------------------------------------------------------------
-- SKILLS (tag system, many-to-many with users and jobs)
-- ----------------------------------------------------------------------------
CREATE TABLE skills (
    id          CHAR(36)     NOT NULL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  TIMESTAMP    NULL,
    UNIQUE KEY uq_skills_name (name)
)

CREATE TABLE user_skills (
    user_id     CHAR(36) NOT NULL,
    skill_id    CHAR(36) NOT NULL,

    PRIMARY KEY (user_id, skill_id),
    CONSTRAINT fk_user_skills_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    CONSTRAINT fk_user_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    INDEX idx_user_skills_skill (skill_id)
)

-- ----------------------------------------------------------------------------
-- JOBS
-- ----------------------------------------------------------------------------
CREATE TABLE jobs (
    id                      CHAR(36)        NOT NULL PRIMARY KEY,
    client_id               CHAR(36)        NOT NULL,

    title                   VARCHAR(200)    NOT NULL,
    description             TEXT            NOT NULL,
    budget                  DECIMAL(12,2)   NOT NULL,
    deadline                DATE            NOT NULL,

    status                  ENUM('open','assigned','in_progress','completed','closed')
                                             NOT NULL DEFAULT 'open',

    -- denormalized pointer, set when a proposal is accepted (Open -> Assigned)
    assigned_freelancer_id  CHAR(36)        NULL,

    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,
    deleted_at               TIMESTAMP      NULL,

    CONSTRAINT fk_jobs_client    FOREIGN KEY (client_id)              REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_jobs_assignee  FOREIGN KEY (assigned_freelancer_id) REFERENCES users(id) ON DELETE SET NULL,

    INDEX idx_jobs_status (status),
    INDEX idx_jobs_client (client_id),
    INDEX idx_jobs_deadline_status (deadline, status),  -- for the scheduled auto-close job
    FULLTEXT INDEX ft_jobs_title_desc (title, description)
) 
CREATE TABLE job_skills (
    job_id      CHAR(36) NOT NULL,
    skill_id    CHAR(36) NOT NULL,

    PRIMARY KEY (job_id, skill_id),
    CONSTRAINT fk_job_skills_job   FOREIGN KEY (job_id)   REFERENCES jobs(id)   ON DELETE CASCADE,
    CONSTRAINT fk_job_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    INDEX idx_job_skills_skill (skill_id)
) 
-- ----------------------------------------------------------------------------
-- PROPOSALS
-- ----------------------------------------------------------------------------
CREATE TABLE proposals (
    id                CHAR(36)      NOT NULL PRIMARY KEY,
    job_id            CHAR(36)      NOT NULL,
    freelancer_id     CHAR(36)      NOT NULL,

    bid_amount        DECIMAL(12,2) NOT NULL,
    cover_letter_path VARCHAR(500)  NOT NULL,   -- PDF only, validated in app layer
    delivery_time_days INT UNSIGNED NOT NULL,

    status            ENUM('pending','accepted','rejected','withdrawn')
                                     NOT NULL DEFAULT 'pending',

    created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
    deleted_at        TIMESTAMP     NULL,

    CONSTRAINT fk_proposals_job         FOREIGN KEY (job_id)        REFERENCES jobs(id)  ON DELETE CASCADE,
    CONSTRAINT fk_proposals_freelancer  FOREIGN KEY (freelancer_id) REFERENCES users(id) ON DELETE RESTRICT,

    UNIQUE KEY uq_job_freelancer (job_id, freelancer_id),  -- one proposal per job (see note #6 above)
    INDEX idx_proposals_job (job_id),
    INDEX idx_proposals_freelancer (freelancer_id),
    INDEX idx_proposals_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- MESSAGES (one thread per Assigned job, scoped to client + freelancer)
-- ----------------------------------------------------------------------------
CREATE TABLE messages (
    id          CHAR(36)  NOT NULL PRIMARY KEY,
    job_id      CHAR(36)  NOT NULL,
    sender_id   CHAR(36)  NOT NULL,

    content     TEXT      NOT NULL,
    read_at     TIMESTAMP NULL,

    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at  TIMESTAMP NULL,

    CONSTRAINT fk_messages_job    FOREIGN KEY (job_id)    REFERENCES jobs(id)  ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE RESTRICT,

    INDEX idx_messages_job_created (job_id, created_at)  -- for paginated thread fetch
) 

-- ----------------------------------------------------------------------------
-- REVIEWS (exactly 1 per job by the client, targeting the freelancer)
-- ----------------------------------------------------------------------------
CREATE TABLE reviews (
    id           CHAR(36)     NOT NULL PRIMARY KEY,
    job_id       CHAR(36)     NOT NULL,
    reviewer_id  CHAR(36)     NOT NULL,
    target_id    CHAR(36)     NOT NULL,

    rating       TINYINT UNSIGNED NOT NULL,
    comment      TEXT         NULL,

    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at   TIMESTAMP    NULL,

    CONSTRAINT fk_reviews_job      FOREIGN KEY (job_id)      REFERENCES jobs(id)  ON DELETE CASCADE,
    CONSTRAINT fk_reviews_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reviews_target   FOREIGN KEY (target_id)   REFERENCES users(id) ON DELETE RESTRICT,

    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    UNIQUE KEY uq_job_reviewer (job_id, reviewer_id),
    INDEX idx_reviews_target (target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- NOTIFICATIONS
-- ----------------------------------------------------------------------------
CREATE TABLE notifications (
    id            CHAR(36)  NOT NULL PRIMARY KEY,
    user_id       CHAR(36)  NOT NULL,

    type          ENUM('new_proposal','proposal_accepted','proposal_rejected',
                        'new_message','job_status_change') NOT NULL,
    reference_id  CHAR(36)  NULL,   -- polymorphic: id of the job/proposal/message it refers to
    payload       JSON      NULL,  -- extra context for the frontend to render without another fetch

    is_read       BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user_read (user_id, is_read)
)


