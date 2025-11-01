-- Snipers Bot Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE contract_role AS ENUM ('rp','tl','pr','clrd','ts','qc','uploader');
CREATE TYPE txn_type AS ENUM ('earn','spend','transfer','penalty','refund','loan','seizure');
CREATE TYPE bounty_status AS ENUM ('open','claimed','resolved','cancelled');
CREATE TYPE loan_status AS ENUM ('requested','active','repaid','defaulted','seized');

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    discord_id VARCHAR(32) UNIQUE NOT NULL,
    codename VARCHAR(64),
    coins BIGINT NOT NULL DEFAULT 0 CHECK (coins >= 0),
    xp BIGINT NOT NULL DEFAULT 0,
    rank VARCHAR(32) DEFAULT 'Recruit',
    contracts_completed INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ
);

-- Contracts Table
CREATE TABLE IF NOT EXISTS contracts (
    id BIGSERIAL PRIMARY KEY,
    assigner_id BIGINT REFERENCES users(id),
    assignee_id BIGINT REFERENCES users(id),
    role contract_role NOT NULL,
    series TEXT NOT NULL,
    chapter INT NOT NULL,
    reward_amount BIGINT NOT NULL CHECK (reward_amount >= 0),
    status VARCHAR(20) DEFAULT 'active',
    proof_url TEXT,
    receipt_url TEXT,
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_contracts_assignee_active ON contracts(assignee_id) WHERE status = 'active';

-- Contract Submissions Table
CREATE TABLE IF NOT EXISTS contract_submissions (
    id BIGSERIAL PRIMARY KEY,
    contract_id BIGINT REFERENCES contracts(id) ON DELETE CASCADE,
    submitter_id BIGINT REFERENCES users(id),
    proof_url TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bounties Table
CREATE TABLE IF NOT EXISTS bounties (
    id BIGSERIAL PRIMARY KEY,
    target_id BIGINT REFERENCES users(id),
    placed_by_id BIGINT REFERENCES users(id),
    amount BIGINT NOT NULL CHECK (amount >= 100),
    reason TEXT NOT NULL,
    status bounty_status DEFAULT 'open',
    placed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    claim_proof TEXT,
    claimant_id BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bounties_open ON bounties(status) WHERE status = 'open';

-- Loans Table
CREATE TABLE IF NOT EXISTS loans (
    id BIGSERIAL PRIMARY KEY,
    borrower_id BIGINT REFERENCES users(id),
    lender_id BIGINT REFERENCES users(id),
    principal BIGINT NOT NULL CHECK (principal > 0),
    interest_rate NUMERIC(5,2) NOT NULL CHECK (interest_rate >= 0),
    due_at TIMESTAMPTZ NOT NULL,
    status loan_status DEFAULT 'requested',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    type txn_type NOT NULL,
    amount BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    reason TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);

-- Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    id BIGSERIAL PRIMARY KEY,
    discord_id VARCHAR(32) UNIQUE,
    owner_id BIGINT REFERENCES users(id),
    name TEXT NOT NULL,
    cost_total BIGINT NOT NULL,
    cost_per_user BIGINT NOT NULL,
    hidden_owner BOOLEAN DEFAULT false,
    expires_at TIMESTAMPTZ,
    receipt_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    actor_id BIGINT REFERENCES users(id),
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) UNIQUE,
    joke_mode VARCHAR(20) DEFAULT 'safe',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
