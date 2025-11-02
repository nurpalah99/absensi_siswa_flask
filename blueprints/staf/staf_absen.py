from utils.role_utils import require_role, require_login
from flask import Blueprint, request, render_template, jsonify, session, redirect, url_for, flash
from datetime import datetime, date, time
from ext import db
from models.siswa import Siswa
from models.absensi import Absensi
from .staf_utils import require_staf, catat_aktivitas, log_absensi_aksi
from sqlalchemy import func

staf_absen = Blueprint("staf_absen", __name__, url_prefix="/staf/absen")


# -----------------------
# Route: Data absen siswa
# -----------------------
@staf_absen.route("/data_absen_siswa")
@require_staf
def data_absen_siswa():
    tanggal = request.args.get("tanggal")
    kelas = request.args.get("kelas", "").strip()

    if not tanggal:
        return jsonify({"status": "error", "message": "Tanggal tidak diberikan"}), 400

    try:
        tanggal_obj = datetime.strptime(tanggal, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"status": "error", "message": "Format tanggal salah"}), 400

    q = Siswa.query.filter(Siswa.status == "Aktif")
    if kelas:
        q = q.filter(Siswa.kelas == kelas)
    siswa_list = q.order_by(Siswa.nama.asc()).all()
    db.session.expire_all()

    out = []
    for s in siswa_list:
        abs_hari_ini = (
            db.session.query(Absensi)
            .filter(Absensi.nis == s.nis, func.date(Absensi.tanggal) == tanggal)
            .order_by(Absensi.id.desc())
            .first()
        )

        def fmt_time(val):
            if isinstance(val, datetime):
                return val.strftime("%H:%M")
            elif isinstance(val, time):
                return val.strftime("%H:%M")
            elif isinstance(val, str):
                return val[:5]
            return "-"

        if abs_hari_ini:
            out.append({
                "id": abs_hari_ini.id,
                "tanggal": tanggal,
                "nis": s.nis,
                "nama": s.nama,
                "kelas": s.kelas,
                "jam_masuk": fmt_time(getattr(abs_hari_ini, "jam_masuk", None)),
                "jam_pulang": fmt_time(getattr(abs_hari_ini, "jam_pulang", None)),
                "status": abs_hari_ini.status or "-",
                "keterangan": abs_hari_ini.keterangan or ""
            })
        else:
            out.append({
                "id": None,
                "tanggal": tanggal,
                "nis": s.nis,
                "nama": s.nama,
                "kelas": s.kelas,
                "jam_masuk": "-",
                "jam_pulang": "-",
                "status": "Belum Absen",
                "keterangan": ""
            })

    return render_template("staf/_tabel_absen.html", data=out)


# -----------------------
# Route: Pulang Massal
# -----------------------
@staf_absen.route("/pulang_massal", methods=["POST"])
@require_login
@require_role(["admin", "staf"])
def pulang_massal():
    tanggal = request.form.get("tanggal") or datetime.now().strftime("%Y-%m-%d")
    jam_pulang_input = request.form.get("jam_pulang") or "12:00"
    kelas = request.form.get("kelas", "").strip()
    alasan = request.form.get("alasan", "").strip()

    try:
        jam_pulang_massal = datetime.strptime(jam_pulang_input, "%H:%M").time()
    except ValueError:
        jam_pulang_massal = time(12, 0)

    siswa_q = Siswa.query.filter(Siswa.status == "Aktif")
    if kelas:
        siswa_q = siswa_q.filter(Siswa.kelas == kelas)
    siswa_list = siswa_q.all()

    def to_time(val):
        if isinstance(val, time):
            return val
        if isinstance(val, datetime):
            return val.time()
        if isinstance(val, str) and len(val) >= 5:
            try:
                return datetime.strptime(val[:5], "%H:%M").time()
            except:
                pass
        return None

    total_update = 0
    total_skip = 0

    for s in siswa_list:
        absen = (
            Absensi.query
            .filter(
                Absensi.nis == s.nis,
                func.date(Absensi.tanggal) == tanggal
            )
            .first()
        )

        if not absen:
            continue

        jm = to_time(absen.jam_masuk)
        jp = to_time(absen.jam_pulang)
        if not jm:
            continue

        # Validasi jam pulang
        if jam_pulang_massal < jm:
            total_skip += 1
            continue

        # Update semua yang hadir pagi (fleksibel)
        if (not jp) or (jp != jam_pulang_massal) or ("Pulang massal otomatis" in (absen.keterangan or "")):
            absen.jam_pulang = jam_pulang_massal
            absen.status = absen.status or "Hadir"
            absen.keterangan = f"Pulang massal otomatis{' — ' + alasan if alasan else ''}"
            total_update += 1

    db.session.commit()

    catat_aktivitas(session.get("nama"),
        f"Pulang massal otomatis {tanggal} ({kelas or 'Semua kelas'}) "
        f"- {total_update} diperbarui, {total_skip} dilewati (jam < masuk)")
    log_absensi_aksi(session.get("nama"),
        f"Pulang massal otomatis {tanggal} ({kelas or 'Semua kelas'}) "
        f"- {total_update} diperbarui, {total_skip} dilewati (jam < masuk)")

    flash(f"✅ Pulang massal {tanggal} selesai — {total_update} siswa diperbarui, "
          f"{total_skip} dilewati karena jam masuk lebih tinggi.", "success")

    return redirect(url_for("staf_absen.kelola_absen", tanggal=tanggal, kelas=kelas))




