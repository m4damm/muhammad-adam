-- create_db.sql (updated with hashed passwords)
CREATE DATABASE IF NOT EXISTS db_agama CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_agama;

-- Tabel jadwal kajian
CREATE TABLE IF NOT EXISTS jadwal_kajian (
    id_kajian INT AUTO_INCREMENT PRIMARY KEY,
    tema VARCHAR(255) NOT NULL,
    ustadz VARCHAR(150) NOT NULL,
    tempat VARCHAR(255) NOT NULL,
    tanggal DATE NOT NULL,
    waktu TIME NOT NULL,
    dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Tabel pengguna
CREATE TABLE IF NOT EXISTS pengguna (
    id_pengguna INT AUTO_INCREMENT PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    peran ENUM('admin','petugas') DEFAULT 'petugas'
) ENGINE=InnoDB;

-- Insert default users (with bcrypt hash)
DELETE FROM pengguna;

INSERT INTO pengguna (nama, username, password, peran) VALUES
('Administrator', 'admin', '$2b$12$V6gCdOjhnZCIZAShItfV.e6rfDOb5MUKvMmtvSuRwBtb3j82hKyM.', 'admin'),  -- password: admin123
('Petugas', 'petugas', '$2b$12$5uGz02yofKuUbZVaVbr7AOWkExX6f0J4W3ZKNM8mV46mYwyMBV0x6', 'petugas');  -- password: petugas123
