-- FlyRank Internship - Backend Track - Assignment A3: Containerize your stack
-- Task table schema for PostgreSQL

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

-- Stretch index on 'done' column for optimized boolean query filtering
CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
