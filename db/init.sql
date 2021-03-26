CREATE TABLE team (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR (100) UNIQUE NOT NULL
);

CREATE TABLE referee (
    id SERIAL PRIMARY KEY,
    ref_name VARCHAR (255) UNIQUE NOT NULL
);

CREATE TABLE match (
    id SERIAL PRIMARY KEY,
    home_team_id INT,
    away_team_id INT,
    match_time TIMESTAMP,
    ref_id INT REFERENCES referee (id)
);

CREATE TABLE event_type (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR (100) UNIQUE NOT NULL
);

CREATE TABLE player (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR (255) UNIQUE NOT NULL,
    team_id INT REFERENCES team (id)
);

CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    event_type_id INT REFERENCES event_type (id),
    event_player_1_id INT REFERENCES player (id),
    event_player_2_id INT REFERENCES player (id),
    minute INT,
    match_id INT REFERENCES match (id)
);

