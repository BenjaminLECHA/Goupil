CREATE TABLE statuts (
    statut_id SERIAL PRIMARY KEY,
    nom VARCHAR(100)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE app (
    app_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    acronyme VARCHAR(20) UNIQUE NOT NULL,
    git_id INTEGER NOT NULL,
    git_url VARCHAR(100) NOT NULL,
    private_token VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE user_app (
    user_app_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    app_id INTEGER REFERENCES app(app_id) ON DELETE CASCADE,
    is_dev BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE issues (
    issue_id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    description TEXT,
    git_id INTEGER,
    is_closed BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    app_id INTEGER REFERENCES app(app_id) ON DELETE CASCADE,
    web_url VARCHAR(255)
);

CREATE TABLE categorie_demande (
    categorie_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    color VARCHAR(7)
);

CREATE TABLE demandes (
    demande_id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    description TEXT,
    statut_id INTEGER REFERENCES statuts(statut_id),
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    app_id INTEGER REFERENCES app(app_id) ON DELETE CASCADE,
    categorie_id INTEGER REFERENCES categorie_demande(categorie_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE demande_issue (
    demande_issue_id SERIAL PRIMARY KEY,
    demande_id INTEGER REFERENCES demandes(demande_id) ON DELETE CASCADE,
    issue_id INTEGER REFERENCES issues(issue_id) ON DELETE CASCADE
);

CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    demande_id INTEGER REFERENCES demandes(demande_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE milestones (
    milestone_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    due_date DATE,
    is_closed BOOLEAN,
    git_id INTEGER,
    is_deleted BOOLEAN DEFAULT FALSE,
    app_id INTEGER REFERENCES app(app_id) ON DELETE CASCADE
);

CREATE TABLE millestone_issue (
    millestone_issue_id SERIAL PRIMARY KEY,
    milestone_id INTEGER REFERENCES milestones(milestone_id) ON DELETE CASCADE,
    issue_id INTEGER REFERENCES issues(issue_id) ON DELETE CASCADE
);

CREATE TABLE labels (
    label_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    git_id INTEGER,
    color VARCHAR(7),
    is_deleted BOOLEAN DEFAULT FALSE,
    app_id INTEGER REFERENCES app(app_id) ON DELETE CASCADE
);

CREATE TABLE label_issue (
    label_issue_id SERIAL PRIMARY KEY,
    label_id INTEGER REFERENCES labels(label_id) ON DELETE CASCADE,
    issue_id INTEGER REFERENCES issues(issue_id) ON DELETE CASCADE
);

CREATE TABLE pieces_jointes (
    piece_jointe_id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    demande_id INTEGER REFERENCES demandes(demande_id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES messages(message_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO "statuts" ("nom") VALUES
('Nouvelle demande'),
('En cours d''échange'),
('Transformé en Issue'),
('Issue associé réalisé'),
('Demande fermé');

INSERT INTO "categorie_demande" ("nom", "color") VALUES
('Bug', '#ef4444'),
('Fonctionnalité', '#3b82f6'),
('Autre', '#6b7280');

INSERT INTO "users" (username, email, password_hash, is_active, is_admin) VALUES
('admin', 'goupil@mail.com', 'scrypt:32768:8:1$BfYIQV93e3IEe3fE$5508b37d47a37203d3be7f5de0e3d65b53f57761fbb5c6441cc0d8df732effb187e8dbcea1e2d2da810898995cd5fea26892ba32cfaf998749ef326d2e12d313', True, True);