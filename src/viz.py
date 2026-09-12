"""Tema de gráficos: una sola definición para todas las figuras del proyecto.

Paleta categórica validada para daltonismo (orden fijo, nunca ciclada).
Regla del proyecto: un solo eje y por gráfico, leyenda siempre que haya 2+
series, rejilla discreta, sin números sobre cada punto.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def use_theme() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "600",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 9.5,
        "axes.labelcolor": INK_2,
        "text.color": INK,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "legend.frameon": False,
        "legend.fontsize": 9,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
    })


def titulo(ax, titulo_txt: str, subtitulo: str | None = None) -> None:
    """Título con subtítulo: el título dice el hallazgo, el subtítulo la unidad."""
    if subtitulo:
        ax.set_title(titulo_txt, color=INK, pad=32)
        ax.annotate(subtitulo, xy=(0, 1.008), xycoords="axes fraction",
                    fontsize=9, color=MUTED, va="bottom")
    else:
        ax.set_title(titulo_txt, color=INK)


def miles(ax) -> None:
    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k" if v >= 1000 else f"{v:,.0f}")
    )


def pct(ax) -> None:
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v:.0%}"))


def guardar(fig, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    print(f"  figura -> {path.name}")
