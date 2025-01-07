CREATE DATABASE IF NOT EXISTS safana_db;
CREATE USER 'virtuosa'@'localhost' IDENTIFIED BY 'cello';
GRANT ALL PRIVILEGES ON safana_db.* TO 'virtuosa'@'%';
FLUSH PRIVILEGES;

