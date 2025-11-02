import importlib
import pkgutil
from flask import Blueprint

def register_blueprints(app):
    """
    Registrasi otomatis semua blueprint di folder /blueprints.
    Menghindari duplikasi & mempermudah pengembangan multi-role.
    """

    package_name = 'blueprints'
    package = importlib.import_module(package_name)
    loaded = set()

    for _, name, _ in pkgutil.walk_packages(package.__path__, package_name + "."):
        if name.endswith(".__init__"):
            continue

        try:
            module = importlib.import_module(name)
        except Exception as e:
            print(f"[WARNING] Gagal import {name}: {e}")
            continue

        for obj in module.__dict__.values():
            if isinstance(obj, Blueprint):
                if obj.name in loaded:
                    print(f"[SKIP] Blueprint {obj.name} sudah terdaftar.")
                    continue

                app.register_blueprint(obj)
                loaded.add(obj.name)
                prefix = obj.url_prefix or "(none)"
                print(f"[OK] Blueprint aktif: {obj.name} → prefix {prefix}")

    print("\n=== Blueprint Aktif ===")
    for bp in app.blueprints.values():
        print(f" - {bp.name:20s} | {bp.url_prefix}")
    print("=======================\n")
