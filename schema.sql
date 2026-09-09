CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE authorized_channels (
    id SERIAL PRIMARY KEY,
    telegram_chat_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    title VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reaction_bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    telegram_bot_id BIGINT UNIQUE NOT NULL,
    token_encrypted TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_error_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE reaction_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    telegram_chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    post_url TEXT NOT NULL,
    emoji VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    total_tasks INT DEFAULT 0,
    successful_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    pending_tasks INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE reaction_tasks (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL REFERENCES reaction_jobs(job_id) ON DELETE CASCADE,
    bot_id BIGINT NOT NULL REFERENCES reaction_bots(telegram_bot_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    attempts INT DEFAULT 0,
    error_code INT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(job_id, bot_id)
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    admin_telegram_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    job_id VARCHAR(100),
    target_chat_id BIGINT,
    target_message_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_reaction_jobs_status ON reaction_jobs(status);
CREATE INDEX idx_reaction_tasks_status ON reaction_tasks(status);
CREATE INDEX idx_reaction_tasks_job_id ON reaction_tasks(job_id);
