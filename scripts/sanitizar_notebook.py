#!/usr/bin/env python3
"""
Sanea las rutas absolutas en las salidas y celdas de zbe_bilbao.ipynb
para que sean relativas y reproducibles en cualquier entorno.
"""
from pathlib import Path
import nbformat

DIR_RAIZ = Path(__file__).resolve().parent.parent
RUTA_NB = DIR_RAIZ / "notebooks" / "zbe_bilbao.ipynb"

nb = nbformat.read(str(RUTA_NB), as_version=4)

# 1. Modificar celda de configuracion para mostrar ruta relativa
if len(nb.cells) > 3:
    c3 = nb.cells[3].source
    c3 = c3.replace('print(f"Ruta raíz del proyecto: {DIR_RAIZ}")', 'print("Ruta base del proyecto: .")')
    c3 = c3.replace('print(f"Ruta raz del proyecto: {DIR_RAIZ}")', 'print("Ruta base del proyecto: .")')
    nb.cells[3].source = c3

# 2. Limpiar salidas que tengan rutas de usuario de Windows
modificados = 0
for i, cell in enumerate(nb.cells):
    for out in cell.get("outputs", []):
        if "text" in out:
            t = out["text"]
            if "alfre" in t or "Desktop" in t:
                # Reemplazar rutas completas por relativas
                t_clean = t.replace("C:\\Users\\alfre\\Desktop\\haizelab\\", "")
                t_clean = t_clean.replace("C:\\\\Users\\\\alfre\\\\Desktop\\\\haizelab\\\\", "")
                t_clean = t_clean.replace("C:\\Users\\alfre\\Desktop\\haizelab", ".")
                out["text"] = t_clean
                modificados += 1

nbformat.write(nb, str(RUTA_NB))
print(f"[OK] Notebook saneado: {modificados} salidas limpiadas.")