# -----------------------
# Route: Koreksi Massal Alpa → Hadir (Simulasi Ujian)
# -----------------------
@staf_absen.route("/koreksi_massal_alpa", methods=["POST"])
@require_login
@require_role(["admin", "staf"])
def koreksi_massal_alpa():
    try:
        tanggal_str = request.form.get("tanggal")
        kelas = request.form.get("kelas", "").strip()
        jam_masuk_input = request.form.get("jam_masuk")
        jam_pulang_input = request.form.get("jam_pulang")
        alasan = request.form.get("alasan", "Kegiatan simulasi ujian nasional")

        if not tanggal_str or not kelas:
            return jsonify(success=False, message="Tanggal dan kelas wajib diisi."), 400

        try:
            tanggal = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify(success=False, message="Format tanggal salah."), 400

        jm = datetime.strptime(jam_masuk_input, "%H:%M").time() if jam_masuk_input else time(7, 00)
        jp = datetime.strptime(jam_pulang_input, "%H:%M").time() if jam_pulang_input else time(12, 00)

        # Ambil semua siswa ALPA di kelas dan tanggal itu
        absensi_list = (
            Absensi.query
            .filter(
                Absensi.kelas == kelas,
                func.date(Absensi.tanggal) == tanggal,
                Absensi.status == "Alpa"
            )
            .all()
        )

        if not absensi_list:
            return jsonify(success=False, message="Tidak ada siswa Alpa di kelas tersebut pada tanggal itu."), 404

        total_update = 0
        for a in absensi_list:
            a.status = "Hadir"
            a.jam_masuk = jm
            a.jam_pulang = jp
            a.keterangan = alasan
            a.is_locked = 0
            total_update += 1

        db.session.commit()

        catat_aktivitas(
            session.get("nama"),
            f"Koreksi massal Alpa→Hadir ({kelas}) tanggal {tanggal} - {total_update} siswa diperbarui."
        )
        log_absensi_aksi(
            session.get("nama"),
            f"Koreksi massal Alpa→Hadir ({kelas}) tanggal {tanggal} - {total_update} siswa diperbarui."
        )

        return jsonify(success=True, message=f"{total_update} siswa kelas {kelas} berhasil dikoreksi menjadi Hadir."), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR koreksi_massal_alpa] {type(e).__name__}: {e}")
        return jsonify(success=False, message="Terjadi kesalahan saat koreksi massal."), 500




# -----------------------
# Route: Koreksi otomatis Hadir -> Terlambat
# -----------------------
@staf_absen.route("/koreksi_terlambat", methods=["POST"])
@require_login
@require_role(["admin", "staf"])
def koreksi_terlambat():
    try:
        tanggal_str = request.form.get("tanggal")
        if not tanggal_str:
            return jsonify(success=False, message="Tanggal wajib diisi."), 400

        # Konversi string ke objek tanggal
        tanggal = datetime.strptime(tanggal_str, "%Y-%m-%d").date()

        batas_waktu = datetime.strptime("07:00", "%H:%M").time()

        # Ambil semua data absensi dengan status Hadir tapi jam_masuk > 07:00
        absensi_terlambat = (
            Absensi.query
            .filter(
                func.date(Absensi.tanggal) == tanggal,
                Absensi.status == "Hadir",
                Absensi.jam_masuk > batas_waktu
            )
            .all()
        )

        if not absensi_terlambat:
            return jsonify(success=False, message="Tidak ada data siswa terlambat pada tanggal ini."), 404

        total_update = 0
        for a in absensi_terlambat:
            a.status = "Terlambat"
            a.keterangan = (a.keterangan or "") + " (terlambat masuk)"
            total_update += 1

        db.session.commit()

        catat_aktivitas(
            session.get("nama"),
            f"Koreksi otomatis Hadir→Terlambat ({tanggal}) - {total_update} data diperbarui."
        )
        log_absensi_aksi(
            session.get("nama"),
            f"Koreksi otomatis Hadir→Terlambat ({tanggal}) - {total_update} data diperbarui."
        )

        return jsonify(success=True, message=f"{total_update} siswa dikoreksi menjadi Terlambat."), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR koreksi_terlambat] {type(e).__name__}: {e}")
        return jsonify(success=False, message="Terjadi kesalahan saat koreksi otomatis."), 500




