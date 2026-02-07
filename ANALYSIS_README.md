# Funciones de Análisis de Scrobbles

Se han agregado tres funciones principales de análisis al módulo `load_scrobbles.py`:

## API de Análisis

### `ScrobblesAnalyzer.get_top_artists(scrobbles, n=10, from_date=None, to_date=None)`
Calcula los **n artistas más escuchados**.

**Parámetros:**
- `scrobbles`: Lista de objetos Scrobble
- `n`: Número de artistas a retornar (default: 10)
- `from_date`: Fecha inicial en formato `"DD Mon YYYY, HH:MM"` (opcional)
- `to_date`: Fecha final en formato `"DD Mon YYYY, HH:MM"` (opcional)

**Retorna:** `List[Tuple[str, int]]` - Lista de (artista, cantidad de escuchas)

---

### `ScrobblesAnalyzer.get_top_albums(scrobbles, n=10, from_date=None, to_date=None)`
Calcula los **n álbumes más escuchados**.

**Parámetros:** Iguales a `get_top_artists`

**Retorna:** `List[Tuple[Tuple[str, str], int]]` - Lista de ((artista, álbum), cantidad)

---

### `ScrobblesAnalyzer.get_top_tracks(scrobbles, n=10, from_date=None, to_date=None)`
Calcula las **n canciones más escuchadas**.

**Parámetros:** Iguales a `get_top_artists`

**Retorna:** `List[Tuple[Tuple[str, str], int]]` - Lista de ((artista, canción), cantidad)

---

## Funciones de Visualización

```python
display_top_artists(results, scrobbles_count)
display_top_albums(results, scrobbles_count)
display_top_tracks(results, scrobbles_count)
```

Estas funciones muestran los resultados en formato tabla con escuchas y porcentajes.

---

## Ejemplo Completo

```python
from load_scrobbles import ScrobblesLoader, ScrobblesAnalyzer, display_top_artists

# 1. Cargar scrobbles
loader = ScrobblesLoader('data')
scrobbles = loader.load_file(loader.list_files()[0])

# 2. Análisis SIN filtro (todo el período)
top_artists = ScrobblesAnalyzer.get_top_artists(scrobbles, n=20)
display_top_artists(top_artists, len(scrobbles))

# 3. Análisis CON filtro de fechas
top_tracks_week = ScrobblesAnalyzer.get_top_tracks(
    scrobbles, 
    n=10,
    from_date="29 Jan 2026, 00:00",
    to_date="05 Feb 2026, 23:59"
)
display_top_tracks(top_tracks_week, count_filtered)
```

---

## Formato de Fechas

Todas las fechas deben estar en formato: **`"DD Mon YYYY, HH:MM"`**

Ejemplos:
- `"05 Feb 2026, 13:57"` ✓
- `"01 Jan 2024, 00:00"` ✓
- `"31 Dec 2025, 23:59"` ✓

Meses: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec

---

## Opciones por Defecto

Si **no especificas fechas**, se analizan **todos los scrobbles** (período completo).

```python
# Análisis de TODO el histórico
top_artists = ScrobblesAnalyzer.get_top_artists(scrobbles, n=50)  # Sin from_date/to_date
```

---

## Archivos Incluidos

1. **`load_scrobbles.py`** - Módulo principal con:
   - Clase `Scrobble`
   - Clase `ScrobblesLoader`
   - Clase `ScrobblesAnalyzer` ← **NUEVO**
   - Funciones de visualización

2. **`analysis_example.py`** - Script de ejemplo que demuestra:
   - Análisis del período completo
   - Análisis de últimos 7 días
   - Top 20 artistas

3. **`ANALYSIS_GUIDE.py`** - Guía interactiva con documentación completa

---

## Campos Disponibles para Análisis

Cada scrobble tiene los siguientes campos:
- `artist` - Nombre del artista
- `album` - Nombre del álbum
- `track` - Nombre de la canción
- `utc_time` - Fecha y hora en formato "DD Mon YYYY, HH:MM"
- `uts` - Timestamp Unix
- Y más: `streamable`, `url`, `images`, etc.

