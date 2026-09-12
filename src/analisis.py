"""Funciones de análisis reutilizables por los notebooks.

Cada función hace una cosa y devuelve un DataFrame o un objeto de statsmodels;
los gráficos viven en los notebooks y en src/figuras.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PROC


# --------------------------------------------------------------------- carga
def cargar(nombre: str, index_fecha: bool = True) -> pd.DataFrame:
    df = pd.read_csv(PROC / f"{nombre}.csv")
    if index_fecha and "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.set_index("fecha").asfreq("MS")
    return df


def nacionalidad_long() -> pd.DataFrame:
    w = pd.read_csv(PROC / "nacionalidad_wide.csv").set_index("pais")
    w.columns = pd.to_datetime(w.columns)
    return (w.stack().rename("pasajeros").reset_index()
            .rename(columns={"level_1": "fecha"}))


# ------------------------------------------------------------ estacionalidad
def stl(serie: pd.Series, robust: bool = True):
    """Descomposición STL. Devuelve el resultado de statsmodels."""
    from statsmodels.tsa.seasonal import STL
    return STL(serie.dropna(), period=12, robust=robust).fit()


def indice_estacional(serie: pd.Series) -> pd.DataFrame:
    """Factor estacional por mes y año: valor / tendencia STL.

    >1 = mes por encima de la tendencia. Permite ver si el perfil estacional
    cambia de un año a otro, no solo cuál es el promedio.
    """
    res = stl(serie)
    fac = (serie / res.trend).rename("factor").to_frame()
    fac["anio"] = fac.index.year
    fac["mes"] = fac.index.month
    return fac


def amplitud_estacional(serie: pd.Series) -> pd.Series:
    """Rango del factor estacional dentro de cada año (max - min).

    Es la métrica de "cuán estacional" es un año: si cae, la demanda se está
    repartiendo mejor a lo largo del calendario.
    """
    fac = indice_estacional(serie)
    completos = fac.groupby("anio")["mes"].count()
    amp = fac.groupby("anio")["factor"].agg(lambda s: s.max() - s.min())
    return amp[completos == 12]


# ------------------------------------------------------- concentración de mercados
def hhi(df_long: pd.DataFrame, excluir: list[str] | None = None) -> pd.Series:
    """Índice Herfindahl-Hirschman de cuotas por país, mes a mes (0-1).

    Se excluye a República Dominicana por defecto: sus "no residentes" son
    diáspora, un mercado con dinámica distinta al turismo extranjero.
    1/n = diversificación perfecta; 1 = un solo mercado.
    """
    d = df_long if excluir is None else df_long[~df_long["pais"].isin(excluir)]
    tot = d.groupby("fecha")["pasajeros"].transform("sum")
    return (d.assign(s2=(d["pasajeros"] / tot) ** 2)
             .groupby("fecha")["s2"].sum().rename("hhi"))


def cuotas(df_long: pd.DataFrame, top: int = 8, excluir: list[str] | None = None) -> pd.DataFrame:
    d = df_long if excluir is None else df_long[~df_long["pais"].isin(excluir)]
    orden = d.groupby("pais")["pasajeros"].sum().nlargest(top).index
    anual = (d[d["pais"].isin(orden)]
             .assign(anio=lambda x: x["fecha"].dt.year)
             .pivot_table(index="anio", columns="pais", values="pasajeros", aggfunc="sum"))
    return anual[list(orden)]


# --------------------------------------------- aeropuerto -> ocupación por zona
def panel_zona_aeropuerto() -> pd.DataFrame:
    """Panel largo (zona x mes) con ocupación y llegadas del aeropuerto asociado."""
    from .config import AEROPUERTO_A_ZONA

    aer = cargar("entradas_aeropuerto")
    zon = cargar("ocupacion_zona")
    filas = []
    for aeropuerto, zona in AEROPUERTO_A_ZONA.items():
        col = f"ext_{aeropuerto}"
        if col not in aer.columns or zona not in zon.columns:
            continue
        filas.append(pd.DataFrame({
            "fecha": aer.index,
            "zona": zona,
            "llegadas_ext": aer[col].values,
            "ocupacion": zon[zona].reindex(aer.index).values,
        }))
    p = pd.concat(filas, ignore_index=True).dropna()
    p["log_llegadas"] = np.log(p["llegadas_ext"].clip(lower=1))
    p["mes"] = p["fecha"].dt.month
    return p


def efectos_fijos_zona(panel: pd.DataFrame):
    """OLS con efectos fijos de zona y de mes: ocupación ~ log(llegadas).

    Los efectos fijos de zona absorben el nivel estructural de cada polo
    turístico; los de mes, la estacionalidad común. Lo que queda es la
    respuesta de la ocupación a su propio flujo aéreo.
    """
    import statsmodels.formula.api as smf
    return smf.ols("ocupacion ~ log_llegadas + C(zona) + C(mes)", data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel["zona"]}
    )


# -------------------------------------------------------------- nowcasting
def backtest_sarimax(y: pd.Series, exog: pd.Series | None = None,
                     inicio: int = 36, orden=(1, 0, 0), estacional=(1, 1, 0, 12)) -> pd.DataFrame:
    """Validación out-of-sample expanding-window, 1 mes adelante.

    Reajusta el modelo en cada paso usando solo información disponible hasta
    ese momento: es la única forma honesta de medir un modelo de series de
    tiempo (un train/test aleatorio filtraría el futuro).
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    y = y.dropna()
    filas = []
    for t in range(inicio, len(y)):
        ytr = y.iloc[:t]
        xtr = exog.iloc[:t] if exog is not None else None
        xte = exog.iloc[t:t + 1] if exog is not None else None
        try:
            fit = SARIMAX(ytr, exog=xtr, order=orden, seasonal_order=estacional,
                          trend="c" if estacional[1] == 0 else None,
                          enforce_stationarity=False).fit(disp=False)
            pred = float(fit.forecast(1, exog=xte).iloc[0])
        except Exception:  # noqa: BLE001
            continue
        filas.append({"fecha": y.index[t], "real": float(y.iloc[t]), "pred": pred})

    out = pd.DataFrame(filas).set_index("fecha")
    out["error"] = out["pred"] - out["real"]
    out["ape"] = (out["error"].abs() / out["real"])
    return out


def naive_estacional(y: pd.Series, inicio: int = 36) -> pd.DataFrame:
    """Referencia obligatoria: el valor del mismo mes del año anterior.

    Un modelo que no le gana a esto no aporta nada.
    """
    y = y.dropna()
    out = pd.DataFrame({"real": y.iloc[inicio:], "pred": y.shift(12).iloc[inicio:]}).dropna()
    out["error"] = out["pred"] - out["real"]
    out["ape"] = out["error"].abs() / out["real"]
    return out


def mape(df: pd.DataFrame) -> float:
    return float(df["ape"].mean() * 100)
