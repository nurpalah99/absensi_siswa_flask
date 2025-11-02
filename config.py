import os

# Tentukan direktori utama project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")

# Buat folder "database" kalau belum ada
os.makedirs(DB_DIR, exist_ok=True)

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = "filesystem"
    JSON_AS_ASCII = False  # biar huruf Indonesia tidak error

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_PATH = os.path.join(DB_DIR, "merged_absensi_fixed_final.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

class ProductionConfig(BaseConfig):
    DEBUG = False
    DATABASE_PATH = os.path.join(DB_DIR, "merged_absensi_fixed_final.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    DATABASE_PATH = os.path.join(DB_DIR, "merged_absensi_fixed_final.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

config_map = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
    "test": TestingConfig
}
