# Cómo subirlo a GitHub

El repositorio ya está inicializado y con el primer commit hecho. Falta enlazarlo
con GitHub y empujarlo, y eso requiere tus credenciales.

## Antes: no lo subas a `marcos-analytics/marcos-analytics`

Ese repositorio es especial. Cuando un repo se llama igual que tu usuario, GitHub
usa su `README.md` como **la portada de tu perfil** — es lo que ve cualquiera que
entre a `github.com/marcos-analytics`. Si metes el proyecto ahí dentro, mezclas tu
carta de presentación con el código de un análisis, y el proyecto queda sin URL
propia que puedas poner en el CV.

Lo correcto son dos repos con trabajos distintos:

| Repositorio | Qué es |
|---|---|
| `marcos-analytics/marcos-analytics` | Tu perfil. Solo un `README.md` que presenta quién eres y enlaza tus proyectos. |
| `marcos-analytics/turismo-rd` | Este proyecto, con su propia URL para el CV y LinkedIn. |

Al final de este archivo hay un bloque listo para pegar en el README del perfil.

## Los comandos

Crea el repositorio vacío en <https://github.com/new> con el nombre `turismo-rd`,
**sin** marcar "Add a README" ni "Add .gitignore" ni licencia (este proyecto ya
los trae). Después, desde la carpeta del proyecto:

```bash
git remote add origin https://github.com/marcos-analytics/turismo-rd.git
git push -u origin main
```

Git te va a pedir usuario y contraseña. GitHub ya no acepta la contraseña de la
cuenta: hay que usar un **personal access token**. Se crea en
Settings → Developer settings → Personal access tokens → Tokens (classic), con
el permiso `repo` marcado. Ese token es el que pegas donde dice "password".

Si prefieres evitar eso, instala [GitHub CLI](https://cli.github.com/) y corre
`gh auth login` una sola vez; después `gh repo create turismo-rd --public --source=. --push`
hace todo en un comando.

## Después de subirlo

1. En la página del repo, botón **About** (engranaje, arriba a la derecha):
   - Descripción: *Análisis de la estructura del turismo dominicano 2022–2026:
     estacionalidad, mercados de origen y pronóstico. Python, pandas, statsmodels.*
   - Topics: `data-analysis` `python` `pandas` `statsmodels` `time-series`
     `open-data` `dominican-republic` `tourism`
   - Website: el enlace de la página publicada.
2. Verifica que las imágenes del README se vean. Si no, es que la carpeta
   `reports/figures/` no subió.

## Bloque para el README de tu perfil

Pégalo en `marcos-analytics/marcos-analytics/README.md`:

```markdown
### Turismo dominicano 2022–2026

Análisis de la estructura del sector turístico sobre datos abiertos de SITUR/MITUR
y el Banco Central: 55 meses, 135 mercados de origen.

- La estacionalidad **no se aplanó** pese a un crecimiento de 46.9% en la tendencia:
  septiembre sigue 35% por debajo, todos los años.
- Estados Unidos cede cinco puntos de cuota y los absorbe Sudamérica, no Europa.
- Un SARIMAX pronostica el mes siguiente con **3.9% de MAPE**, un tercio mejor que
  la referencia ingenua.

Python · pandas · statsmodels · STL · SARIMAX · OLS con efectos fijos

[Repositorio](https://github.com/marcos-analytics/turismo-rd) · [Análisis completo](AQUÍ_EL_ENLACE_DE_LA_PÁGINA)
```
