DROP DATABASE IF EXISTS catalog;
CREATE DATABASE catalog;
\c catalog

CREATE TABLE users(
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(100),
	picture TEXT
);


CREATE TABLE restaurants(
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	picture TEXT,
	user_id INT REFERENCES users(id)
);


CREATE TABLE menus(
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	price INT,
	description TEXT,
	picture TEXT,
	restaurant_id INT REFERENCES restaurants(id),
	user_id INT REFERENCES users(id)
);
