# build_app.spec
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

# safe project root resolution (works when __file__ may be undefined)
project_root = os.path.abspath(os.getcwd())
src_dir = os.path.join(project_root, 'src')

# hidden imports
hidden_imports = []
try:
    hidden_imports += collect_submodules('tkinterdnd2')
except Exception:
    pass

# datas / binaries
datas = []
binaries = []

a = Analysis(
    [os.path.join(src_dir, 'tk_app.py')],
    pathex=[src_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ImgResizer',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(project_root, 'assets', 'icon.ico') if os.path.exists(os.path.join(project_root,'assets','icon.ico')) else None,
)
