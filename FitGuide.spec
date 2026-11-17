from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata
streamlit_data, streamlit_bins, streamlit_hidden = collect_all('streamlit')
a = Analysis(['desktop.py'], pathex=[],
    binaries=streamlit_bins,
    datas=streamlit_data + copy_metadata('streamlit') + [('app.py','.'), ('fitguide','fitguide')],
    hiddenimports=streamlit_hidden + collect_submodules('fitguide') + ['server.gateway','webview.platforms.edgechromium','webview.platforms.winforms'],
    excludes=['pytest','tkinter'], noarchive=False)
pyz = PYZ(a.pure)
# Extract bundled DLLs at runtime so Explorer's ZIP extraction does not attach
# the downloaded archive's Internet zone to Python.Runtime.dll.
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name='FitGuide', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False)
