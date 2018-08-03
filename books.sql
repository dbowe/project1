CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       first VARCHAR NOT NULL,
       last VARCHAR NOT NULL,
       username VARCHAR NOT NULL,
       password VARCHAR NOT NULL
);

CREATE TABLE books (
       isbn INTEGER PRIMARY KEY,
       title VARCHAR NOT NULL,
       author VARCHAR NOT NULL,
       publication INTEGER
);

CREATE TABLE reviews (
       id SERIAL PRIMARY KEY,
       isbn INTEGER REFERENCES books,
       user_id INTEGER REFERENCES users,
       rating NUMERIC(5),
       review VARCHAR(500)
);