"""Fuentes de datos del proyecto.

Todas son fuentes oficiales dominicanas de acceso abierto:
  - SITUR / MITUR  -> microdatos mensuales 2022-presente (muy granular)
  - Banco Central  -> series largas 1978-presente (para contexto histórico)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIGS = ROOT / "reports" / "figures"

# ---------------------------------------------------------------- SITUR (MITUR)
# Mensual, 2022-01 en adelante. Estructura: encabezados en dos niveles,
# columna "Año" solo en el primer mes de cada año, meses en español.
SITUR = "https://situr.mitur.gob.do/wp-content/uploads/estadisticas/mensual/"

SITUR_FILES = {
    "flujo_migratorio":  "1. Flujo migratorio.xlsx",
    "pais_residencia":   "2. Por país de residencia.xlsx",
    "pais_nacionalidad": "4. Por país de nacionalidad.xlsx",
    "origen_destino":    "5. Origen y destino.xlsx",
    "hotel_tradicional": "1. Actividad hotelera - zonas tradicionales.xlsx",
    "hotel_mitur":       "2. Actividad hotelera - zonas MITUR.xlsx",
    "vuelos_llegadas":   "1. Llegadas de vuelos.xlsx",
    "vuelos_ocupacion":  "2. Ocupación de vuelos.xlsx",
    "maritimas":         "1. Llegadas marítimas.xlsx",
}

# ------------------------------------------------------ Banco Central (BCRD)
# Series largas. Útiles para poner el periodo 2022-2026 en perspectiva.
BCRD = "https://cdn.bancentral.gov.do/documents/estadisticas/sector-turismo/documents/"

BCRD_FILES = {
    "llegadas_total_1978":   "lleg_total.xls",              # llegadas 1978-presente
    "gasto_estadia_1993":    "turismo_gasto_estadia.xls",   # gasto turístico + estadía promedio
    "gasto_estadia_dom_res": "turismo_gasto_estadia_dom_res.xls",
    "gasto_estadia_dom_nr":  "turismo_gasto_estadia_dom_no_res.xls",
    "valor_agregado_1980":   "turismo_valor.xlsx",          # valor agregado del sector
    "maritima_1994":         "lleg_maritima_1994-2025.xls",
    "fiscal_1998":           "turismo_fiscal.xls",
}

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# Mapeo aeropuerto -> zona hotelera. Es una hipótesis de trabajo, no oficial:
# se usa para probar si el flujo de un aeropuerto explica la ocupación de su zona.
AEROPUERTO_A_ZONA = {
    "punta_cana":   "bavaro_punta_cana",
    "la_romana":    "romana_bayahibe",
    "puerto_plata": "puerto_plata",
    "las_americas": "gran_santo_domingo",
    "samana":       "samana",
    "cibao":        "santiago",
}
