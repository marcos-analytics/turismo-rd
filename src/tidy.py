"""Parsers para los Excel de SITUR/MITUR.

Estos archivos NO son tablas limpias: traen logo, títulos, encabezados en dos
niveles con celdas combinadas, el año escrito una sola vez por bloque de 12
meses, meses en español, y notas al pie. Todo eso se resuelve acá para que el
análisis reciba dataframes indexados por fecha.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from .config import MESES


def slug(s) -> str:
    """'Ocupación abierta' -> 'ocupacion_abierta'."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()
    return re.sub(r"^_|_$", "", re.sub(r"[^a-z0-9]+", "_", s))


def _raw_grid(path, sheet) -> list[list]:
    df = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)
    return df.where(pd.notna(df), None).values.tolist()


def _ffill_row(row: list) -> list:
    """Rellena a la derecha los huecos que dejan las celdas combinadas."""
    out, last = [], None
    for c in row:
        if c is not None and str(c).strip() != "":
            last = str(c).strip()
        out.append(last)
    return out


def tidy_anio_mes(path, sheet) -> pd.DataFrame:
    """Hojas con forma 'Año | Mes | ...columnas'.

    Localiza la fila de encabezado buscando literalmente Año/Mes, reconstruye
    los nombres de columna combinando hasta dos niveles superiores, arrastra el
    año hacia abajo y descarta las filas de notas al pie.
    """
    grid = _raw_grid(path, sheet)

    hr = next(
        (i for i, r in enumerate(grid)
         if len(r) > 1
         and slug(r[0]) == "ano"
         and slug(r[1]) == "mes"),
        None,
    )
    if hr is None:
        raise ValueError(f"No encontré la fila 'Año | Mes' en {sheet!r} de {path.name}")

    # niveles superiores (hasta 2), con forward-fill por celdas combinadas
    levels = []
    for k in (1, 2):
        if hr - k < 0:
            break
        row = grid[hr - k]
        if row and slug(row[0]) == "ano":
            break
        levels.insert(0, _ffill_row(row))

    base = grid[hr]
    cols = []
    for j, c in enumerate(base):
        if j < 2:
            cols.append(slug(c))
            continue
        parts = [lv[j] for lv in levels if j < len(lv) and lv[j]]
        parts.append(c)
        cols.append(slug(" ".join(str(p) for p in parts if p)))

    records, year = [], None
    for row in grid[hr + 1:]:
        a = row[0] if row else None
        if a is not None and str(a).strip().replace(".0", "").isdigit() and int(float(a)) > 1900:
            year = int(float(a))
        month = MESES.get(slug(row[1] if len(row) > 1 else None).replace("_", ""))
        if not month or year is None:
            continue
        rec = {"fecha": pd.Timestamp(year, month, 1)}
        for j in range(2, min(len(cols), len(row))):
            if cols[j]:
                rec[cols[j]] = pd.to_numeric(row[j], errors="coerce")
        if any(pd.notna(v) for k, v in rec.items() if k != "fecha"):
            records.append(rec)

    out = pd.DataFrame(records).set_index("fecha").sort_index()
    return out.dropna(axis=1, how="all")


def tidy_pais(path, sheet_pattern: str, label_pattern: str) -> pd.DataFrame:
    """Hojas 'un año por pestaña, países en filas, meses en columnas' -> formato largo.

    Devuelve columnas: fecha, pais, pasajeros.
    """
    xl = pd.ExcelFile(path)
    sheet_re, label_re = re.compile(sheet_pattern), re.compile(label_pattern)
    rows = []

    for sn in xl.sheet_names:
        if not sheet_re.match(slug(sn)):
            continue
        m = re.search(r"(20\d\d)", sn)
        if not m:
            continue
        year = int(m.group(1))
        grid = _raw_grid(path, sn)

        hr = next((i for i, r in enumerate(grid) if r and label_re.match(slug(r[0]))), None)
        if hr is None:
            continue

        months = [MESES.get(slug(c).replace("_", "")) for c in grid[hr]]
        for row in grid[hr + 1:]:
            pais = str(row[0]).strip() if row and row[0] is not None else ""
            if not pais or re.match(r"(?i)^(fuente|nota|total)", pais):
                continue
            for j, mo in enumerate(months):
                if j == 0 or not mo or j >= len(row):
                    continue
                v = pd.to_numeric(row[j], errors="coerce")
                if pd.notna(v):
                    rows.append((pd.Timestamp(year, mo, 1), pais, float(v)))

    return (pd.DataFrame(rows, columns=["fecha", "pais", "pasajeros"])
            .sort_values(["pais", "fecha"])
            .reset_index(drop=True))
