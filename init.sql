CREATE DATABASE IF NOT EXISTS safana_db;
CREATE USER 'rehsoz'@'localhost' IDENTIFIED BY 'beanz';
GRANT ALL PRIVILEGES ON safana_db.* TO 'rehsoz'@'%';
FLUSH PRIVILEGES;

