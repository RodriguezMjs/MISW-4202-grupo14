-- Usuario de replicación (Replica lo usa para conectarse al Primary)
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_pass';

-- Las tablas se crean directamente en travelhub
-- (Docker ya creó la DB por nosotros via POSTGRES_DB)
CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    available_rooms INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Datos de prueba para validar que la replicación funciona
INSERT INTO hotels (name, city, available_rooms) VALUES
    ('Hotel Bogotá Plaza', 'Bogotá', 45),
    ('Hotel Cartagena Bay', 'Cartagena', 12),
    ('Hotel Medellín Centro', 'Medellín', 30);
