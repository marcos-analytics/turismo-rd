**English** · [Español](README.es.md)

# Dominican tourism: seasonality, source markets and forecasting

Analysis of official open data on the Dominican tourism sector,
January 2022 – July 2026 (55 months).

**The question:** Dominican tourism grew sharply after the pandemic. Did that growth
change the *structure* of the sector — when people arrive, where they come from, and
which resort area they go to — or is there simply more of the same?

![Trend in arrivals of non-resident foreign passengers, 2022-2026](reports/figures/01_llegadas_tendencia.png)

## Findings, and what to do about them

| Finding | What it means for a decision |
|---|---|
| **Trend.** +46.9% in the STL trend over 4.5 years, with no sign of saturation. | The growth is structural, not a rebound. The constraint to watch is capacity — rooms and airline seats — not demand. |
| **Seasonality.** It did not flatten: the amplitude of the seasonal factor holds at ~0.5–0.6 every year, and September sits ~35% below trend. | Whatever is being done to fill the low season is not moving the needle. Before spending more on the same thing, make it measurable: annual seasonal amplitude is the indicator, and it has to fall consistently — not one good September. |
| **Source markets.** The US falls from 59% to 54% of share; Argentina goes from 5.6% to 9.5%. Europe loses ground. | Diversification is already happening on its own, and it is South American. The cheap margin is in following that current — air connectivity and marketing toward the Southern Cone — rather than trying to win Europe back, which is moving the other way. And Argentines arrive during the northern low season: the previous problem, solved by another route. |
| **Forecasting.** SARIMAX one month ahead: **3.9% MAPE** vs 5.7% for the seasonal-naive benchmark `y(t−12)`. Adding scheduled flights as an exogenous regressor **makes the model worse**. | A 3.9% error one month out is good enough to plan staffing and hotel purchasing. The simple model wins: this does not need more complexity, it needs more history. |

A fifth result — the elasticity between arrivals at an airport and occupancy in its
resort area — stayed in the notebook and is **deliberately kept out of this table**.
It is positive (+0.76 pp for every +10% in arrivals) but rests on only six clusters
and on an airport→area mapping I built myself. That is a hypothesis, not a conclusion.

Every figure is in [`reports/figures/`](reports/figures), and the full analysis — with
the reasoning and the limits of each result — is in
[`notebooks/analisis.ipynb`](notebooks/analisis.ipynb).

> The notebook, the code comments and the commit history are in Spanish: the sources,
> the column names and the domain vocabulary are Spanish, and translating them would
> have put a layer between the code and the data it reads.

## Data

Everything comes from official Dominican open data:

| Source | What it provides | Coverage |
|---|---|---|
| [SITUR / MITUR](https://situr.mitur.gob.do/estadisticas/descargas/) | Migration flow, arrivals by airport, country of nationality and residence, city of departure, hotel occupancy by area, flights | Monthly, 2022–present |
| [Central Bank, tourism sector](https://www.bancentral.gov.do/a/d/2537-sector-turismo) | Total arrivals, tourist spending, average stay, sector value added | Annual/monthly, since 1978 |
| [ONE — Statistics](https://www.one.gob.do/datos-y-estadisticas/) | Demographic and economic context, household survey, census | Varies |

The exact URL of every file lives in `src/config.py`.

### Why the official spreadsheets need a parser

The SITUR files are not clean tables: they carry the institutional logo, titles in the
first rows, **two-level headers with merged cells**, the year written once per block of
twelve months, month names in Spanish, and footnotes. A plain `pd.read_excel()` returns
garbage. `src/tidy.py` handles it generically: it locates the `Año | Mes` row,
reconstructs column names by combining the levels above, forward-fills the year, and
drops the footnotes.

## Running it

```bash
pip install -r requirements.txt

python -m src.download    # downloads the official spreadsheets to data/raw/
python -m src.build       # cleans them into data/processed/*.csv
python -m src.figuras     # generates reports/figures/*.png
jupyter lab notebooks/analisis.ipynb
```

The repo ships a **snapshot** of `data/processed/` (data as of 5 August 2026) so the
notebook runs without depending on the source servers being up. One difference: the
snapshot of `nacionalidad_wide.csv` carries the **top 20 markets**; running `src.build`
yields all 135 countries, and the HHI drops slightly as a result. The conclusions do not
change — the decimals do.

## Layout

```
src/config.py     URLs for every source + airport→area mapping
src/download.py   downloads the raw spreadsheets
src/tidy.py       parsers for the SITUR files (two-level headers)
src/build.py      raw → processed, the contract with the notebooks
src/analisis.py   STL, HHI, fixed-effects panel, SARIMAX backtest
src/viz.py        chart theme (colorblind-validated palette)
src/figuras.py    generates every figure
notebooks/        the narrated analysis
```

## Methodological decisions

- **"Tourist" = non-resident foreigner.** The official data separates residence
  (resident / non-resident) from nationality (Dominican / foreign). A Dominican from
  the diaspora visiting home is a *non-resident Dominican*: they count in arrivals but
  follow a different calendar (peak in December, not March) and a different spending
  pattern. They are analysed separately.
- **Robust STL rather than classical decomposition.** With `robust=True`, outlier
  months do not drag the seasonal component.
- **Expanding-window validation, never `train_test_split`.** In time series, a random
  split leaks the future into training and produces a falsely low error. Here the model
  is refit at each month using only the past.
- **Every forecast competes against `y(t−12)`.** A model that cannot beat the same
  month last year adds nothing.

## Known limits

- Only 55 months. Enough for seasonality and one-month-ahead forecasting; not enough
  for claims about long cycles. That needs the Central Bank series (arrivals since 1978).
- The airport→area panel has **six clusters**: clustered standard errors are fragile
  with that few groups, and the p-value of 0.047 is not a hard boundary.
- That same airport→area mapping is a **working hypothesis**, not official data. It is
  declared in `src/config.py` precisely so it can be changed.
- The flights↔occupancy relationship is **endogenous**: airlines add capacity where
  demand already exists. These are conditional associations, not causal effects.

## License

Code under MIT. The data belongs to MITUR, the Central Bank and ONE, and is governed by
each institution's terms.
