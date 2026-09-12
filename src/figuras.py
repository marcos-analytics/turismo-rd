"""Genera todas las figuras de reports/figures/.

    python -m src.figuras
"""
from __future__ import annotations

import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import analisis as A
from . import viz
from .config import FIGS

warnings.filterwarnings("ignore")

MES_ABR = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
ZONA_NOMBRE = {
    "bavaro_punta_cana": "Bávaro – Punta Cana",
    "romana_bayahibe": "Romana – Bayahíbe",
    "puerto_plata": "Puerto Plata",
    "gran_santo_domingo": "Gran Santo Domingo",
    "samana": "Samaná",
    "santiago": "Santiago",
    "sosua_cabarete": "Sosúa – Cabarete",
    "boca_chica_juan_dolio": "Boca Chica – Juan Dolio",
}
FUENTE = "Fuente: SITUR / Ministerio de Turismo de la República Dominicana."


def fig1_tendencia(y: pd.Series) -> None:
    res = A.stl(y)
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.plot(y.index, y.values, color=viz.SERIES[0], lw=1.6, label="Serie observada")
    ax.plot(res.trend.index, res.trend.values, color=viz.SERIES[1], lw=2.6,
            label="Tendencia (STL)")
    viz.miles(ax)
    viz.titulo(ax, "El crecimiento del turismo extranjero es de tendencia, no de rebote",
               "Entradas mensuales de pasajeros no residentes extranjeros, 2022–2026")
    ax.set_ylabel("Pasajeros por mes")
    ax.legend(loc="lower right", ncol=2)
    ax.annotate(FUENTE, xy=(0, -0.16), xycoords="axes fraction",
                fontsize=8, color=viz.MUTED)
    viz.guardar(fig, FIGS / "01_llegadas_tendencia.png")


def fig2_estacionalidad(y: pd.Series) -> None:
    fac = A.indice_estacional(y)
    anios = sorted(fac["anio"].unique())
    ramp = viz.SEQ[2:]  # pasos ordinales, del más claro al más oscuro
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    for i, a in enumerate(anios):
        d = fac[fac["anio"] == a].sort_values("mes")
        c = ramp[min(i, len(ramp) - 1)]
        ax.plot(d["mes"], d["factor"], color=c, lw=2.2, marker="o", ms=4.5,
                mfc=c, mec=viz.SURFACE, mew=1.2, label=str(a))
    ax.axhline(1, color=viz.AXIS, lw=1, zorder=1)
    ax.set_xticks(range(1, 13), MES_ABR)
    ax.set_xlim(0.6, 12.4)
    viz.pct(ax)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}×"))
    viz.titulo(ax, "La forma del año turístico se repite: marzo arriba, septiembre abajo",
               "Factor estacional (observado ÷ tendencia STL); 1.00× = igual a la tendencia")
    ax.set_ylabel("Factor estacional")
    ax.legend(loc="lower center", ncol=len(anios), bbox_to_anchor=(0.5, -0.26))
    ax.annotate(FUENTE, xy=(0, -0.34), xycoords="axes fraction",
                fontsize=8, color=viz.MUTED)
    viz.guardar(fig, FIGS / "02_perfil_estacional.png")


def fig3_concentracion(nl: pd.DataFrame) -> None:
    h = A.hhi(nl, excluir=["República Dominicana"])
    r = h.rolling(12).mean()
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.plot(h.index, h.values, color=viz.SERIES[0], lw=1.4, alpha=0.55,
            label="HHI mensual")
    ax.plot(r.index, r.values, color=viz.SERIES[1], lw=2.8,
            label="Promedio móvil 12 meses")
    viz.titulo(ax, "La concentración subió hasta 2024 y desde entonces vuelve al punto de partida",
               "Índice Herfindahl-Hirschman de entradas por país de nacionalidad "
               "(excluye diáspora dominicana)")
    ax.set_ylabel("HHI (0 = diverso, 1 = un solo mercado)")
    ax.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.22))
    ax.annotate(FUENTE + " Calculado sobre los 20 mercados principales.",
                xy=(0, -0.30), xycoords="axes fraction", fontsize=8, color=viz.MUTED)
    viz.guardar(fig, FIGS / "03_concentracion_hhi.png")


