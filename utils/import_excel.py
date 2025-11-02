import pandas as pd
from models.siswa import Siswa
from app import db

def import_siswa_from_excel(filepath):
    df = pd.read_excel(filepath)
    for _, row in df.iterrows():
        siswa = Siswa(
            nis=str(row['NIS']),
            nama=row['Nama'],
            kelas=row['Kelas'],
            status=row.get('Status', 'Aktif'),
            foto=row.get('Foto', None)
        )
        db.session.add(siswa)
    db.session.commit()
    print("✅ Data siswa berhasil diimpor dari Excel!")
