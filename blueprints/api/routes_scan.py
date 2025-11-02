from ext import db
from models import Siswa, Absensi, Pengaturan
from flask import Blueprint, request, jsonify
from datetime import datetime
from colorama import Fore, Style, init
import os

init(autoreset=True)

api_scan = Blueprint("api_scan", __name__, url_prefix="/api")
print("[OK] routes_scan.py → Versi FIX untuk model jam_masuk / jam_pulang")


@api_scan.route("/absen_qr", methods=["POST"])
def absen_qr():
    try:
        data = request.get_json() or {}
        qr_value = data.get("qr")

        if not qr_value:
            return jsonify(success=False, message="QR tidak terbaca.")

        siswa = Siswa.query.filter_by(nis=qr_value, status="Aktif").first()
        if not siswa:
            print(Fore.RED + f"[NOT FOUND] NIS {qr_value} tidak ditemukan / nonaktif.")
            return jsonify(success=False, message="Data siswa tidak ditemukan atau tidak aktif.")

        now = datetime.now()
        today = now.date()
        jam = now.time()
        jam_str = now.strftime("%H:%M:%S")

        pengaturan = Pengaturan.query.first()
        jam_masuk = datetime.strptime(pengaturan.jam_masuk, "%H:%M").time() if pengaturan and pengaturan.jam_masuk else datetime.strptime("07:15", "%H:%M").time()
        jam_pulang = datetime.strptime(pengaturan.jam_pulang, "%H:%M").time() if pengaturan and pengaturan.jam_pulang else datetime.strptime("15:30", "%H:%M").time()

        # Cek apakah siswa sudah absen hari ini
        abs_hari_ini = Absensi.query.filter_by(nis=siswa.nis, tanggal=today).first()

        # ======================================================
        # 🟢 ABSEN MASUK
        # ======================================================
        if not abs_hari_ini:
            status = "Hadir" if jam <= jam_masuk else "Terlambat"

            absen_baru = Absensi(
                nis=siswa.nis,
                nama=siswa.nama,
                kelas=siswa.kelas,
                tanggal=today,
                jam_masuk=jam,
                status=status,
                keterangan="Scan QR oleh staf"
            )
            db.session.add(absen_baru)
            db.session.commit()

            _update_trigger()
            print(Fore.GREEN + f"[DB] {status.upper()} → {siswa.nama} ({siswa.kelas}) {jam_str}")

            return jsonify(
                success=True,
                message=f"{siswa.nama} {status.lower()} ({siswa.kelas})",
                nama=siswa.nama,
                kelas=siswa.kelas,
                waktu=jam_str,
                status=status
            )

        # ======================================================
        # 🔄 ABSEN PULANG
        # ======================================================
        else:
            if abs_hari_ini.jam_pulang:
                print(Fore.YELLOW + f"[SKIP] {siswa.nama} sudah absen pulang.")
                return jsonify(
                    success=True,
                    message=f"{siswa.nama} sudah absen pulang.",
                    nama=siswa.nama,
                    kelas=siswa.kelas,
                    waktu=abs_hari_ini.jam_pulang.strftime("%H:%M:%S"),
                    status="Pulang"
                )

            if jam >= jam_pulang:
                abs_hari_ini.jam_pulang = jam
                abs_hari_ini.status = "Pulang"
                abs_hari_ini.keterangan = "Scan pulang oleh staf"
                db.session.commit()

                _update_trigger()
                print(Fore.CYAN + f"[DB] PULANG → {siswa.nama} ({siswa.kelas}) {jam_str}")

                return jsonify(
                    success=True,
                    message=f"{siswa.nama} telah absen pulang.",
                    nama=siswa.nama,
                    kelas=siswa.kelas,
                    waktu=jam_str,
                    status="Pulang"
                )

            print(Fore.YELLOW + f"[INFO] {siswa.nama} sudah absen masuk, belum waktunya pulang.")
            return jsonify(
                success=True,
                message=f"{siswa.nama} sudah absen masuk ({siswa.kelas}), belum waktunya pulang.",
                nama=siswa.nama,
                kelas=siswa.kelas,
                waktu=abs_hari_ini.jam_masuk.strftime("%H:%M:%S"),
                status=abs_hari_ini.status
            )

    except Exception as e:
        db.session.rollback()
        print(Fore.RED + f"[ERROR absensi_qr] {type(e).__name__}: {e}" + Style.RESET_ALL)
        return jsonify(success=False, message="Terjadi kesalahan server."), 500


# ==========================================================
# 🔔 TRIGGER DASHBOARD STAF
# ==========================================================
def _update_trigger():
    try:
        os.makedirs("static", exist_ok=True)
        trigger_path = os.path.join("static", "trigger_absen.txt")
        with open(trigger_path, "w") as f:
            f.write(datetime.now().isoformat())
        print(Fore.MAGENTA + "[Trigger] Dashboard staf diperbarui." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[Trigger ERROR] {e}" + Style.RESET_ALL)
