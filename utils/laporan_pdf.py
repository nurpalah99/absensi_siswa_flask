from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from io import BytesIO
from flask import send_file
from datetime import datetime

def generate_laporan_pdf(
    data_absen, 
    nama_staf, 
    nip_staf, 
    judul_laporan="LAPORAN REKAPITULASI ABSENSI STAF",
    periode_mulai=None,
    periode_selesai=None
):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    logo_kiri = "static/img/logo_banten.png"
    logo_kanan = "static/img/logo_smkn14.png"

    try:
        p.drawImage(ImageReader(logo_kiri), 50, height - 110, width=70, height=70, mask='auto')
        p.drawImage(ImageReader(logo_kanan), width - 120, height - 110, width=70, height=70, mask='auto')
    except:
        pass

    # === KOP SURAT ===
    p.setFont("Times-Bold", 18)
    p.drawCentredString(width / 2, height - 40, "PEMERINTAH PROVINSI BANTEN")
    p.drawCentredString(width / 2, height - 60, "DINAS PENDIDIKAN DAN KEBUDAYAAN")

    p.setFont("Times-Bold", 14)
    p.drawCentredString(width / 2, height - 80, "UNIT PELAKSANA TEKNIS")

    p.setFont("Times-Bold", 18)
    p.drawCentredString(width / 2, height - 100, "SMK NEGERI 14 KABUPATEN TANGERANG")

    p.setFont("Times-Roman", 10)
    p.drawCentredString(width / 2, height - 115,
        "Kp. Mindi RT. 02 RW. 03 Desa Budi Mulya Kec. Cikupa Kab. Tangerang Banten 15710")
    p.drawCentredString(width / 2, height - 127,
        "NPSN. 70046137 | https://smkn14kabtangerang.sch.id | smkn14kabupatentangerang@gmail.com")

    p.setStrokeColor(colors.black)
    p.setLineWidth(1.5)
    p.line(50, height - 132, width - 50, height - 132)
    p.setLineWidth(0.5)
    p.line(50, height - 135, width - 50, height - 135)

    # === JUDUL & PERIODE ===
    p.setFont("Times-Bold", 14)
    p.drawCentredString(width / 2, height - 160, judul_laporan.upper())

    tanggal_cetak = datetime.today().strftime("%d %B %Y")

    if periode_mulai and periode_selesai:
        periode_text = f"Periode: {periode_mulai.strftime('%d %B %Y')} s.d. {periode_selesai.strftime('%d %B %Y')}"
    else:
        periode_text = f"Periode: {tanggal_cetak}"

    p.setFont("Times-Roman", 12)
    p.drawCentredString(width / 2, height - 180, periode_text)

    # === ISI LAPORAN ===
    y = height - 210
    for i, row in enumerate(data_absen, start=1):
        p.drawString(50, y, f"{i}. {row['nama']} - Masuk: {row['jam_masuk']} - Pulang: {row['jam_pulang']} - Status: {row['status']}")
        y -= 20
        if y < 100:
            p.showPage()
            y = height - 100

    # === TANDA TANGAN ===
    base_y = 150
    p.setFont("Times-Roman", 12)
    p.drawRightString(width - 50, base_y + 110, f"Tangerang, {tanggal_cetak}")
    p.drawString(50, base_y + 110, "Mengetahui,")
    p.drawString(50, base_y + 90, "Kepala Sekolah")
    p.drawRightString(width - 50, base_y + 90, "Staf Administrasi")

    p.drawString(50, base_y + 20, "Kumasrin, SP.")
    p.drawString(50, base_y + 5, "NIP. 196806272007011010")
    p.drawRightString(width - 50, base_y + 20, f"{nama_staf}")
    p.drawRightString(width - 50, base_y + 5, f"NIP. {nip_staf}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{judul_laporan.replace(' ', '_')}_{tanggal_cetak}.pdf")
