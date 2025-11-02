import pandas as pd
from io import BytesIO
from flask import send_file
from datetime import datetime

def generate_laporan_excel(
    data_absen, 
    nama_staf, 
    nip_staf, 
    judul_laporan="LAPORAN REKAPITULASI ABSENSI STAF",
    periode_mulai=None,
    periode_selesai=None
):
    df = pd.DataFrame(data_absen)
    output = BytesIO()
    tanggal_cetak = datetime.today().strftime("%d %B %Y")

    if periode_mulai and periode_selesai:
        periode_text = f"Periode: {periode_mulai.strftime('%d %B %Y')} s.d. {periode_selesai.strftime('%d %B %Y')}"
    else:
        periode_text = f"Periode: {tanggal_cetak}"

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, startrow=7, sheet_name='Laporan')
        workbook = writer.book
        worksheet = writer.sheets['Laporan']

        title_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 18, 'font_name': 'Times New Roman'})
        subtitle_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 14, 'font_name': 'Times New Roman'})
        center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_name': 'Times New Roman'})
        bold = workbook.add_format({'bold': True, 'font_name': 'Times New Roman'})
        normal = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 11})

        worksheet.merge_range('A1:F1', "PEMERINTAH PROVINSI BANTEN", title_format)
        worksheet.merge_range('A2:F2', "DINAS PENDIDIKAN DAN KEBUDAYAAN", title_format)
        worksheet.merge_range('A3:F3', "UNIT PELAKSANA TEKNIS", subtitle_format)
        worksheet.merge_range('A4:F4', "SMK NEGERI 14 KABUPATEN TANGERANG", title_format)
        worksheet.merge_range('A5:F5', "Kp. Mindi RT. 02 RW. 03 Desa Budi Mulya Kec. Cikupa Kab. Tangerang Banten 15710", center)
        worksheet.merge_range('A6:F6', "NPSN. 70046137 | https://smkn14kabtangerang.sch.id | smkn14kabupatentangerang@gmail.com", center)

        worksheet.set_row(6, 5, None, {'bottom': 2})
        worksheet.merge_range('A8:F8', judul_laporan.upper(), subtitle_format)
        worksheet.merge_range('A9:F9', periode_text, center)

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(10, col_num, value, bold)
        worksheet.set_column(0, len(df.columns), 20, normal)

        row_ttd = len(df) + 13
        worksheet.write(row_ttd, 4, f"Tangerang, {tanggal_cetak}", normal)
        worksheet.write(row_ttd + 1, 0, "Mengetahui,", normal)
        worksheet.write(row_ttd + 2, 0, "Kepala Sekolah", normal)
        worksheet.write(row_ttd + 2, 4, "Staf Administrasi", normal)
        worksheet.write(row_ttd + 6, 0, "Kumasrin, SP.", normal)
        worksheet.write(row_ttd + 7, 0, "NIP. 196806272007011010", normal)
        worksheet.write(row_ttd + 6, 4, nama_staf, normal)
        worksheet.write(row_ttd + 7, 4, f"NIP. {nip_staf}", normal)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"{judul_laporan.replace(' ', '_')}_{tanggal_cetak}.xlsx")
