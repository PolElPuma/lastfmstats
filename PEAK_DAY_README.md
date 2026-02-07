# Función: Calcular Pico Diario de Canciones

## Descripción

Se han agregado dos funciones nuevas a la clase `ScrobblesAnalyzer` que permiten calcular el día en el que más veces se escuchó una canción específica:

### `get_peak_day_for_track(scrobbles, artist, track)`

Calcula el día con más escuchas para una canción dada.

**Parámetros:**
- `scrobbles`: Lista de scrobbles
- `artist`: Nombre exacto del artista
- `track`: Nombre exacto de la canción

**Retorna:** 
- Tupla `(fecha_str, escuchas_ese_día, total_escuchas)`
- Ejemplo: `("17 Nov 2025", 64, 194)`
- `None` si la canción no se encuentra

---

### `get_all_days_for_track(scrobbles, artist, track)`

Obtiene todos los días en que se escuchó una canción, con los conteos ordenados descendentemente.

**Parámetros:** Iguales a `get_peak_day_for_track`

**Retorna:**
- Lista de tuplas `[(fecha_str, escuchas), ...]` ordenadas por escuchas descendentes
- Ejemplo: `[("17 Nov 2025", 64), ("28 Nov 2025", 38), ...]`
- `None` si la canción no se encuentra

---

## ⚠️ Importante: Zona Horaria

**Las fechas se calculan basándose en la zona horaria local del equipo que ejecuta el programa.**

- Los datos originales de Last.fm están en **UTC+0**
- Las funciones convierten cada timestamp UTC al horario local
- Un día se define como: **00:00 a 23:59 en la zona horaria local**

Por ejemplo, si estás en UTC+2:
- Una canción escuchada a las 23:00 UTC se cuenta como si fuera las 01:00 (del día siguiente en tu zona horaria)

---

## Funciones de Visualización

```python
display_peak_day_for_track(peak_day_result)
```
Muestra el día pico con tabla de información:
- Fecha del pico
- Escuchas ese día
- Total de escuchas
- Porcentaje del día

```python
display_all_days_for_track(days_result, artist, track)
```
Muestra un historial completo con:
- Todos los días en que se escuchó la canción
- Escuchas en cada día
- Gráfico de barras visual (█ lleno, ░ vacío)
- Porcentaje de escuchas por día

---

## Ejemplos de Uso

### Ejemplo 1: Encontrar el pico de una canción

```python
from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer,
    display_peak_day_for_track
)

# Cargar datos
loader = ScrobblesLoader('data')
scrobbles = loader.load_file(loader.list_files()[0])

# Buscar pico diario
peak = ScrobblesAnalyzer.get_peak_day_for_track(
    scrobbles,
    artist="Radiohead",
    track="Creep"
)

if peak:
    display_peak_day_for_track(peak)
    # Salida:
    # Fecha: 17 Nov 2025
    # Escuchas ese día: 64
    # Total escuchas: 194
    # Porcentaje del día: 32.99%
```

---

### Ejemplo 2: Ver historial completo

```python
from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer,
    display_all_days_for_track
)

# Cargar datos
loader = ScrobblesLoader('data')
scrobbles = loader.load_file(loader.list_files()[0])

# Obtener todos los días
all_days = ScrobblesAnalyzer.get_all_days_for_track(
    scrobbles,
    artist="Mori",
    track="Lovers to Strangers"
)

if all_days:
    display_all_days_for_track(all_days, "Mori", "Lovers to Strangers")
    
    # Salida:
    # #  Fecha        Escuchas  % del total  Barra
    # 1  17 Nov 2025    64        33.0%       ████████████...
    # 2  28 Nov 2025    38        19.6%       ███████...
    # 3  18 Nov 2025    18         9.3%       ███...
    # ...
```

---

### Ejemplo 3: Analizar la canción más escuchada

```python
from load_scrobbles import (
    ScrobblesLoader,
    ScrobblesAnalyzer,
    display_peak_day_for_track,
    display_all_days_for_track
)

# Cargar y obtener top track
loader = ScrobblesLoader('data')
scrobbles = loader.load_file(loader.list_files()[0])

top_tracks = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=1)
(artist, track), _ = top_tracks[0]

# Calcular pico
peak = ScrobblesAnalyzer.get_peak_day_for_track(scrobbles, artist, track)
display_peak_day_for_track(peak)

# Mostrar historial
all_days = ScrobblesAnalyzer.get_all_days_for_track(scrobbles, artist, track)
display_all_days_for_track(all_days, artist, track)
```

---

## Información Técnica

- **Parseo de fechas:** Formato Last.fm `"DD Mon YYYY, HH:MM"` en UTC+0
- **Conversión de zona horaria:** Usa `datetime.timezone` y `zoneinfo.ZoneInfo`
- **Agrupamiento:** Por fecha local (00:00 a 23:59 zona horaria del equipo)
- **Ordenamiento:** Por cantidad de escuchas descendente

---

## Archivos

- **Módulo:** `src/load_scrobbles.py`
  - Clase: `ScrobblesAnalyzer`
  - Función: `get_peak_day_for_track()`
  - Función: `get_all_days_for_track()`
  - Función: `display_peak_day_for_track()`
  - Función: `display_all_days_for_track()`

- **Pruebas:** `src/test_peak_day.py`
  - Tests 1-3 que demuestran el uso completo
  - Ejecución: `python src/test_peak_day.py`
