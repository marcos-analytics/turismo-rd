"""Genera notebooks/analisis.ipynb (así el notebook queda versionado como código)."""
import json
from pathlib import Path

md = lambda s: {"cell_type": "markdown", "metadata": {}, "source": s.strip()}
code = lambda s: {"cell_type": "code", "metadata": {}, "execution_count": None,
                  "outputs": [], "source": s.strip()}

cells = [
md("""
# Turismo en República Dominicana: estacionalidad, mercados y predicción

**Pregunta central:** el turismo dominicano creció con fuerza después de la pandemia.
¿Ese crecimiento cambió la *estructura* del sector — cuándo llega la gente, de dónde
viene, y a qué polo turístico va — o simplemente hay más de lo mismo?

Se responde en cuatro partes:

1. **Tendencia vs. estacionalidad** — separar el crecimiento real del vaivén del calendario (STL).
2. **Mercados de origen** — concentración (HHI) y quién gana o pierde cuota.
3. **Aeropuerto → ocupación hotelera** — panel con efectos fijos de zona y mes.
4. **Predicción** — SARIMAX contra una referencia ingenua, validado out-of-sample.

**Datos:** SITUR / Ministerio de Turismo (mensual, 2022-01 a 2026-07, 55 meses).
Los Excel oficiales se descargan con `python -m src.download` y se limpian con
`python -m src.build`.
"""),

code("""
import warnings; warnings.filterwarnings("ignore")
import sys; sys.path.insert(0, "..")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import analisis as A, viz
viz.use_theme()

flujo = A.cargar("flujo_migratorio")
print(f"{len(flujo)} meses: {flujo.index.min():%Y-%m} a {flujo.index.max():%Y-%m}")
flujo.head(3)
"""),

md("""
## 0. Qué mide cada columna

El dato oficial distingue dos ejes que se confunden fácil:

- **residencia**: *no residente* (turista, el que nos interesa) vs *residente*.
- **nacionalidad**: *dominicano* vs *extranjero*.

Un dominicano de la diáspora que viene de visita es **no residente dominicano**: entra
en las cifras de "llegadas" pero no se comporta como turista de sol y playa — se queda
en casa de familiares, viaja en diciembre y agosto. Por eso casi todo el análisis usa
`ent_nr_ext` (no residentes extranjeros) y trata a la diáspora aparte.
"""),

code("""
tot = flujo[["ent_nr_ext", "ent_nr_dom"]].sum()
print(f"No residentes extranjeros : {tot['ent_nr_ext']:,.0f}")
print(f"No residentes dominicanos : {tot['ent_nr_dom']:,.0f}  "
      f"({tot['ent_nr_dom']/tot.sum():.1%} del total)")

# La diáspora tiene un calendario propio: comparemos el mes pico de cada grupo.
perfil = (flujo.assign(mes=flujo.index.month)
               .groupby("mes")[["ent_nr_ext", "ent_nr_dom"]].mean())
perfil = perfil / perfil.mean()
print("\\nMes pico  extranjeros:", perfil['ent_nr_ext'].idxmax(),
      "| diáspora:", perfil['ent_nr_dom'].idxmax())
"""),

md("""
## 1. ¿Crecimiento o rebote? Descomposición STL

El nivel mensual no dice nada por sí solo: marzo siempre es alto y septiembre siempre
es bajo. STL separa la serie en **tendencia + estacionalidad + resto**, y con *robust=True*
los meses atípicos (huracanes, Semana Santa corrida) no arrastran el ajuste.
"""),

code("""
y = flujo["ent_nr_ext"]
res = A.stl(y)

crec = res.trend.iloc[-1] / res.trend.iloc[0] - 1
print(f"Tendencia: {res.trend.iloc[0]:,.0f} -> {res.trend.iloc[-1]:,.0f}  ({crec:+.1%} en 4.5 años)")
print(f"Peso de la estacionalidad: sd(estacional)/sd(serie) = "
      f"{res.seasonal.std()/y.std():.2f}")
print(f"Meses más atípicos (residuo STL):")
print((res.resid / y.std()).abs().nlargest(3).round(2).to_string())
"""),

md("""
![tendencia](../reports/figures/01_llegadas_tendencia.png)

La tendencia sube de forma casi lineal, sin la curva de saturación que tendría un simple
rebote post-pandemia. El crecimiento no se agotó.

### ¿Cambió la *forma* del año?

Si el sector se estuviera desestacionalizando, la distancia entre el mejor y el peor mes
se achicaría año con año. Se mide con el factor estacional (observado ÷ tendencia).
"""),

code("""
amp = A.amplitud_estacional(y)
print("Amplitud estacional (máx - mín del factor), solo años completos:")
print(amp.round(3).to_string())
print("\\nNo hay una tendencia clara a la baja: la estacionalidad no cede.")
"""),

md("""
![estacionalidad](../reports/figures/02_perfil_estacional.png)

Las cinco curvas casi se superponen. **La estacionalidad no se aplanó**: el sector creció
de nivel manteniendo intacto su calendario. Marzo por encima de la tendencia, septiembre
casi un 35% por debajo — todos los años.
"""),

md("""
## 2. Mercados de origen: ¿diversificación o dependencia?

El HHI suma los cuadrados de las cuotas de mercado. Su inverso `1/HHI` se lee directo:
**cuántos mercados "equivalentes" sostienen al sector**. Se excluye a República Dominicana
porque su flujo es diáspora, no turismo de mercado.
"""),

code("""
nl = A.nacionalidad_long()
h = A.hhi(nl, excluir=["República Dominicana"])
r12 = h.rolling(12).mean()

for f in ["2023-01-01", "2024-07-01", "2026-07-01"]:
    print(f"{f[:7]}  HHI {r12.loc[f]:.3f}  ->  {1/r12.loc[f]:.1f} mercados equivalentes")
"""),

md("""
![hhi](../reports/figures/03_concentracion_hhi.png)

La concentración **subió hasta mediados de 2024 y luego bajó** hasta volver casi al punto
de partida. Un índice agregado esconde el movimiento: hay que mirar quién se mueve.
"""),

code("""
c = A.cuotas(nl, top=6, excluir=["República Dominicana"])
share = (c.div(c.sum(axis=1), axis=0) * 100).round(1)
share
"""),

md("""
![cuotas](../reports/figures/06_cuotas_mercado.png)

Ahí está la historia real: **Estados Unidos baja de 59% a 54%** y **Argentina pasa de
5.6% a 9.5%**. La diversificación existe, pero es sudamericana — no viene de Europa, que
en el mismo periodo pierde peso (Reino Unido cae de 5.5% a 3.5%).
"""),

md("""
## 3. ¿Cuánto del negocio hotelero explica el aeropuerto?

Cada polo turístico tiene su puerta de entrada. Si el flujo aéreo de un aeropuerto
predice la ocupación de su zona, la capacidad aérea es una palanca de política pública.

El mapeo aeropuerto→zona está en `src/config.py` y es una **hipótesis de trabajo**, no un
dato oficial: Punta Cana → Bávaro-Punta Cana, La Romana → Romana-Bayahíbe, etc.

Especificación: `ocupación ~ log(llegadas extranjeras) + efectos fijos de zona + de mes`.
Los efectos fijos de zona absorben el nivel estructural de cada polo (Bayahíbe vive de
*all-inclusive* con ocupación alta todo el año; Santo Domingo es negocios). Los de mes
absorben la estacionalidad común del país. Lo que sobra es la respuesta al flujo propio.
"""),

code("""
panel = A.panel_zona_aeropuerto()
m = A.efectos_fijos_zona(panel)

b = m.params["log_llegadas"]
print(f"beta log(llegadas) = {b:.4f}   p = {m.pvalues['log_llegadas']:.3f}")
print(f"Lectura: +10% de llegadas extranjeras -> {b*np.log(1.1)*100:+.2f} pp de ocupación")
print(f"R2 = {m.rsquared:.3f}   n = {int(m.nobs)} (zona x mes)")
"""),

md("""
**Cómo leerlo con honestidad.** El efecto es positivo y significativo al 5%, pero es
**pequeño**: duplicar las llegadas de un aeropuerto sube la ocupación de su zona apenas
~5.5 pp. Tiene sentido económico — la oferta hotelera también crece, así que más
pasajeros se reparten entre más habitaciones.

Tres límites que hay que declarar antes de que los encuentre otro:

1. **Seis clusters.** Los errores estándar agrupados por zona son frágiles con tan pocos
   grupos; el p-valor de 0.047 no debe leerse como una frontera dura.
2. **Endogeneidad.** Las aerolíneas ponen vuelos *donde* hay demanda hotelera, así que la
   causalidad corre en los dos sentidos. Esto es una asociación condicional, no un efecto causal.
3. **El mapeo es mío.** Cambiar Cibao→Santiago por Cibao→Puerto Plata movería el resultado.
   Vale la pena reestimarlo con mapeos alternativos como prueba de robustez.
"""),

md("""
## 4. Predicción: ¿le ganamos a la referencia ingenua?

La regla de oro en series de tiempo: **todo modelo compite contra `y(t-12)`** — el mismo
mes del año pasado. Y la validación tiene que ser *out-of-sample con ventana expansiva*:
en cada mes se reajusta el modelo usando solo el pasado. Un `train_test_split` aleatorio
filtraría el futuro dentro del entrenamiento y daría un error falsamente bajo.
"""),

code("""
naive = A.naive_estacional(y, inicio=24)
sar   = A.backtest_sarimax(y, None, inicio=24)
vue   = A.cargar("vuelos")["vuelos_regulares"].reindex(y.index)
sar_x = A.backtest_sarimax(y, vue, inicio=24)

pd.DataFrame({
    "modelo": ["Ingenuo y(t-12)", "SARIMAX(1,0,0)(1,1,0,12)", "SARIMAX + vuelos regulares"],
    "MAPE %": [A.mape(naive), A.mape(sar), A.mape(sar_x)],
    "n": [len(naive), len(sar), len(sar_x)],
}).round(2)
"""),

md("""
![backtest](../reports/figures/05_backtest.png)

**SARIMAX baja el MAPE de 5.7% a 3.9%** — una mejora de un tercio sobre la referencia.

Y un resultado negativo que vale la pena reportar: **agregar los vuelos regulares como
regresor exógeno empeora el modelo** (4.3%). La razón es que para pronosticar con un
exógeno hay que conocerlo de antemano; el número de vuelos ya está contenido en la propia
historia de llegadas, así que solo agrega parámetros que estimar con 55 observaciones.
Menos es más cuando la muestra es corta.
"""),

md("""
## 5. Conclusiones y recomendaciones

Cada hallazgo con la decisión que habilita y cómo se sabría si funcionó.

**1. El crecimiento es estructural, no rebote.** La tendencia STL sube de forma sostenida
sin señales de agotamiento.
→ *Decisión:* la restricción a vigilar es de **capacidad** (habitaciones, asientos), no de
demanda. La pregunta de planificación no es "cómo atraemos más", es "dónde se satura primero".
→ *Cómo medirlo:* seguir `disp_efectiva` del dato hotelero contra la tendencia de llegadas;
si la ocupación sube mientras la disponibilidad no, la capacidad ya es el cuello de botella.

**2. La estacionalidad no se aplanó.** Septiembre sigue ~35% por debajo de la tendencia
todos los años, y la amplitud estacional no baja.
→ *Decisión:* lo que se esté haciendo para llenar la temporada baja no está funcionando.
Antes de repetir el gasto, hay que poder medirlo.
→ *Cómo medirlo:* la **amplitud del factor estacional por año** es el KPI (hoy ~0.5–0.6).
Una campaña de temporada baja que sirva la hace bajar de forma sostenida por dos o tres
años; un septiembre bueno suelto no prueba nada.

**3. La diversificación es real pero sudamericana.** EE.UU. cede cinco puntos de cuota,
Argentina casi duplica la suya, Europa pierde peso.
→ *Decisión:* el margen barato está en **acompañar la corriente que ya existe** —
conectividad y promoción hacia el Cono Sur — en vez de intentar recuperar Europa, que va
en contra. Y tiene un beneficio cruzado: el verano austral cae en la temporada baja del
hemisferio norte, así que el punto 2 se resuelve en parte por esta vía.
→ *Cómo medirlo:* cuota sudamericana y HHI en paralelo; si la cuota sube pero el HHI no
baja, se está cambiando una dependencia por otra.

**4. Un SARIMAX simple pronostica el mes siguiente con ~3.9% de error**, un tercio mejor
que la referencia ingenua; agregarle vuelos no ayuda.
→ *Decisión:* ese error ya es **operativamente útil** para planificar personal, compras y
turnos con un mes de anticipación. No hace falta un modelo más complejo: hace falta más
historia y horizontes más largos.
→ *Cómo medirlo:* seguir el MAPE mes a mes contra `y(t−12)`; el día que el modelo deje de
ganarle, algo cambió en el régimen y hay que reestimarlo.

**Un quinto resultado que dejo fuera de las recomendaciones a propósito:** la elasticidad
entre llegadas por aeropuerto y ocupación de su zona (parte 3) es positiva pero descansa en
seis clusters y en un mapeo que armé yo. Da para una hipótesis que vale la pena probar con
mejores datos, no para recomendar nada todavía.

### Qué haría después

- Enganchar las series largas del Banco Central (llegadas desde 1978, gasto turístico
  desde 1993) para ver si el patrón estacional de 2022-2026 es histórico o nuevo.
- Traer gasto por turista para pasar de "cuántos vienen" a "cuánto dejan" — el argentino
  se queda más noches que el estadounidense, y eso cambia el ranking de mercados.
- Reestimar la parte 3 con mapeos aeropuerto→zona alternativos y con la ocupación por
  zona *y segmento* (la hoja ya está en el Excel de SITUR).
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4, "nbformat_minor": 5,
}

out = Path(__file__).parent / "notebooks" / "analisis.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"-> {out}  ({len(cells)} celdas)")
