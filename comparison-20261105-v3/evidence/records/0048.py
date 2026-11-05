from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
src=(root/'pyqcu_repeated.py').read_text();assert 'else 4' in src
target=root/'pyqcu_repeated_full.py';assert not target.exists();target.write_text(src.replace('else 4','else 2'))
entry=(root/'pyqcu_entry.py').read_text().replace('pyqcu_repeated.py','pyqcu_repeated_full.py')
(root/'pyqcu_entry_full.py').write_text(entry)
