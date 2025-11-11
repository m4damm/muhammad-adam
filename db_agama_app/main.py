# main.py
# Loads login.ui then main.ui (tabs). Handles secure login (via CrudDB.login) and user management + kajian CRUD.
# Requirements: pip install PySide6 mysql-connector-python bcrypt
import sys, csv, os
from PySide6.QtWidgets import (QApplication, QWidget, QMessageBox, QFileDialog, QTableWidgetItem)
from PySide6.QtCore import QFile, QIODevice, QDate, QTime
from PySide6.QtUiTools import QUiLoader
from crudDB import CrudDB

UI_DIR = os.path.join(os.path.dirname(__file__), "")

def load_ui(filename):
    loader = QUiLoader()
    ui_file = QFile(filename)
    ui_file.open(QIODevice.ReadOnly)
    ui = loader.load(ui_file)
    ui_file.close()
    return ui

class App:
    def __init__(self):
        try:
            self.db = CrudDB()
        except Exception as e:
            QMessageBox.critical(None, "DB Error", f"Gagal koneksi ke database:\n{e}")
            sys.exit(1)

        self.login_win = load_ui(os.path.join(UI_DIR, "login.ui"))
        self.main_win = load_ui(os.path.join(UI_DIR, "main.ui"))
        self.user = None
        self.selected_kajian_id = None
        self.selected_user_id = None

        # wire login
        self.login_win.findChild(QWidget, "btn_login").clicked.connect(self.handle_login)
        self.login_win.findChild(QWidget, "btn_cancel").clicked.connect(self.exit_app)

        # wire kajian widgets/buttons
        self.main_win.findChild(QWidget, "btn_tambah_kajian").clicked.connect(self.tambah_kajian)
        self.main_win.findChild(QWidget, "btn_edit_kajian").clicked.connect(self.edit_kajian)
        self.main_win.findChild(QWidget, "btn_hapus_kajian").clicked.connect(self.hapus_kajian)
        self.main_win.findChild(QWidget, "btn_clear_kajian").clicked.connect(self.clear_kajian_form)
        self.main_win.findChild(QWidget, "btn_export_kajian").clicked.connect(self.export_kajian_csv)
        self.main_win.findChild(QWidget, "table_kajian").cellClicked.connect(self.on_kajian_row_clicked)
        self.main_win.findChild(QWidget, "edit_search_kajian").textChanged.connect(self.on_search_kajian_text)

        # wire user management widgets/buttons
        self.main_win.findChild(QWidget, "btn_tambah_user").clicked.connect(self.tambah_user)
        self.main_win.findChild(QWidget, "btn_edit_user").clicked.connect(self.edit_user)
        self.main_win.findChild(QWidget, "btn_hapus_user").clicked.connect(self.hapus_user)
        self.main_win.findChild(QWidget, "btn_clear_user").clicked.connect(self.clear_user_form)
        self.main_win.findChild(QWidget, "table_user").cellClicked.connect(self.on_user_row_clicked)

        # init defaults
        self.main_win.findChild(QWidget, "edit_tanggal").setDate(QDate.currentDate())
        self.main_win.findChild(QWidget, "edit_waktu").setTime(QTime.currentTime())

    def show_login(self):
        self.login_win.show()

    def exit_app(self):
        QApplication.quit()

    def handle_login(self):
        username = self.login_win.findChild(QWidget, "edit_username").text().strip()
        password = self.login_win.findChild(QWidget, "edit_password").text().strip()
        if not username or not password:
            QMessageBox.warning(self.login_win, "Login", "Masukkan username dan password.")
            return
        user = self.db.login(username, password)
        if not user:
            QMessageBox.warning(self.login_win, "Login", "Username atau password salah.")
            return
        self.user = user
        self.login_win.close()
        # configure UI based on role
        peran = self.user.get("peran", "petugas")
        if peran == "petugas":
            # hide user management tab
            tabw = self.main_win.findChild(QWidget, "tabWidget")
            # find index of tab_pengguna
            for i in range(tabw.count()):
                if tabw.widget(i).objectName() == "tab_pengguna":
                    tabw.removeTab(i)
                    break
        # load initial data
        self.load_kajian_table()
        self.load_user_table()
        self.main_win.show()

    # ---------------- kajian functions ----------------
    def read_kajian_form(self):
        tema = self.main_win.findChild(QWidget, "edit_tema").text().strip()
        ustadz = self.main_win.findChild(QWidget, "edit_ustadz").text().strip()
        tempat = self.main_win.findChild(QWidget, "edit_tempat").text().strip()
        tanggal = self.main_win.findChild(QWidget, "edit_tanggal").date().toString("yyyy-MM-dd")
        waktu = self.main_win.findChild(QWidget, "edit_waktu").time().toString("HH:mm:ss")
        return tema, ustadz, tempat, tanggal, waktu

    def validate_kajian_form(self):
        tema, ustadz, tempat, _, _ = self.read_kajian_form()
        if not tema or not ustadz or not tempat:
            QMessageBox.warning(self.main_win, "Validasi", "Tema, Ustadz, dan Tempat harus diisi.")
            return False
        return True

    def tambah_kajian(self):
        if not self.validate_kajian_form():
            return
        tema, ustadz, tempat, tanggal, waktu = self.read_kajian_form()
        try:
            self.db.tambah_kajian(tema, ustadz, tempat, tanggal, waktu)
            QMessageBox.information(self.main_win, "Sukses", "Kajian ditambahkan.")
            self.load_kajian_table()
            self.clear_kajian_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def load_kajian_table(self, rows=None):
        table = self.main_win.findChild(QWidget, "table_kajian")
        if rows is None:
            rows = self.db.ambil_semua_kajian()
        table.setRowCount(0)
        for r in rows:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(r["id_kajian"])))
            table.setItem(row, 1, QTableWidgetItem(r["tema"]))
            table.setItem(row, 2, QTableWidgetItem(r["ustadz"]))
            table.setItem(row, 3, QTableWidgetItem(r["tempat"]))
            table.setItem(row, 4, QTableWidgetItem(r["tanggal"].strftime("%Y-%m-%d")))
            table.setItem(row, 5, QTableWidgetItem(r["waktu"].strftime("%H:%M:%S") if r["waktu"] else ""))

    def on_kajian_row_clicked(self, row, col):
        try:
            table = self.main_win.findChild(QWidget, "table_kajian")
            id_item = table.item(row, 0)
            if id_item is None:
                return
            id_kajian = int(id_item.text())
            recs = self.db.ambil_semua_kajian()
            rec = None
            for r in recs:
                if r["id_kajian"] == id_kajian:
                    rec = r
                    break
            if rec:
                self.selected_kajian_id = rec["id_kajian"]
                self.main_win.findChild(QWidget, "edit_tema").setText(rec["tema"])
                self.main_win.findChild(QWidget, "edit_ustadz").setText(rec["ustadz"])
                self.main_win.findChild(QWidget, "edit_tempat").setText(rec["tempat"])
                dt = rec["tanggal"]
                self.main_win.findChild(QWidget, "edit_tanggal").setDate(QDate(dt.year, dt.month, dt.day))
                wt = rec["waktu"]
                self.main_win.findChild(QWidget, "edit_waktu").setTime(QTime(wt.hour, wt.minute, wt.second))
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def clear_kajian_form(self):
        self.selected_kajian_id = None
        self.main_win.findChild(QWidget, "edit_tema").clear()
        self.main_win.findChild(QWidget, "edit_ustadz").clear()
        self.main_win.findChild(QWidget, "edit_tempat").clear()
        self.main_win.findChild(QWidget, "edit_tanggal").setDate(QDate.currentDate())
        self.main_win.findChild(QWidget, "edit_waktu").setTime(QTime.currentTime())
        self.main_win.findChild(QWidget, "table_kajian").clearSelection()

    def edit_kajian(self):
        if not hasattr(self, "selected_kajian_id") or self.selected_kajian_id is None:
            QMessageBox.warning(self.main_win, "Pilih", "Pilih kajian yang akan diubah.")
            return
        if self.user.get("peran") == "petugas":
            QMessageBox.warning(self.main_win, "Izin", "Petugas tidak memiliki akses edit.")
            return
        if not self.validate_kajian_form():
            return
        tema, ustadz, tempat, tanggal, waktu = self.read_kajian_form()
        try:
            self.db.update_kajian(self.selected_kajian_id, tema, ustadz, tempat, tanggal, waktu)
            QMessageBox.information(self.main_win, "Sukses", "Kajian diupdate.")
            self.load_kajian_table()
            self.clear_kajian_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def hapus_kajian(self):
        if not hasattr(self, "selected_kajian_id") or self.selected_kajian_id is None:
            QMessageBox.warning(self.main_win, "Pilih", "Pilih kajian yang akan dihapus.")
            return
        if self.user.get("peran") == "petugas":
            QMessageBox.warning(self.main_win, "Izin", "Petugas tidak memiliki akses hapus.")
            return
        ok = QMessageBox.question(self.main_win, "Konfirmasi", "Yakin ingin menghapus?")
        if ok != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.hapus_kajian(self.selected_kajian_id)
            QMessageBox.information(self.main_win, "Sukses", "Kajian dihapus.")
            self.load_kajian_table()
            self.clear_kajian_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def on_search_kajian_text(self, text):
        if not text:
            self.load_kajian_table()
            return
        rows = self.db.cari_kajian(text)
        self.load_kajian_table(rows)

    def export_kajian_csv(self):
        fname, _ = QFileDialog.getSaveFileName(self.main_win, "Simpan CSV", "", "CSV Files (*.csv)")
        if not fname:
            return
        rows = self.db.ambil_semua_kajian()
        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id_kajian","tema","ustadz","tempat","tanggal","waktu"])
                for r in rows:
                    writer.writerow([r["id_kajian"], r["tema"], r["ustadz"], r["tempat"], r["tanggal"].strftime("%Y-%m-%d"), r["waktu"].strftime("%H:%M:%S") if r["waktu"] else ""])
            QMessageBox.information(self.main_win, "Export", f"Data tersimpan di: {fname}")
        except Exception as e:
            QMessageBox.critical(self.main_win, "Export Error", str(e))

    # ---------------- user management ----------------
    def read_user_form(self):
        nama = self.main_win.findChild(QWidget, "edit_nama_user").text().strip()
        username = self.main_win.findChild(QWidget, "edit_username_user").text().strip()
        password = self.main_win.findChild(QWidget, "edit_password_user").text()
        password_conf = self.main_win.findChild(QWidget, "edit_password_confirm").text()
        peran = self.main_win.findChild(QWidget, "combo_peran_user").currentText()
        return nama, username, password, password_conf, peran

    def validate_user_form(self, require_password=True):
        nama, username, password, password_conf, peran = self.read_user_form()
        if not nama or not username:
            QMessageBox.warning(self.main_win, "Validasi", "Nama dan Username harus diisi.")
            return False
        if require_password:
            if not password:
                QMessageBox.warning(self.main_win, "Validasi", "Password harus diisi.")
                return False
            if password != password_conf:
                QMessageBox.warning(self.main_win, "Validasi", "Password dan konfirmasi tidak cocok.")
                return False
        return True

    def tambah_user(self):
        if not self.validate_user_form(require_password=True):
            return
        nama, username, password, _, peran = self.read_user_form()
        try:
            self.db.tambah_pengguna(nama, username, password, peran)
            QMessageBox.information(self.main_win, "Sukses", "Pengguna ditambahkan.")
            self.load_user_table()
            self.clear_user_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def load_user_table(self):
        table = self.main_win.findChild(QWidget, "table_user")
        rows = self.db.ambil_semua_pengguna()
        table.setRowCount(0)
        for r in rows:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(r["id_pengguna"])))
            table.setItem(row, 1, QTableWidgetItem(r["nama"]))
            table.setItem(row, 2, QTableWidgetItem(r["username"]))
            table.setItem(row, 3, QTableWidgetItem(r["peran"]))

    def on_user_row_clicked(self, row, col):
        try:
            table = self.main_win.findChild(QWidget, "table_user")
            id_item = table.item(row, 0)
            if id_item is None:
                return
            id_user = int(id_item.text())
            rows = self.db.ambil_semua_pengguna()
            rec = None
            for r in rows:
                if r["id_pengguna"] == id_user:
                    rec = r
                    break
            if rec:
                self.selected_user_id = rec["id_pengguna"]
                self.main_win.findChild(QWidget, "edit_nama_user").setText(rec["nama"])
                self.main_win.findChild(QWidget, "edit_username_user").setText(rec["username"])
                # clear password fields for security
                self.main_win.findChild(QWidget, "edit_password_user").clear()
                self.main_win.findChild(QWidget, "edit_password_confirm").clear()
                # set role
                combo = self.main_win.findChild(QWidget, "combo_peran_user")
                idx = combo.findText(rec["peran"])
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def clear_user_form(self):
        self.selected_user_id = None
        self.main_win.findChild(QWidget, "edit_nama_user").clear()
        self.main_win.findChild(QWidget, "edit_username_user").clear()
        self.main_win.findChild(QWidget, "edit_password_user").clear()
        self.main_win.findChild(QWidget, "edit_password_confirm").clear()
        self.main_win.findChild(QWidget, "combo_peran_user").setCurrentIndex(1)  # default petugas
        self.main_win.findChild(QWidget, "table_user").clearSelection()

    def edit_user(self):
        if not hasattr(self, "selected_user_id") or self.selected_user_id is None:
            QMessageBox.warning(self.main_win, "Pilih", "Pilih pengguna yang akan diubah.")
            return
        # require password only if user entered one
        nama, username, password, password_conf, peran = self.read_user_form()
        require_pw = bool(password)
        if not self.validate_user_form(require_password=require_pw):
            return
        try:
            self.db.update_pengguna(self.selected_user_id, nama, username, password, peran)
            QMessageBox.information(self.main_win, "Sukses", "Pengguna diupdate.")
            self.load_user_table()
            self.clear_user_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

    def hapus_user(self):
        if not hasattr(self, "selected_user_id") or self.selected_user_id is None:
            QMessageBox.warning(self.main_win, "Pilih", "Pilih pengguna yang akan dihapus.")
            return
        # prevent deleting yourself
        if self.selected_user_id == self.user.get("id_pengguna"):
            QMessageBox.warning(self.main_win, "Aksi dilarang", "Tidak bisa menghapus user yang sedang login.")
            return
        ok = QMessageBox.question(self.main_win, "Konfirmasi", "Yakin ingin menghapus pengguna ini?")
        if ok != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.hapus_pengguna(self.selected_user_id)
            QMessageBox.information(self.main_win, "Sukses", "Pengguna dihapus.")
            self.load_user_table()
            self.clear_user_form()
        except Exception as e:
            QMessageBox.critical(self.main_win, "Error", str(e))

def main():
    app = QApplication(sys.argv)
    application = App()
    application.show_login()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
