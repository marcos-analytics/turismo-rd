"""data/raw/*.xlsx  ->  data/processed/*.csv

Correr después de src/download.py:
    python -m src.build

Los CSV que quedan en data/processed/ son el contrato con los notebooks:
si esta capa corre, el análisis corre.
"""
from __future__ import annotations

import pandas as pd

from .config import PROC, RAW
from .tidy import tidy_anio_mes, tidy_pais

SITUR = RAW / "situr"

RENOMBRES = {
    "flujo_migratorio": {
        "entradas_pasajeros_no_residentes_dominicano": "ent_nr_dom",
        "entradas_pasajeros_no_residentes_extranjero": "ent_nr_ext",
        "entradas_pasajeros_residentes_dominicano": "ent_res_dom",
        "entradas_pasajeros_residentes_extranjero": "ent_res_ext",
        "salidas_pasajeros_no_residentes_dominicano": "sal_nr_dom",
        "salidas_pasajeros_no_residentes_extranjero": "sal_nr_ext",
        "salidas_pasajeros_residentes_dominicano": "sal_res_dom",
        "salidas_pasajeros_residentes_extranjero": "sal_res_ext",
    },
}


def _strip_prefix(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    return df.rename(columns=lambda c: c[len(prefix):] if c.startswith(prefix) else c)


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)

    # 1. flujo migratorio nacional
    f = tidy_anio_mes(SITUR / "flujo_migratorio.xlsx", "Flujo migratorio")
    f = f.rename(columns=RENOMBRES["flujo_migratorio"])[list(RENOMBRES["flujo_migratorio"].values())]
    f.to_csv(PROC / "flujo_migratorio.csv")

    # 2. entradas de no residentes por aeropuerto y nacionalidad del pasajero
    a = tidy_anio_mes(SITUR / "flujo_migratorio.xlsx", "Entradas NR por aeropuerto")
    a = _strip_prefix(a, "entrada_de_pasajeros_no_residentes_")
    a = a.rename(columns=lambda c: c.replace("dominicano_", "dom_").replace("extranjero_", "ext_"))
    a.to_csv(PROC / "entradas_aeropuerto.csv")

    # 3. actividad hotelera nacional
    h = tidy_anio_mes(SITUR / "hotel_tradicional.xlsx", "Actividad hotelera")
    h = _strip_prefix(h, "actividad_hotelera_").rename(columns={
        "disponibilidad_ampliada": "disp_ampliada",
        "disponibilidad_de_hoteles": "disp_hoteles",
        "disponibilidad_efectiva": "disp_efectiva",
        "huespedes_extranjeros_del_total": "pct_huesp_ext",
        "huespedes_locales_del_total": "pct_huesp_local",
    })
    h.loc[:, [c for c in h.columns if c]].to_csv(PROC / "hotel_nacional.csv")

    # 4. ocupación hotelera por zona turística
    z = tidy_anio_mes(SITUR / "hotel_tradicional.xlsx", "Ocupación por zona")
    z = _strip_prefix(z, "ocupacion_abierta_")
    z.to_csv(PROC / "ocupacion_zona.csv")

    # 5. vuelos
    v = tidy_anio_mes(SITUR / "vuelos_llegadas.xlsx", "Entrada de vuelos")
    v = _strip_prefix(v, "llegada_de_vuelos_").rename(columns={"regulares_vuelos": "vuelos_regulares"})
    v.to_csv(PROC / "vuelos.csv")

    # 6. entradas por país de nacionalidad (formato largo -> ancho)
    n = tidy_pais(SITUR / "pais_nacionalidad.xlsx",
                  r"^entradas_pais_nacionalidad_20\d\d$",
                  r"^pais_de_nacionalidad$")
    n.to_csv(PROC / "nacionalidad_long.csv", index=False)
    (n.pivot_table(index="pais", columns="fecha", values="pasajeros")
      .to_csv(PROC / "nacionalidad_wide.csv"))

    print(f"Listo. {len(list(PROC.glob('*.csv')))} CSV en {PROC}")
    print(f"Periodo: {f.index.min():%Y-%m} a {f.index.max():%Y-%m}  ({len(f)} meses)")


if __name__ == "__main__":
    main()