# -----------------------
# Route: Tutup Absen
# -----------------------
@staf_absen.route("/tutup_absen", methods=["POST"])
@require_login
@require_role(["admin", "staf"])
def tutup_absen():
    """Menutup absensi harian: mengisi otomatis status siswa yang belum absen"""
    tanggal = request.form.get("tanggal")
    kelas = request.form.get("kelas")

    if not tanggal:
        return jsonify({"message": "Tanggal tidak diberikan."}), 400

    try:
        tanggal_obj = datetime.strptime(tanggal, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Format tanggal salah."}), 400

    siswa_q = Siswa.query.filter(Siswa.status == "Aktif")
    if kelas:
        siswa_q = siswa_q.filter(Siswa.kelas == kelas)
    siswa_list = siswa_q.all()

    total_alpa, total_bolos = 0, 0

    for s in siswa_list:
        absen = Absensi.query.filter(
            Absensi.nis == s.nis,
            func.date(Absensi.tanggal) == tanggal_obj
        ).first()

        if not absen:
            baru = Absensi(
                nis=s.nis,
                nama=s.nama,
                kelas=s.kelas,
                tanggal=tanggal_obj,
                status="Alpa",
                keterangan="Tidak hadir saat absen ditutup"
            )
            db.session.add(baru)
            total_alpa += 1
            continue

        if absen.jam_masuk and not absen.jam_pulang and absen.status not in ["Izin", "Sakit", "Dispensasi"]:
            absen.status = "Bolos"
            absen.keterangan = "Tidak absen pulang saat absen ditutup"
            total_bolos += 1

        setattr(absen, "is_locked", 1)

    db.session.commit()

    catat_aktivitas(session.get("nama"),
        f"Tutup absen {tanggal} ({kelas or 'Semua kelas'}) — {total_alpa} Alpa, {total_bolos} Bolos.")
    log_absensi_aksi(session.get("nama"),
        f"Tutup absen {tanggal} ({kelas or 'Semua kelas'}) — {total_alpa} Alpa, {total_bolos} Bolos.")

    return jsonify({
        "message": f"Tutup absen berhasil — {total_alpa} siswa Alpa, {total_bolos} siswa Bolos."
    }), 200


# -----------------------
# Route: Update Absen
# -----------------------
@staf_absen.route("/update_absen", methods=["POST"])
@require_login
@require_role(["admin", "staf", "walikelas"])
def update_absen():
    try:
        absen_id = request.form.get("id")
        nis = request.form.get("nis")
        nama = request.form.get("nama")
        kelas = request.form.get("kelas")
        status_baru = request.form.get("status")
        jam_masuk = request.form.get("jam_masuk")
        jam_pulang = request.form.get("jam_pulang")
        keterangan = request.form.get("keterangan", "").strip()

        # === CASE 1: Buat data baru ===
        if not absen_id or absen_id in ["0", "None", None]:
            if not (nis and nama and kelas):
                return jsonify(success=False, message="Data siswa tidak lengkap untuk membuat absensi baru."), 400

            tanggal = datetime.now().date()
            jm = datetime.strptime(jam_masuk, "%H:%M").time() if jam_masuk else None
            jp = datetime.strptime(jam_pulang, "%H:%M").time() if jam_pulang else None

            absen_baru = Absensi(
                nis=nis,
                nama=nama,
                kelas=kelas,
                tanggal=tanggal,
                jam_masuk=jm,
                jam_pulang=jp,
                status=status_baru or "Hadir",
                keterangan=keterangan or ""
            )

            db.session.add(absen_baru)
            db.session.commit()

            catat_aktivitas(session.get("nama"),
                f"Buat absensi baru untuk {nama} ({kelas}) tanggal {tanggal}.")
            log_absensi_aksi(session.get("nama"),
                f"Buat absensi baru untuk {nama} ({kelas}) tanggal {tanggal}.")
            return jsonify(success=True, message="Data absensi baru berhasil dibuat."), 200

        # === CASE 2: Update data yang sudah ada ===
        absen = Absensi.query.get(absen_id)
        if not absen:
            return jsonify(success=False, message="Data absensi tidak ditemukan."), 404

        status_lama = absen.status or "-"
        alasan_sah = (status_baru or "").lower() in ["izin", "sakit", "dispensasi"]

        # 🔹 IZINKAN PERUBAHAN STATUS ALPA KE APA PUN
        if status_lama.lower() == "alpa":
            absen.is_locked = 0
        elif getattr(absen, "is_locked", 0):
            if not alasan_sah:
                return jsonify(success=False,
                    message="Data absensi sudah dikunci dan tidak dapat diubah selain ke izin/sakit/dispensasi."
                ), 403
            else:
                absen.is_locked = 0

        # Update data
        absen.status = status_baru
        absen.keterangan = keterangan or absen.keterangan

        if jam_masuk:
            try:
                absen.jam_masuk = datetime.strptime(jam_masuk, "%H:%M").time()
            except ValueError:
                return jsonify(success=False, message="Format jam masuk tidak valid."), 400

        if jam_pulang:
            try:
                jp = datetime.strptime(jam_pulang, "%H:%M").time()
                if absen.jam_masuk and jp < absen.jam_masuk:
                    return jsonify(success=False, message="Jam pulang tidak boleh lebih awal dari jam masuk."), 400
                absen.jam_pulang = jp
            except ValueError:
                return jsonify(success=False, message="Format jam pulang tidak valid."), 400

        db.session.commit()

        # 🔹 Log aktivitas staf
        if status_lama.lower() == "alpa":
            catat_aktivitas(session.get("nama"),
                            f"Koreksi absensi Alpa → {status_baru} untuk {absen.nama} ({absen.kelas})")
            log_absensi_aksi(session.get("nama"),
                            f"Koreksi absensi Alpa → {status_baru} untuk {absen.nama} ({absen.kelas})")
        else:
            catat_aktivitas(session.get("nama"),
                            f"Edit absensi ID {absen_id}: {status_lama} → {status_baru} | Ket: {absen.keterangan}")
            log_absensi_aksi(session.get("nama"),
                            f"Edit absensi ID {absen_id}: {status_lama} → {status_baru} | Ket: {absen.keterangan}")

        return jsonify(success=True, message="Perubahan absensi berhasil disimpan."), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR update_absen] {type(e).__name__}: {e}")
        return jsonify(success=False, message="Gagal menyimpan perubahan."), 500


