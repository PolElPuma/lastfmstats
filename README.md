# Last.fm Stats Analyzer

Una aplicación Python para analizar tu historial de scrobbles en Last.fm con visualización interactiva en HTML, incluyendo calendario visual, estadísticas detalladas y análisis de rachas.

## 🎯 Características

- **Carga de scrobbles**: Importa archivos JSON con tu historial de Last.fm
- **Análisis estadístico completo**:
  - Top canciones, artistas y álbumes
  - Días con mayor actividad
  - Canciones con mayor pico de escuchas en un día
  - Rachas de días consecutivos (para canciones, artistas y álbumes)
- **Calendario visual interactivo**: 
  - Visualiza por cada día cuál fue la canción más escuchada
  - Ver información detallada al hacer clic en cada día
  - Selector de años para análisis separado por año
  - Gráfico circular de escuchas por hora
- **Análisis por años**: Separa automáticamente las estadísticas por año
- **Interfaz amigable**: Aplicación CLI con opciones interactivas

## 📋 Requisitos

- Python 3.9+
- No requiere dependencias externas (usa solo librerías estándar de Python)

## 🚀 Instalación y Uso

### 1. Preparar datos

Descarga tu historial de scrobbles desde Last.fm en formato JSON. Coloca los archivos en la carpeta `data/`:

```bash
ls data/
# Esperado: scrobbles-USERNAME-TIMESTAMP.json
```

### 2. Ejecutar la aplicación

```bash
python3 src/main.py
```

La aplicación te presentará un menú interactivo:

1. **Cargar archivo de scrobbles** - Selecciona el archivo JSON a analizar
2. **Ver resumen de estadísticas** - Muestra top 20 canciones, artistas, álbumes, etc.
3. **Buscar día pico de una canción** - Encuentra qué día escuchaste más una canción
4. **Ver todos los días de una canción** - Historial completo de escuchas de una canción
5. **Ver top días (escuchas globales)** - Días con más actividad general
6. **Generar calendario visual HTML** - Crea un archivo HTML interactivo
7. **Salir**

### 3. Generar calendario interactivo

La opción 6 genera un archivo `calendar.html` que puedes abrir en tu navegador:

```bash
python3 src/main.py
# Selecciona opción 6
# Se generará calendar.html
```

Luego abre `calendar.html` en tu navegador favorito.

## 📊 Estructura del Calendario HTML

El calendario generado incluye:

### Selector de Años
Sitúado en la parte superior, permite cambiar entre años y actualizar todas las estadísticas automáticamente.

### Resumen de Estadísticas
- **🔝 Top Canciones** - Las más escuchadas del período
- **🎤 Top Artistas** - Artistas con más reproducciones
- **💿 Top Álbumes** - Álbumes más escuchados
- **🔥 Top Días** - Días con más escuchas y canción principal de cada día
- **⭐ Picos de Escuchas** - Canciones con mayor cantidad de escuchas en un único día
- **🎵 Rachas de Canciones** - Canciones escuchadas en más días consecutivos
- **🎤 Rachas de Artistas** - Artistas escuchados en más días consecutivos
- **💿 Rachas de Álbumes** - Álbumes escuchados en más días consecutivos

### Gráfico Horario
Visualización circular mostrando en qué horas del día escuchas más música. Pasa el ratón sobre el gráfico para ver detalles de cada hora.

### Calendario Interactivo
Grid de tarjetas mostrando:
- **Imagen del álbum** (o icono de búsqueda de Google)
- **Artista y canción** más escuchados ese día
- **Número de escuchas** totales ese día
- **Interactividad**: haz clic en cualquier tarjeta para ver más detalles en un modal

### Modal de Detalles
Al hacer clic en un día, se muestra:
- Imagen del álbum
- Artista y canción
- Número de escuchas ese día
- Enlace a Last.fm para más información

## 📈 Análisis Detallado de Funcionalidades

### Top Tracks/Artists/Albums
Calcula las N canciones, artistas o álbumes con más escuchas en el período seleccionado.

### Peak Plays
Identifica canciones que tuvieron su mayor cantidad de escuchas concentradas en un solo día.

### Consecutive Days (Rachas)
Encuentra las más largas secuencias de días consecutivos en los que escuchaste:
- Una canción específica
- Un artista específico  
- Un álbum específico

Perfecta para identificar obsesiones temporales.

### Hourly Distribution
Agrupa todas las escuchas por hora del día (0-23), mostrando:
- Total de escuchas por hora
- Artista y canción top de cada hora
- Distribución visual en gráfico circular

## 🧪 Tests

