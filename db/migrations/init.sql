CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY UNIQUE, 
    first_name TEXT,
    last_name TEXT,
    course INT,
    curator_id INT
);

CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    max_score INT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_task (
    user_id INTEGER, 
    task_id INTEGER, 
    score INT
);

CREATE TABLE IF NOT EXISTS curator (
    id INTEGER PRIMARY KEY UNIQUE, 
    first_name TEXT,
    last_name TEXT
);
