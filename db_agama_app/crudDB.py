# crudDB.py (updated with bcrypt login + CRUD user)
import mysql.connector
from mysql.connector import Error
import bcrypt

class CrudDB:
    def __init__(self, host="localhost", user="root", password="", database="db_agama", port=3306):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except Error as e:
            raise RuntimeError(f"Database connection failed: {e}")

    # -------------------- Login --------------------
    def login(self, username, password):
        self.cursor.execute("SELECT * FROM pengguna WHERE username=%s", (username,))
        user = self.cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return user
        return None

    # -------------------- CRUD JADWAL KAJIAN --------------------
    def tambah_kajian(self, tema, ustadz, tempat, tanggal, waktu):
        sql = "INSERT INTO jadwal_kajian (tema, ustadz, tempat, tanggal, waktu) VALUES (%s,%s,%s,%s,%s)"
        self.cursor.execute(sql, (tema, ustadz, tempat, tanggal, waktu))
        self.conn.commit()

    def ambil_semua_kajian(self):
        self.cursor.execute("SELECT * FROM jadwal_kajian ORDER BY tanggal, waktu")
        return self.cursor.fetchall()

    def update_kajian(self, id_kajian, tema, ustadz, tempat, tanggal, waktu):
        sql = "UPDATE jadwal_kajian SET tema=%s, ustadz=%s, tempat=%s, tanggal=%s, waktu=%s WHERE id_kajian=%s"
        self.cursor.execute(sql, (tema, ustadz, tempat, tanggal, waktu, id_kajian))
        self.conn.commit()

    def hapus_kajian(self, id_kajian):
        self.cursor.execute("DELETE FROM jadwal_kajian WHERE id_kajian=%s", (id_kajian,))
        self.conn.commit()

    # -------------------- CRUD PENGGUNA --------------------
    def ambil_semua_pengguna(self):
        self.cursor.execute("SELECT id_pengguna, nama, username, peran FROM pengguna ORDER BY id_pengguna ASC")
        return self.cursor.fetchall()

    def tambah_pengguna(self, nama, username, password, peran):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sql = "INSERT INTO pengguna (nama, username, password, peran) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(sql, (nama, username, hashed, peran))
        self.conn.commit()

    def update_pengguna(self, id_pengguna, nama, username, password, peran):
        if password.strip():
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = "UPDATE pengguna SET nama=%s, username=%s, password=%s, peran=%s WHERE id_pengguna=%s"
            vals = (nama, username, hashed, peran, id_pengguna)
        else:
            sql = "UPDATE pengguna SET nama=%s, username=%s, peran=%s WHERE id_pengguna=%s"
            vals = (nama, username, peran, id_pengguna)
        self.cursor.execute(sql, vals)
        self.conn.commit()

    def hapus_pengguna(self, id_pengguna):
        self.cursor.execute("DELETE FROM pengguna WHERE id_pengguna=%s", (id_pengguna,))
        self.conn.commit()

    def close(self):
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()
