"""Descarga los Excel crudos a data/raw/.

Correr desde la raíz del proyecto:
    python -m src.download

Nota: los servidores de MITUR y del Banco Central a veces tardan o rechazan
peticiones sin User-Agent, así que se manda uno y se reintenta.
"""
from __future__ import annotations

import sys
import time
import urllib.parse
import urllib.request

from .config import BCRD, BCRD_FILES, RAW, SITUR, SITUR_FILES

UA = {"User-Agent": "Mozilla/5.0 (proyecto academico de analisis de datos)"}


def fetch(url: str, dest, intentos: int = 3) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    for i in range(intentos):
        try:
            req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&=%"), headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) < 5_000:
                raise ValueError(f"respuesta sospechosamente corta ({len(data)} bytes)")
            dest.write_bytes(data)
            print(f"  ok  {dest.name}  ({len(data)/1024:.0f} KB)")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"  ... intento {i+1}/{intentos} falló: {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))
    print(f"  FALLO {dest.name}", file=sys.stderr)
    return False


def main() -> None:
    print("SITUR / MITUR (mensual 2022-presente)")
    for key, fname in SITUR_FILES.items():
        fetch(SITUR + fname, RAW / "situr" / f"{key}.xlsx")

    print("\nBanco Central (series largas)")
    for key, fname in BCRD_FILES.items():
        fetch(BCRD + fname, RAW / "bcrd" / f"{key}{fname[fname.rfind('.'):]}")

    print(f"\nListo. Archivos en {RAW}")


if __name__ == "__main__":
    main()
