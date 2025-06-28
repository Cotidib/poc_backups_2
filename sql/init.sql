-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS test_db;
USE test_db;

-- Crear tabla de empleados
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insertar algunos datos de ejemplo
INSERT INTO employees (name, position) VALUES
    ('Juan Perez', 'Developer'),
    ('Maria Garcia', 'Project Manager'),
    ('Carlos Rodriguez', 'QA Engineer');

-- Dar privilegios al usuario test_user
-- Primero asegurarnos de que el usuario existe
CREATE USER IF NOT EXISTS 'test_user'@'%' IDENTIFIED BY 'test_password';

-- Dar privilegios para la base de datos test_db
GRANT ALL PRIVILEGES ON test_db.* TO 'test_user'@'%';

-- Dar privilegios adicionales necesarios para binary log
GRANT REPLICATION CLIENT ON *.* TO 'test_user'@'%';
GRANT REPLICATION SLAVE ON *.* TO 'test_user'@'%';
GRANT SUPER ON *.* TO 'test_user'@'%';

-- Aplicar los cambios de privilegios
FLUSH PRIVILEGES; 