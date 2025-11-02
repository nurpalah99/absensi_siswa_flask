import importlib
import pkgutil
from ext import db  # ✅ gunakan db utama dari ext.py


# Import semua model agar terdaftar
from .siswa import Siswa
from .absensi import Absensi
from .pengaturan import Pengaturan


def load_models():
    """
    Mengimpor semua file model di folder models secara otomatis.
    Contoh: models/user.py, models/siswa.py, dll.
    Tujuannya agar SQLAlchemy mengenali semua model saat db.create_all() dipanggil.
    """
    package_name = 'models'
    package = importlib.import_module(package_name)

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")
