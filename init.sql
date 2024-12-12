CREATE DATABASE IF NOT EXISTS reknown_db;
CREATE USER 'rehsoz'@'localhost' IDENTIFIED BY 'beanz';
GRANT ALL PRIVILEGES ON reknown_db.* TO 'rehsoz'@'%';
FLUSH PRIVILEGES;

