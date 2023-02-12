DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_ha TEXT NOT NULL
);

INSERT INTO user (username, password_ha)
VALUES ('admin', 'ISMvKXpXpadDiUoOSoAfww==');