Ejecutar la suite de tests:

```bash
python3 -m pytest test/test_analyzer.py -v
```

Tests incluyen:
- Validación de agregación de datos
- Pruebas con datos vacíos y casos límite
- Pruebas de caracteres especiales en datos
- Validación de generación de HTML
- Pruebas de carga de archivos

## 📁 Estructura del Proyecto

```
lastfmstats/
├── src/
│   ├── main.py                 # Punto de entrada, interfaz CLI
│   └── load_scrobbles.py       # Core: classes Scrobble, ScrobblesLoader, ScrobblesAnalyzer
├── test/
│   └── test_analyzer.py        # Suite de tests (16 pruebas)
├── data/
│   └── scrobbles-*.json        # Archivos de datos (no incluidos en repo)
├── calendar.html               # Generado por la aplicación
└── README.md                   # Este archivo
```

## 🔧 Clases Principal

### `Scrobble`
Representa un scrobble individual (reproducción de una canción).

**Atributos**:
- `uts`: Unix timestamp
- `utc_time`: Hora en formato legible
- `artist`: Nombre del artista
- `track`: Nombre de la canción
- `album`: Nombre del álbum
- `images`: URLs de imágenes del álbum por tamaño
- `url`: Enlace a Last.fm

### `ScrobblesLoader`
Carga y parsea archivos JSON de Last.fm.

**Métodos principales**:
- `load_file(filepath)`: Carga un archivo de scrobbles
- `interactive_load()`: Interfaz interactiva para seleccionar archivo
- `list_files()`: Lista archivos disponibles

### `ScrobblesAnalyzer`
Análisis estadístico completo del historial.

**Métodos principales**:
- `get_top_tracks(scrobbles, n)`: Top N canciones
- `get_top_artists(scrobbles, n)`: Top N artistas
- `get_top_albums(scrobbles, n)`: Top N álbumes
- `get_top_days_overall(scrobbles, n)`: Top N días por escuchas
- `get_peak_day_for_track()`: Día pico de una canción
- `get_all_days_for_track()`: Historial completo de una canción
- `get_top_tracks_by_peak_plays()`: Canciones con mayor pico en un día
- `get_top_tracks_by_consecutive_days()`: Rachas más largas por canción
- `get_top_artists_by_consecutive_days()`: Rachas más largas por artista
- `get_top_albums_by_consecutive_days()`: Rachas más largas por álbum
- `get_hourly_top()`: Distribución por hora
- `get_most_played_track_per_day()`: Canción top cada día
- `generate_calendar_html()`: Genera HTML interactivo

## 🎨 Personalización del HTML

El archivo `calendar.html` es completamente funcional sin necesidad de un servidor externo. Incluye:

- Estilos CSS modernos con gradientes y animaciones
- JavaScript puro (sin librerías externas)
- Selector de años dinámico
- Modal interactivo con animaciones
- Gráfico circular renderizado en Canvas
- Responsivo y funcional en todos los navegadores

Para personalizar colores o estilos, edita la sección `<style>` en la salida HTML.

## 📝 Formato de Datos

Los archivos JSON de Last.fm esperados tienen la estructura:

```json
[
  {
    "date": {
      "uts": "1609459200",
      "#text": "01 Jan 2021, 12:00"
    },
    "artist": {
      "#text": "Artist Name",
      "mbid": "..."
    },
    "album": {
      "#text": "Album Name",
      "mbid": "..."
    },
    "name": "Track Name",
    "mbid": "...",
    "url": "https://www.last.fm/...",
    "image": [...]
  }
]
```

## 🐛 Solución de Problemas

### "No se encontraron archivos de scrobbles"
Asegúrate de:
1. Tener archivos JSON en la carpeta `data/`
2. Que los archivos cumplan con el formato esperado de Last.fm
3. Que los nombres comiencen con `scrobbles-`

### "Error al renderizar el calendario"
1. Verifica que tu navegador soporte Canvas (necesario para el gráfico horario)
2. Si hay errores de JavaScript, abre la consola del navegador (F12) para ver detalles
3. Asegúrate de que las imágenes de Last.fm sean accesibles

### Los datos no aparecen en el HTML
1. Verifica que se cargaron correctamente los scrobbles (chequea el terminal)
2. Intenta regenerar el calendar.html
3. Limpia el caché del navegador (Ctrl+Shift+Delete)

## 📄 Licencia

Proyecto de análisis personal de Last.fm.

## 👤 Autor

Desarrollado como herramienta de análisis estadístico de historial musical.

---

**Versión**: 1.0
**Última actualización**: Febrero 2026