def fig6_cuotas(nl: pd.DataFrame) -> None:
    """Lo que el HHI esconde: quién gana y quién pierde cuota."""
    c = A.cuotas(nl, top=6, excluir=["República Dominicana"])
    share = c.div(c.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    for i, pais in enumerate(share.columns):
        ax.plot(share.index, share[pais], color=viz.SERIES[i], lw=2.4,
                marker="o", ms=5, mfc=viz.SERIES[i], mec=viz.SURFACE, mew=1.4,
                label=pais)
        ax.annotate(f" {pais}", xy=(share.index[-1], share[pais].iloc[-1]),
                    fontsize=8.5, color=viz.INK_2, va="center")
    ax.set_yscale("log")
    ax.set_yticks([4, 6, 10, 20, 40, 60])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xticks(share.index)
    ax.set_xlim(share.index.min() - 0.15, share.index.max() + 1.3)
    viz.titulo(ax, "Estados Unidos cede cuota; Argentina casi la duplica",
               "Cuota en las entradas de los 6 mercados principales, escala logarítmica")
    ax.set_ylabel("Cuota del mercado extranjero")
    ax.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.30))
    ax.annotate(FUENTE + " 2026 cubre enero–julio.", xy=(0, -0.40),
                xycoords="axes fraction", fontsize=8, color=viz.MUTED)
    viz.guardar(fig, FIGS / "06_cuotas_mercado.png")


def fig4_zonas() -> None:
    z = A.cargar("ocupacion_zona")
    cols = [c for c in ["bavaro_punta_cana", "romana_bayahibe", "puerto_plata",
                        "gran_santo_domingo", "samana", "santiago"] if c in z.columns]
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.6), sharex=True, sharey=True)
    for ax, c in zip(axes.flat, cols):
        ax.plot(z.index, z[c].values, color=viz.SERIES[0], lw=2)
        ax.fill_between(z.index, 0, z[c].values, color=viz.SERIES[0], alpha=0.10)
        ax.set_title(ZONA_NOMBRE.get(c, c), fontsize=10)
        viz.pct(ax)
        ax.set_ylim(0.2, 1.0)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelrotation=0)
    fig.suptitle("Romana–Bayahíbe casi no tiene temporada baja; Puerto Plata vive de picos",
                 x=0.005, ha="left", fontsize=12, fontweight="600", color=viz.INK)
    fig.text(0.005, 0.925, "Ocupación hotelera abierta por zona turística, 2022–2026",
             fontsize=9, color=viz.MUTED)
    fig.text(0.005, -0.03, FUENTE, fontsize=8, color=viz.MUTED)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    viz.guardar(fig, FIGS / "04_ocupacion_zonas.png")


def fig5_backtest(y: pd.Series) -> pd.DataFrame:
    naive = A.naive_estacional(y, inicio=24)
    sar = A.backtest_sarimax(y, None, inicio=24)
    vue = A.cargar("vuelos")["vuelos_regulares"].reindex(y.index)
    sar_x = A.backtest_sarimax(y, vue, inicio=24)

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.plot(sar.index, sar["real"], color=viz.INK_2, lw=2.4, label="Real")
    ax.plot(sar.index, sar["pred"], color=viz.SERIES[0], lw=2.2, ls="--",
            label=f"SARIMAX 1 mes adelante (MAPE {A.mape(sar):.1f}%)")
    ax.plot(naive.index, naive["pred"], color=viz.SERIES[1], lw=1.8, ls=":",
            label=f"Referencia ingenua y(t−12) (MAPE {A.mape(naive):.1f}%)")
    viz.miles(ax)
    viz.titulo(ax, "El modelo le gana a la referencia ingenua por ~1.8 puntos de MAPE",
               "Validación out-of-sample, ventana expansiva, un mes adelante")
    ax.set_ylabel("Pasajeros no residentes extranjeros")
    ax.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.24), fontsize=8.5)
    ax.annotate(FUENTE, xy=(0, -0.32), xycoords="axes fraction",
                fontsize=8, color=viz.MUTED)
    viz.guardar(fig, FIGS / "05_backtest.png")

    return pd.DataFrame({
        "modelo": ["Ingenuo y(t−12)", "SARIMAX", "SARIMAX + vuelos"],
        "mape_pct": [A.mape(naive), A.mape(sar), A.mape(sar_x)],
        "n_pronosticos": [len(naive), len(sar), len(sar_x)],
    })


def main() -> None:
    viz.use_theme()
    f = A.cargar("flujo_migratorio")
    y = f["ent_nr_ext"]
    nl = A.nacionalidad_long()

    fig1_tendencia(y)
    fig2_estacionalidad(y)
    fig3_concentracion(nl)
    fig6_cuotas(nl)
    fig4_zonas()
    tabla = fig5_backtest(y)

    print("\nComparación de modelos:")
    print(tabla.to_string(index=False))

    panel = A.panel_zona_aeropuerto()
    m = A.efectos_fijos_zona(panel)
    b = m.params["log_llegadas"]
    print(f"\nEfectos fijos zona+mes: +10% de llegadas extranjeras al aeropuerto "
          f"de la zona -> {b*np.log(1.1)*100:+.2f} pp de ocupación "
          f"(p={m.pvalues['log_llegadas']:.3f}, R2={m.rsquared:.2f}, n={int(m.nobs)})")


if __name__ == "__main__":
    main()