# -----------------------
# Route: Hapus / Reset Absen
# -----------------------
@staf_absen.route("/hapus_absen", methods=["POST"])
@require_login
@require_role(["admin", "staf"])
def hapus_absen():
    try:
        absen_id = request.form.get("id")
        if not absen_id:
            return jsonify(success=False, message="ID absensi tidak diberikan."), 400

        absen = Absensi.query.get(absen_id)
        if not absen:
            return jsonify(success=False, message="Data absensi tidak ditemukan."), 404

        nama = absen.nama
        kelas = absen.kelas
        tanggal = absen.tanggal

        # Hapus data absensi
        db.session.delete(absen)
        db.session.commit()

        catat_aktivitas(session.get("nama"),
                        f"Hapus data absensi {nama} ({kelas}) tanggal {tanggal}")
        log_absensi_aksi(session.get("nama"),
                        f"Hapus data absensi {nama} ({kelas}) tanggal {tanggal}")

        return jsonify(success=True, message=f"Data absensi {nama} ({kelas}) tanggal {tanggal} berhasil dihapus."), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR hapus_absen] {type(e).__name__}: {e}")
        return jsonify(success=False, message="Gagal menghapus data absensi."), 500



# -----------------------
# Route: Kelola Absen
# -----------------------
@staf_absen.route("/kelola_absen")
@require_staf
def kelola_absen():
    semua_kelas = [k[0] for k in db.session.query(Siswa.kelas).distinct().order_by(Siswa.kelas.asc())]
    tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
    return render_template("staf/kelola_absen.html", semua_kelas=semua_kelas, tanggal_hari_ini=tanggal_hari_ini)
