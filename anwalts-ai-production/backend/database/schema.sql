-- AnwaltsAI PostgreSQL Database Schema
-- Production-ready schema with proper indexing and constraints

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table with role-based access control
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'assistant' CHECK (role IN ('admin', 'assistant')),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Templates table for custom legal templates
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    type VARCHAR(50) DEFAULT 'document' CHECK (type IN ('document', 'email', 'clause')),
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Clauses library for reusable legal clauses
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[], -- Array of tags for better searchability
    language VARCHAR(10) DEFAULT 'de',
    is_favorite BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Clipboard entries for legal clipboard functionality
CREATE TABLE clipboard_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    source_type VARCHAR(50) DEFAULT 'manual' CHECK (source_type IN ('manual', 'template', 'ai_generated')),
    metadata JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions for JWT token management
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents for generated content tracking
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    template_id UUID REFERENCES templates(id),
    ai_model VARCHAR(100),
    ai_prompt TEXT,
    generation_time_ms INTEGER,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10, 6),
    quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analytics for AI usage tracking
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for compliance
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for optimal performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

CREATE INDEX idx_templates_user_id ON templates(user_id);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_type ON templates(type);
CREATE INDEX idx_templates_public ON templates(is_public);
CREATE INDEX idx_templates_usage ON templates(usage_count DESC);

CREATE INDEX idx_clauses_user_id ON clauses(user_id);
CREATE INDEX idx_clauses_category ON clauses(category);
CREATE INDEX idx_clauses_language ON clauses(language);
CREATE INDEX idx_clauses_favorite ON clauses(is_favorite);
CREATE INDEX idx_clauses_tags ON clauses USING GIN(tags);

CREATE INDEX idx_clipboard_user_id ON clipboard_entries(user_id);
CREATE INDEX idx_clipboard_expires ON clipboard_entries(expires_at);
CREATE INDEX idx_clipboard_source ON clipboard_entries(source_type);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_token ON sessions(token_hash);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_template ON documents(template_id);
CREATE INDEX idx_documents_created ON documents(created_at DESC);

CREATE INDEX idx_analytics_user ON analytics_events(user_id);
CREATE INDEX idx_analytics_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created ON analytics_events(created_at DESC);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clauses_updated_at BEFORE UPDATE ON clauses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired clipboard entries
CREATE OR REPLACE FUNCTION cleanup_expired_clipboard()
RETURNS void AS $$
BEGIN
    DELETE FROM clipboard_entries 
    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
END;
$$ language 'plpgsql';

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ language 'plpgsql';

-- Initial admin user (password: admin123 - change in production!)
INSERT INTO users (id, email, name, role, password_hash) VALUES
    (uuid_generate_v4(), 'admin@anwalts-ai.de', 'Administrator', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lwjga7NoWLNqJdlgC');

-- Sample clauses for German legal context
INSERT INTO clauses (user_id, category, title, content, tags, language) 
SELECT u.id, 'Vertragsrecht', 'Standard Haftungsausschluss', 
    'Der Auftragnehmer haftet nur für Schäden, die auf vorsätzliches oder grob fahrlässiges Verhalten zurückzuführen sind.',
    ARRAY['Haftung', 'Verträge', 'Standard'],
    'de'
FROM users u WHERE u.role = 'admin' LIMIT 1;

INSERT INTO clauses (user_id, category, title, content, tags, language)
SELECT u.id, 'Datenschutz', 'DSGVO Einverständniserklärung',
    'Ich erkläre mich damit einverstanden, dass meine personenbezogenen Daten gemäß der DSGVO verarbeitet werden.',
    ARRAY['DSGVO', 'Datenschutz', 'Einverständnis'],
    'de'
FROM users u WHERE u.role = 'admin' LIMIT 1;