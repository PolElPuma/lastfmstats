import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import glob
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo
import time


class Scrobble:
    """Representa un scrobble (escucha a una canción)"""
    
    def __init__(self, data: Dict[str, Any]):
        """
        Inicializa un scrobble desde los datos de Last.fm
        
        Args:
            data: Diccionario con los datos del scrobble
        """
        # Campos de fecha
        self.uts = data.get('date', {}).get('uts', '')
        self.utc_time = data.get('date', {}).get('#text', '')

        # Campos de artista
        self.artist = data.get('artist', {}).get('#text', '')
        self.artist_mbid = data.get('artist', {}).get('mbid', '')

        # Campos de álbum
        self.album = data.get('album', {}).get('#text', '')
        self.album_mbid = data.get('album', {}).get('mbid', '')

        # Campos de canción
        self.track = data.get('name', '')
        self.track_mbid = data.get('mbid', '')
        
        # Campos adicionales
        self.streamable = data.get('streamable', '')
        self.url = data.get('url', '')
        
        # Imágenes (extrae las URLs según tamaño)
        self.images = self._extract_images(data.get('image', []))
    
    def _extract_images(self, images: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Extrae las URLs de imágenes por tamaño
        
        Args:
            images: Lista de diccionarios de imagen
            
        Returns:
            Diccionario con size como clave y URL como valor
        """
        image_dict = {}
        if isinstance(images, list):
            for img in images:
                if isinstance(img, dict):
                    size = img.get('size', 'unknown')
                    url = img.get('#text', '')
                    image_dict[size] = url
        return image_dict
    
    def __repr__(self) -> str:
        return (f"Scrobble(uts={self.uts}, artist='{self.artist}', "
                f"track='{self.track}', album='{self.album}')")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el scrobble a diccionario"""
        return {
            'uts': self.uts,
            'utc_time': self.utc_time,
            'artist': self.artist,
            'artist_mbid': self.artist_mbid,
            'album': self.album,
            'album_mbid': self.album_mbid,
            'track': self.track,
            'track_mbid': self.track_mbid,
            'streamable': self.streamable,
            'url': self.url,
            'images': self.images
        }


class ScrobblesLoader:
    """Cargador de archivos de scrobbles"""
    
    def __init__(self, data_dir: str = 'data'):
        """
        Inicializa el cargador
        
        Args:
            data_dir: Directorio donde se encuentran los archivos JSON
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Directorio {data_dir} no encontrado")
    
    def list_files(self) -> List[str]:
        """
        Lista los archivos de scrobbles disponibles
        
        Returns:
            Lista de nombres de archivo con ruta
        """
        pattern = str(self.data_dir / "scrobbles-*.json")
        files = glob.glob(pattern)
        return sorted(files)
    
    def show_available_files(self) -> None:
        """Muestra los archivos disponibles"""
        files = self.list_files()
        if not files:
            print("No se encontraron archivos de scrobbles en la carpeta 'data'")
            return
        
        print("\n" + "="*60)
        print("Archivos de Scrobbles Disponibles:")
        print("="*60)
        for i, file in enumerate(files, 1):
            filename = Path(file).name
            size_mb = Path(file).stat().st_size / (1024 * 1024)
            print(f"{i}. {filename} ({size_mb:.2f} MB)")
        print("="*60 + "\n")
    
    def load_file(self, filepath: str) -> List[Scrobble]:
        """
        Carga un archivo JSON de scrobbles
        
        Args:
            filepath: Ruta del archivo a cargar
            
        Returns:
            Lista de objetos Scrobble
        """
        print(f"\nCargando archivo: {Path(filepath).name}...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON: {e}")
            return []
        
        # Extraer los scrobbles del formato de Last.fm
        # Pueden ser varias estructuras diferentes
        scrobbles = []
        
        if isinstance(data, list):
            # Verificar si es un array de arrays (batches) o array directo
            if data and isinstance(data[0], list):
                # Es un array de arrays, procesar cada array
                for batch in data:
                    if isinstance(batch, list):
                        for track_data in batch:
                            if isinstance(track_data, dict):
                                try:
                                    scrobble = Scrobble(track_data)
                                    scrobbles.append(scrobble)
                                except:
                                    continue
            else:
                # Es un array directo de tracks
                for track_data in data:
                    if isinstance(track_data, dict):
                        try:
                            scrobble = Scrobble(track_data)
                            scrobbles.append(scrobble)
                        except:
                            continue
        elif isinstance(data, dict):
            # Es un objeto, intentar diferentes estructuras
            if 'recenttracks' in data and isinstance(data['recenttracks'], dict):
                tracks = data['recenttracks'].get('track', [])
                if not isinstance(tracks, list):
                    tracks = [tracks]
            elif 'track' in data:
                tracks = data['track']
                if not isinstance(tracks, list):
                    tracks = [tracks]
            else:
                tracks = []
            
            for track_data in tracks:
                if isinstance(track_data, dict):
                    try:
                        scrobble = Scrobble(track_data)
                        scrobbles.append(scrobble)
                    except:
                        continue
        
        print(f"✓ Se cargaron {len(scrobbles)} scrobbles correctamente")
        return scrobbles
    
    def interactive_load(self) -> List[Scrobble]:
        """
        Interfaz interactiva para seleccionar y cargar archivo
        
        Returns:
            Lista de objetos Scrobble del archivo seleccionado
        """
        self.show_available_files()
        
        files = self.list_files()
        if not files:
            return []
        
        # Si solo hay un archivo, cargarlo automáticamente
        if len(files) == 1:
            print(f"Cargando automáticamente: {Path(files[0]).name}")
            return self.load_file(files[0])
        
        # Si hay múltiples archivos, permitir seleccionar
        while True:
            try:
                choice = input("Selecciona el número del archivo a cargar (o 'q' para salir): ").strip()
                
                if choice.lower() == 'q':
                    print("Operación cancelada")
                    return []
                
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    return self.load_file(files[idx])
                else:
                    print(f"Opción inválida. Por favor, selecciona entre 1 y {len(files)}")
            except ValueError:
                print("Por favor, ingresa un número válido")


class ScrobblesAnalyzer:
    """Analizador de estadísticas de scrobbles"""
    # Nota: la lógica de búsqueda/descarga de imágenes fue removida.

    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """
        Convierte una cadena de fecha de Last.fm al formato datetime
        
        Args:
            date_str: Cadena de fecha en formato "DD Mon YYYY, HH:MM"
            
        Returns:
            Objeto datetime o None si no se puede parsear
        """
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d %b %Y, %H:%M")
        except ValueError:
            return None
    
    @staticmethod
    def _filter_scrobbles_by_date(
        scrobbles: List[Scrobble],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Scrobble]:
        """
        Filtra scrobbles por rango de fechas
        
        Args:
            scrobbles: Lista de scrobbles a filtrar
            from_date: Fecha inicial en formato "DD Mon YYYY, HH:MM" (inclusive)
            to_date: Fecha final en formato "DD Mon YYYY, HH:MM" (inclusive)
            
        Returns:
            Lista de scrobbles filtrados
        """
        if not from_date and not to_date:
            return scrobbles
        
        filtered = []
        from_dt = ScrobblesAnalyzer._parse_date(from_date) if from_date else None
        to_dt = ScrobblesAnalyzer._parse_date(to_date) if to_date else None
        
        for scrobble in scrobbles:
            scrobble_dt = ScrobblesAnalyzer._parse_date(scrobble.utc_time)
            if not scrobble_dt:
                continue
            
            if from_dt and scrobble_dt < from_dt:
                continue
            if to_dt and scrobble_dt > to_dt:
                continue
            
            filtered.append(scrobble)
        
        return filtered
    
    @staticmethod
    def get_top_artists(
        scrobbles: List[Scrobble],
        n: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Tuple[str, int]]:
        """
        Obtiene los n artistas más escuchados
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de artistas a retornar
            from_date: Fecha inicial (opcional)
            to_date: Fecha final (opcional)
            
        Returns:
            Lista de tuplas (artista, cantidad) ordenadas por cantidad descendente
        """
        filtered = ScrobblesAnalyzer._filter_scrobbles_by_date(scrobbles, from_date, to_date)
        artists = [s.artist for s in filtered if s.artist]
        counter = Counter(artists)
        return counter.most_common(n)
    
    @staticmethod
    def get_top_albums(
        scrobbles: List[Scrobble],
        n: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Tuple[Tuple[str, str], int]]:
        """
        Obtiene los n álbumes más escuchados
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de álbumes a retornar
            from_date: Fecha inicial (opcional)
            to_date: Fecha final (opcional)
            
        Returns:
            Lista de tuplas ((artista, álbum), cantidad) ordenadas por cantidad descendente
        """
        filtered = ScrobblesAnalyzer._filter_scrobbles_by_date(scrobbles, from_date, to_date)
        albums = [(s.artist, s.album) for s in filtered if s.album]
        counter = Counter(albums)
        return counter.most_common(n)
    
    @staticmethod
    def get_top_tracks(
        scrobbles: List[Scrobble],
        n: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Tuple[Tuple[str, str], int]]:
        """
        Obtiene las n canciones más escuchadas
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de canciones a retornar
            from_date: Fecha inicial (opcional)
            to_date: Fecha final (opcional)
            
        Returns:
            Lista de tuplas ((artista, canción), cantidad) ordenadas por cantidad descendente
        """
        filtered = ScrobblesAnalyzer._filter_scrobbles_by_date(scrobbles, from_date, to_date)
        tracks = [(s.artist, s.track) for s in filtered if s.track]
        counter = Counter(tracks)
        return counter.most_common(n)
    
    @staticmethod
    def _utc_to_local(utc_time_str: str) -> Optional[datetime]:
        """
        Convierte una cadena de fecha UTC (formato Last.fm) a datetime local del equipo
        
        Args:
            utc_time_str: Cadena de fecha en formato "DD Mon YYYY, HH:MM" (UTC+0)
            
        Returns:
            Objeto datetime en la zona horaria local, o None si no se puede parsear
        """
        if not utc_time_str:
            return None
        
        try:
            # Parsear la fecha en UTC
            dt_utc = datetime.strptime(utc_time_str, "%d %b %Y, %H:%M").replace(tzinfo=timezone.utc)
            
            # Convertir a zona horaria local del sistema
            local_tz = ZoneInfo("UTC")  # Por defecto, obtener la zona local
            try:
                import time
                if time.daylight:
                    local_tz = ZoneInfo("UTC")
                # Intentar usar la zona horaria del sistema
                from datetime import datetime as dt_now
                local_now = dt_now.now(tz=None)
                if hasattr(local_now, 'astimezone'):
                    local_tz = local_now.astimezone().tzinfo
            except:
                pass
            
            # Mejor: usar una aproximación más simple - obtener UTC offset del sistema
            offset = datetime.now(timezone.utc).astimezone().utcoffset()
            if offset is not None:
                local_tz = timezone(offset)
            
            dt_local = dt_utc.astimezone(local_tz)
            return dt_local
            
        except (ValueError, Exception):
            return None
    
    @staticmethod
    def get_peak_day_for_track(
        scrobbles: List[Scrobble],
        artist: str,
        track: str
    ) -> Optional[Tuple[str, int, int]]:
        """
        Calcula el día en el que más se escuchó una canción (en la zona horaria local)
        
        Args:
            scrobbles: Lista de scrobbles
            artist: Nombre del artista
            track: Nombre de la canción
            
        Returns:
            Tupla (fecha_formateada, cantidad_escuchas, total_escuchas) o None si no se encuentra
            La fecha está en formato "DD Mon YYYY" en zona horaria local
        """
        # Filtrar scrobbles de la canción específica
        track_scrobbles = [
            s for s in scrobbles 
            if s.artist == artist and s.track == track
        ]
        
        if not track_scrobbles:
            return None
        
        # Agrupar por día (en zona horaria local)
        day_counts = Counter()
        day_datetimes = {}  # Para guardar referencia a datetime de cada día
        
        for scrobble in track_scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt:
                # Usar la fecha del día (sin hora)
                day_key = local_dt.strftime("%d %b %Y")
                day_counts[day_key] += 1
                day_datetimes[day_key] = local_dt
        
        if not day_counts:
            return None
        
        # Obtener el día con más escuchas
        peak_day, count = day_counts.most_common(1)[0]
        
        return (peak_day, count, len(track_scrobbles))
    
    @staticmethod
    def get_all_days_for_track(
        scrobbles: List[Scrobble],
        artist: str,
        track: str
    ) -> Optional[List[Tuple[str, int]]]:
        """
        Obtiene todos los días en que se escuchó una canción con sus conteos
        
        Args:
            scrobbles: Lista de scrobbles
            artist: Nombre del artista
            track: Nombre de la canción
            
        Returns:
            Lista de tuplas (fecha, cantidad) ordenadas por cantidad descendente
        """
        # Filtrar scrobbles de la canción específica
        track_scrobbles = [
            s for s in scrobbles 
            if s.artist == artist and s.track == track
        ]
        
        if not track_scrobbles:
            return None
        
        # Agrupar por día (en zona horaria local)
        day_counts = Counter()
        
        for scrobble in track_scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt:
                day_key = local_dt.strftime("%d %b %Y")
                day_counts[day_key] += 1
        
        if not day_counts:
            return None
        
        # Retornar ordenado por cantidad descendente
        return day_counts.most_common()
    
    @staticmethod
    def get_top_days_overall(
        scrobbles: List[Scrobble],
        n: int = 10
    ) -> Optional[List[Tuple[str, int]]]:
        """
        Obtiene los n días con más escuchas en total (globales)
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de días top a retornar (default: 10)
            
        Returns:
            Lista de tuplas (fecha, cantidad_escuchas) ordenadas por cantidad descendente
        """
        if not scrobbles:
            return None
        
        # Agrupar todos los scrobbles por día (en zona horaria local)
        day_counts = Counter()
        
        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt:
                day_key = local_dt.strftime("%d %b %Y")
                day_counts[day_key] += 1
        
        if not day_counts:
            return None
        
        # Retornar los top n días ordenados por cantidad descendente
        return day_counts.most_common(n)
    
    @staticmethod
    def get_top_days_overall_by_artist_count(
        scrobbles: List[Scrobble],
        n: int = 10
    ) -> Optional[List[Tuple[str, int]]]:
        """
        Obtiene los n días con más artistas diferentes escuchados
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de días top a retornar (default: 10)
            
        Returns:
            Lista de tuplas (fecha, cantidad_artistas_unicos) ordenadas por cantidad descendente
        """
        if not scrobbles:
            return None
        
        # Agrupar artistas únicos por día
        day_artists = defaultdict(set)
        
        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt and scrobble.artist:
                day_key = local_dt.strftime("%d %b %Y")
                day_artists[day_key].add(scrobble.artist)
        
        if not day_artists:
            return None
        
        # Convertir sets a counts
        day_artist_counts = [(day, len(artists)) for day, artists in day_artists.items()]
        day_artist_counts.sort(key=lambda x: x[1], reverse=True)
        
        return day_artist_counts[:n]
    
    @staticmethod
    def get_top_days_overall_by_track_count(
        scrobbles: List[Scrobble],
        n: int = 10
    ) -> Optional[List[Tuple[str, int]]]:
        """
        Obtiene los n días con more canciones diferentes escuchadas
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de días top a retornar (default: 10)
            
        Returns:
            Lista de tuplas (fecha, cantidad_canciones_unicas) ordenadas por cantidad descendente
        """
        if not scrobbles:
            return None
        
        # Agrupar canciones únicas por día
        day_tracks = defaultdict(set)
        
        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt and scrobble.track:
                day_key = local_dt.strftime("%d %b %Y")
                # Usar (artist, track) como clave única
                track_key = (scrobble.artist, scrobble.track)
                day_tracks[day_key].add(track_key)
        
        if not day_tracks:
            return None
        
        # Convertir sets a counts
        day_track_counts = [(day, len(tracks)) for day, tracks in day_tracks.items()]
        day_track_counts.sort(key=lambda x: x[1], reverse=True)
        
        return day_track_counts[:n]
    
    @staticmethod
    def get_most_played_track_per_day(
        scrobbles: List[Scrobble]
    ) -> Optional[Dict[str, Tuple[str, str, str, str, int]]]:
        """
        Obtiene el track más escuchado por cada día
        
        Args:
            scrobbles: Lista de scrobbles
            
        Returns:
            Diccionario {fecha: (artista, track, imagen_url, url_track, escuchas)}
            O None si no hay datos
        """
        if not scrobbles:
            return None
        
        # Agrupar scrobbles por día y contar tracks
        day_tracks = defaultdict(Counter)
        
        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt:
                day_key = local_dt.strftime("%d %b %Y")
                track_key = (scrobble.artist, scrobble.track)
                day_tracks[day_key][track_key] += 1
        
        if not day_tracks:
            return None
        
        # Para cada día, obtener el track más escuchado
        result = {}
        
        for day, track_counts in day_tracks.items():
            if track_counts:
                (artist, track), count = track_counts.most_common(1)[0]
                
                # Buscar el scrobble para obtener metadatos
                day_scrobbles = [
                    s for s in scrobbles
                    if s.artist == artist and s.track == track
                ]
                
                if day_scrobbles:
                    scrobble = day_scrobbles[0]
                    # Obtener imagen (preferir extralarge)
                    image_url = scrobble.images.get('extralarge', '')
                    if not image_url:
                        image_url = scrobble.images.get('large', '')
                    if not image_url:
                        image_url = scrobble.images.get('medium', '')
                    # Si no hay imagen en Last.fm, dejar en blanco (sin búsqueda externa)
                    if not image_url:
                        image_url = ''
                    
                    result[day] = (artist, track, image_url, scrobble.url, count)
        
        return result if result else None
    
    @staticmethod
    def get_top_tracks_by_peak_plays(
        scrobbles: List[Scrobble],
        n: int = 5
    ) -> Optional[List[Tuple[Tuple[str, str], int, str]]]:
        """
        Obtiene las N canciones con el mayor número de escuchas en un solo día (su día pico)
        
        Args:
            scrobbles: Lista de scrobbles
            n: Número de canciones a retornar (default: 5)
            
        Returns:
            Lista de tuplas ((artist, track), peak_plays, peak_day)
            Ordenadas por peak_plays descendente, o None si no hay datos
        """
        if not scrobbles:
            return None
        
        # Diccionario: track_key -> {day -> count}
        track_day_counts: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            
            if local_dt:
                day_key = local_dt.strftime("%d %b %Y")
                track_key = (scrobble.artist, scrobble.track)
                track_day_counts[track_key][day_key] += 1
        
        if not track_day_counts:
            return None
        
        # Para cada canción, obtener el día pico y sus escuchas
        result: List[Tuple[Tuple[str, str], int, str]] = []
        
        for (artist, track), day_counts in track_day_counts.items():
            if day_counts:
                peak_day = max(day_counts.items(), key=lambda x: x[1])
                day, plays = peak_day
                result.append(((artist, track), plays, day))
        
        # Ordenar por plays descendente
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result[:n] if result else None

    @staticmethod
    def get_top_tracks_by_consecutive_days(
        scrobbles: List[Scrobble],
        n: int = 5
    ) -> Optional[List[Tuple[Tuple[str, str], int, str, str]]]:
        """
        Obtiene las N canciones que se escucharon en más días seguidos (racha más larga).

        Args:
            scrobbles: Lista de scrobbles
            n: Número de canciones a retornar (default: 5)

        Returns:
            Lista de tuplas ((artist, track), streak_length, start_day, end_day)
            donde start_day y end_day están en formato "DD Mon YYYY" (zona local).
            Ordenadas por streak_length descendente, o None si no hay datos.
        """
        if not scrobbles:
            return None

        # Para cada canción, construir el conjunto de días únicos en los que fue escuchada
        track_days: Dict[Tuple[str, str], set] = defaultdict(set)

        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            if local_dt and scrobble.track and scrobble.artist:
                day = local_dt.date()
                key = (scrobble.artist, scrobble.track)
                track_days[key].add(day)

        if not track_days:
            return None

        results: List[Tuple[Tuple[str, str], int, str, str]] = []

        # Para cada pista, calcular la racha máxima de días consecutivos
        for (artist, track), days_set in track_days.items():
            if not days_set:
                continue

            # Ordenar días
            days_sorted = sorted(days_set)

            max_streak = 0
            max_start = None
            max_end = None

            cur_streak = 0
            cur_start = None
            prev_day = None

            for d in days_sorted:
                if prev_day is None:
                    cur_streak = 1
                    cur_start = d
                else:
                    if (d - prev_day).days == 1:
                        cur_streak += 1
                    else:
                        # racha interrumpida
                        if cur_streak > max_streak:
                            max_streak = cur_streak
                            max_start = cur_start
                            max_end = prev_day
                        cur_streak = 1
                        cur_start = d

                prev_day = d

            # Chequear la última racha
            if cur_streak > max_streak:
                max_streak = cur_streak
                max_start = cur_start
                max_end = prev_day

            if max_streak > 0 and max_start and max_end:
                start_str = max_start.strftime("%d %b %Y")
                end_str = max_end.strftime("%d %b %Y")
                results.append(((artist, track), max_streak, start_str, end_str))

        # Ordenar por longitud de racha descendente
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:n] if results else None

    @staticmethod
    def get_top_artists_by_consecutive_days(
        scrobbles: List[Scrobble],
        n: int = 5
    ) -> Optional[List[Tuple[str, int, str, str]]]:
        """
        Obtiene las N artistas que se escucharon en más días seguidos (racha más larga).

        Args:
            scrobbles: Lista de scrobbles
            n: Número de artistas a retornar (default: 5)

        Returns:
            Lista de tuplas (artist, streak_length, start_day, end_day)
            donde start_day y end_day están en formato "DD Mon YYYY" (zona local).
        """
        if not scrobbles:
            return None

        artist_days: Dict[str, set] = defaultdict(set)

        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            if local_dt and scrobble.artist:
                day = local_dt.date()
                artist_days[scrobble.artist].add(day)

        if not artist_days:
            return None

        results: List[Tuple[str, int, str, str]] = []

        for artist, days_set in artist_days.items():
            if not days_set:
                continue

            days_sorted = sorted(days_set)

            max_streak = 0
            max_start = None
            max_end = None

            cur_streak = 0
            cur_start = None
            prev_day = None

            for d in days_sorted:
                if prev_day is None:
                    cur_streak = 1
                    cur_start = d
                else:
                    if (d - prev_day).days == 1:
                        cur_streak += 1
                    else:
                        if cur_streak > max_streak:
                            max_streak = cur_streak
                            max_start = cur_start
                            max_end = prev_day
                        cur_streak = 1
                        cur_start = d

                prev_day = d

            if cur_streak > max_streak:
                max_streak = cur_streak
                max_start = cur_start
                max_end = prev_day

            if max_streak > 0 and max_start and max_end:
                start_str = max_start.strftime("%d %b %Y")
                end_str = max_end.strftime("%d %b %Y")
                results.append((artist, max_streak, start_str, end_str))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n] if results else None

    @staticmethod
    def get_top_albums_by_consecutive_days(
        scrobbles: List[Scrobble],
        n: int = 5
    ) -> Optional[List[Tuple[Tuple[str, str], int, str, str]]]:
        """
        Obtiene las N parejas (artista, álbum) que se escucharon en más días seguidos.

        Args:
            scrobbles: Lista de scrobbles
            n: Número de álbumes a retornar (default: 5)

        Returns:
            Lista de tuplas ((artist, album), streak_length, start_day, end_day)
        """
        if not scrobbles:
            return None

        album_days: Dict[Tuple[str, str], set] = defaultdict(set)

        for scrobble in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(scrobble.utc_time)
            if local_dt and scrobble.artist and scrobble.album:
                day = local_dt.date()
                key = (scrobble.artist, scrobble.album)
                album_days[key].add(day)

        if not album_days:
            return None

        results: List[Tuple[Tuple[str, str], int, str, str]] = []

        for (artist, album), days_set in album_days.items():
            if not days_set:
                continue

            days_sorted = sorted(days_set)

            max_streak = 0
            max_start = None
            max_end = None

            cur_streak = 0
            cur_start = None
            prev_day = None

            for d in days_sorted:
                if prev_day is None:
                    cur_streak = 1
                    cur_start = d
                else:
                    if (d - prev_day).days == 1:
                        cur_streak += 1
                    else:
                        if cur_streak > max_streak:
                            max_streak = cur_streak
                            max_start = cur_start
                            max_end = prev_day
                        cur_streak = 1
                        cur_start = d

                prev_day = d

            if cur_streak > max_streak:
                max_streak = cur_streak
                max_start = cur_start
                max_end = prev_day

            if max_streak > 0 and max_start and max_end:
                start_str = max_start.strftime("%d %b %Y")
                end_str = max_end.strftime("%d %b %Y")
                results.append(((artist, album), max_streak, start_str, end_str))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n] if results else None

    @staticmethod
    def get_hourly_top(
        scrobbles: List[Scrobble]
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Calcula para cada hora del día (0-23):
          - total de escuchas
          - artista más escuchado (y contador)
          - canción más escuchada (y contador)

        Returns:
            Diccionario con claves '0'..'23' y valores {total, top_artist: (artist, count), top_track: (artist, track, count)}
        """
        if not scrobbles:
            return None

        hour_totals = defaultdict(int)
        hour_artists = defaultdict(Counter)
        hour_tracks = defaultdict(Counter)

        for s in scrobbles:
            local_dt = ScrobblesAnalyzer._utc_to_local(s.utc_time)
            if not local_dt:
                continue
            h = local_dt.hour
            hour_totals[h] += 1
            if s.artist:
                hour_artists[h][s.artist] += 1
            if s.track:
                hour_tracks[h][(s.artist, s.track)] += 1

        result: Dict[str, Dict[str, Any]] = {}
        for h in range(24):
            total = hour_totals.get(h, 0)
            top_artist = None
            top_track = None
            if hour_artists.get(h):
                artist, ac = hour_artists[h].most_common(1)[0]
                top_artist = (artist, ac)
            if hour_tracks.get(h):
                (artist_t, track_t), tc = hour_tracks[h].most_common(1)[0]
                top_track = (artist_t, track_t, tc)

            result[str(h)] = {
                'total': total,
                'top_artist': top_artist or (),
                'top_track': top_track or ()
            }

        return result

    @staticmethod
    # Fin de la clase ScrobblesAnalyzer (lógica de búsqueda/descarga de imágenes eliminada)
    
    @staticmethod
    def generate_calendar_html(
        scrobbles: List[Scrobble],
        output_file: str = "calendar.html",
        summary: Optional[Dict[str, Any]] = None,
        n_items: int = 20,
        n_days: int = 5,
        n_peak_plays: int = 5
    ) -> None:
        """
        Genera un archivo HTML con un calendario visual de las canciones más escuchadas
        
        Args:
            scrobbles: Lista de scrobbles
            output_file: Ruta del archivo HTML de salida
            summary: Diccionario con datos de resumen
            n_items: Número de canciones/artistas/álbumes a mostrar
            n_days: Número de días top a mostrar
            n_peak_plays: Número de canciones con mayor pico a mostrar
        """
        track_per_day = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles)
        
        if not track_per_day:
            print("No hay datos para generar calendario")
            return

        # Usar solo las URLs disponibles en los scrobbles (no hay búsquedas externas)
        
        # Preparar datos serializados para JS
        # Agregar parámetros de configuración al resumen
        summary_with_config = (summary or {}).copy()
        summary_with_config['_config'] = {
            'n_items': n_items,
            'n_days': n_days,
            'n_peak_plays': n_peak_plays
        }
        # Incluir datos por hora si no están en el resumen
        if 'hourly_top' not in summary_with_config:
            summary_with_config['hourly_top'] = ScrobblesAnalyzer.get_hourly_top(scrobbles) or {}
        
        track_json = json.dumps(track_per_day, ensure_ascii=False)
        summary_json = json.dumps(summary_with_config, ensure_ascii=False)

        # Crear HTML
        html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario de Escuchas - Last.fm Stats</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 1.8em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
              font-size: 0.95em;
            opacity: 0.9;
        }
        
        .calendar-grid {
            display: grid;
                grid-template-columns: repeat(auto-fill, minmax(75px, 1fr));
                gap: 8px;
                margin-bottom: 30px;
        }
        
        .day-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .day-card:hover {
            transform: translateY(-4px) scale(1.05);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .day-date {
            position: absolute;
                top: 4px;
                left: 4px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.65em;
            font-weight: bold;
            z-index: 10;
        }
        
        .day-image {
            width: 100%;
                height: 80px;
            object-fit: cover;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .day-image.no-image {
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
                font-size: 0.7em;
            text-align: center;
                padding: 5px;
        }
        
        .day-info {
            padding: 6px;
            background: white;
        }
        
        .day-artist {
            font-weight: bold;
                font-size: 0.75em;
            color: #333;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
                margin-bottom: 2px;
        }
        
        .day-track {
            font-size: 0.7em;
            color: #666;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 4px;
        }
        
        .day-plays {
            font-size: 0.65em;
            color: #999;
            text-align: right;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 400px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            text-align: center;
            animation: slideIn 0.3s;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .modal-image {
            width: 100%;
            max-width: 300px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .modal-date {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 10px;
        }
        
        .modal-artist {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .modal-track {
            font-size: 1.1em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .modal-plays {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 15px;
        }
        
        .modal-link {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            transition: transform 0.2s;
            font-size: 0.9em;
        }
        
        .modal-link:hover {
            transform: scale(1.05);
        }
        
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 2em;
            font-weight: bold;
            color: #999;
            cursor: pointer;
            background: none;
            border: none;
        }
        
        .close:hover {
            color: #333;
        }
        
        .stats {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            color: #666;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .stats p {
            font-size: 1.1em;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Calendario de Escuchas</h1>
            <p>Las canciones más escuchadas cada día</p>
        </div>
        
        <div id="summary-container"></div>
        
        <div id="hourly-chart-container" style="margin:18px 0 28px; display:flex; gap:18px; align-items:center; justify-content:center;">
            <canvas id="hourChart" width="360" height="360" style="width:360px; height:360px; flex:0 0 360px; background:transparent; border-radius:8px;"></canvas>
            <div id="hourInfo" style="color:white; width:420px; font-size:0.95em; flex:0 0 420px;">
                <h3 style="margin-bottom:6px;">🕒 Hora a Hora — Detalle</h3>
                <div id="hourDetail">Pasa el ratón sobre el gráfico para ver el artista y la canción más escuchados en esa hora.</div>
            </div>
        </div>
        <div class="calendar-grid" id="calendar">
        </div>
        
        <div class="stats">
            <p>Total de días: <strong id="totalDays">0</strong></p>
            <p>Total de escuchas: <strong id="totalPlays">0</strong></p>
        </div>
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <button class="close" onclick="closeModal()">&times;</button>
            <img id="modalImage" class="modal-image" src="" alt="Album">
            <div class="modal-date" id="modalDate"></div>
            <div class="modal-artist" id="modalArtist"></div>
            <div class="modal-track" id="modalTrack"></div>
            <div class="modal-plays" id="modalPlays"></div>
            <a id="modalLink" class="modal-link" href="#" target="_blank">Ver en Last.fm</a>
        </div>
    </div>
    
    <script>
        const trackPerDay = """ + track_json + """;
        const summaryData = """ + summary_json + """;
        
        function openModal(date, artist, track, imageUrl, url, plays) {
            document.getElementById('modalDate').textContent = date;
            document.getElementById('modalArtist').textContent = artist;
            document.getElementById('modalTrack').textContent = track;
            document.getElementById('modalPlays').textContent = plays + ' escuchas';
                let modalImg = document.getElementById('modalImage');
                modalImg.src = imageUrl || '';
                if (!imageUrl) {
                    modalImg.alt = 'Sin imagen disponible';
                }
            document.getElementById('modalLink').href = url;
            document.getElementById('modal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('show');
        }
        
        function renderCalendar() {
            let calendar = document.getElementById('calendar');
            let totalDays = 0;
            let totalPlays = 0;
            
            // Convertir string a objeto si es necesario
            let data = """ + track_json + """;
            
            for (let [date, info] of Object.entries(data)) {
                let [artist, track, imageUrl, url, plays] = info;
                totalDays++;
                totalPlays += plays;

                let card = document.createElement('div');
                card.className = 'day-card';

                let googleSearchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(artist + ' ' + track) + '&tbm=isch';

                // Imagen - creación por DOM para evitar errores de quoting en HTML
                let imgWrapper = document.createElement('div');
                if (imageUrl) {
                    let img = document.createElement('img');
                    img.className = 'day-image';
                    img.src = imageUrl;
                    img.alt = track;
                    img.onerror = function() {
                        this.style.display = 'none';
                        let placeholder = document.createElement('div');
                        placeholder.className = 'day-image no-image';
                        placeholder.innerHTML = '🔍 Ver en Google';
                        placeholder.style.cursor = 'pointer';
                        placeholder.onclick = function(){ window.open(googleSearchUrl, '_blank'); };
                        imgWrapper.appendChild(placeholder);
                    };
                    imgWrapper.appendChild(img);
                } else {
                    let placeholder = document.createElement('div');
                    placeholder.className = 'day-image no-image';
                    placeholder.innerHTML = '🔍 Ver en Google';
                    placeholder.style.cursor = 'pointer';
                    placeholder.onclick = function(){ window.open(googleSearchUrl, '_blank'); };
                    imgWrapper.appendChild(placeholder);
                }

                let infoDiv = document.createElement('div');
                infoDiv.className = 'day-info';
                infoDiv.innerHTML = '<div class="day-artist" title="' + artist + '">' + artist + '</div>' +
                                    '<div class="day-track" title="' + track + '">' + track + '</div>' +
                                    '<div class="day-plays">' + plays + ' escuchas</div>';

                let dateDiv = document.createElement('div');
                dateDiv.className = 'day-date';
                dateDiv.textContent = date;

                card.appendChild(dateDiv);
                card.appendChild(imgWrapper);
                card.appendChild(infoDiv);

                card.onclick = () => openModal(date, artist, track, imageUrl, url, plays);
                calendar.appendChild(card);
            }
            
            document.getElementById('totalDays').textContent = totalDays;
            document.getElementById('totalPlays').textContent = totalPlays;
        }
        
        function renderSummary(summary) {
            if (!summary || Object.keys(summary).length === 0) return;
            
            // Obtener parámetros de configuración
            const config = summary._config || {};
            const n_items = config.n_items || 20;
            const n_days = config.n_days || 5;
            const n_peak_plays = config.n_peak_plays || 5;
            
            let html = '<div class="stats" style="margin-bottom:18px; text-align:left;">';
            html += '<h2 style="margin-bottom:12px; text-align:center;">📊 Resumen de Estadísticas</h2>';
            
            // Top tracks
            const tt = summary.top_tracks || [];
            if (tt.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>🔝 Top ' + n_items + ' Canciones:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of tt) {
                    const artist = item[0][0] || '';
                    const track = item[0][1] || '';
                    const plays = item[1] || 0;
                    const peak = (summary.track_peaks || {})[artist + '||' + track] || {};
                    const peakDay = peak.date || '';
                    const peakPlays = peak.count || '';
                    html += '<li>' + artist + ' — ' + track + ' (' + plays + ')';
                    if (peakDay) html += ' — pico: ' + peakDay + ' (' + peakPlays + ')';
                    html += '</li>';
                }
                html += '</ol></div>';
            }
            
            // Top artists
            const ta = summary.top_artists || [];
            if (ta.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>🎤 Top ' + n_items + ' Artistas:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of ta) {
                    html += '<li>' + item[0] + ' (' + item[1] + ' escuchas)</li>';
                }
                html += '</ol></div>';
            }
            
            // Top albums
            const tal = summary.top_albums || [];
            if (tal.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>💿 Top ' + n_items + ' Álbumes:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of tal) {
                    html += '<li>' + item[0][0] + ' — ' + item[0][1] + ' (' + item[1] + ' escuchas)</li>';
                }
                html += '</ol></div>';
            }
            
            // Top days con canción más escuchada
            const td = summary.top_days || [];
            if (td.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>🔥 Top ' + n_days + ' Días con Más Escuchas:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of td) {
                    const day = item[0];
                    const plays = item[1];
                    const m = (summary.top_days_most_played || {})[day] || {};
                    const mArtist = m[0] || '';
                    const mTrack = m[1] || '';
                    const mPlays = m[2] || '';
                    html += '<li>' + day + ' — <strong>' + plays + '</strong> escuchas';
                    if (mTrack) html += ' — "' + mArtist + ' — ' + mTrack + '" (' + mPlays + ')';
                    html += '</li>';
                }
                html += '</ol></div>';
            }
            
            // Top tracks by peak plays
            const ttp = summary.top_tracks_peak_plays || [];
            if (ttp.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>⭐ Top ' + n_peak_plays + ' Canciones con Mayor Pico en un Día:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of ttp) {
                    const artist = item[0][0] || '';
                    const track = item[0][1] || '';
                    const peakPlays = item[1] || 0;
                    const peakDay = item[2] || '';
                    html += '<li>' + artist + ' — ' + track + ' (' + peakPlays + ' escuchas en ' + peakDay + ')</li>';
                }
                html += '</ol></div>';
            }

            // Top tracks by consecutive days (rachas)
            const ttc = summary.top_tracks_consecutive_days || [];
            if (ttc.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>🔥 Top ' + n_days + ' Canciones con Mayor Racha de Días Seguidos:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of ttc) {
                    const artist = item[0][0] || '';
                    const track = item[0][1] || '';
                    const streak = item[1] || 0;
                    const startDay = item[2] || '';
                    const endDay = item[3] || '';
                    html += '<li>' + artist + ' — ' + track + ' (' + streak + ' días) — periodo: ' + startDay + ' → ' + endDay + '</li>';
                }
                html += '</ol></div>';
            }

            // Top artists by consecutive days
            const tta = summary.top_artists_consecutive_days || [];
            if (tta.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>🎤 Top ' + n_days + ' Artistas con Mayor Racha de Días Seguidos:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of tta) {
                    const artist = item[0] || '';
                    const streak = item[1] || 0;
                    const startDay = item[2] || '';
                    const endDay = item[3] || '';
                    html += '<li>' + artist + ' (' + streak + ' días) — periodo: ' + startDay + ' → ' + endDay + '</li>';
                }
                html += '</ol></div>';
            }

            // Top albums by consecutive days
            const tta2 = summary.top_albums_consecutive_days || [];
            if (tta2.length > 0) {
                html += '<div style="margin-bottom:12px;"><strong>💿 Top ' + n_days + ' Álbumes con Mayor Racha de Días Seguidos:</strong><ol style="margin:4px 0 0 20px;">';
                for (let item of tta2) {
                    const artist = item[0][0] || '';
                    const album = item[0][1] || '';
                    const streak = item[1] || 0;
                    const startDay = item[2] || '';
                    const endDay = item[3] || '';
                    html += '<li>' + artist + ' — ' + album + ' (' + streak + ' días) — periodo: ' + startDay + ' → ' + endDay + '</li>';
                }
                html += '</ol></div>';
            }
            
            html += '</div>';
            document.getElementById('summary-container').innerHTML = html;
            // Render hourly chart if available
            const hourly = summary.hourly_top || {};
            try {
                renderHourlyChart(hourly);
            } catch (e) {
                console.warn('No se pudo renderizar gráfico horario:', e);
            }
        }
        
        function renderHourlyChart(hourly) {
            if (!hourly) return;
            const canvas = document.getElementById('hourChart');
            if (!canvas || !canvas.getContext) return;
            const ctx = canvas.getContext('2d');
            const w = canvas.width;
            const h = canvas.height;
            ctx.clearRect(0,0,w,h);

            // Build totals array for 0..23
            const totals = [];
            for (let i=0;i<24;i++) {
                const v = (hourly[String(i)] && hourly[String(i)].total) ? hourly[String(i)].total : 0;
                totals.push(v);
            }
            const sum = totals.reduce((a,b)=>a+b,0);
            if (sum === 0) {
                // Draw empty circle
                ctx.fillStyle = 'rgba(255,255,255,0.06)';
                ctx.beginPath(); ctx.arc(w/2,h/2,100,0,Math.PI*2); ctx.fill();
                return;
            }

            // Draw pie slices
            let start = -Math.PI/2;
            const radius = Math.min(w,h) * 0.38;
            for (let i=0;i<24;i++) {
                const val = totals[i];
                const angle = val / sum * Math.PI*2;
                const end = start + angle;
                // color by hour
                ctx.beginPath();
                ctx.moveTo(w/2,h/2);
                ctx.fillStyle = 'hsl(' + Math.round(i * (360/24)) + ',70%,60%)';
                ctx.arc(w/2,h/2,radius,start,end);
                ctx.closePath();
                ctx.fill();
                start = end;
            }

            // Add interactivity: mousemove shows detail (throttled to hour changes)
            let lastHour = null;
            canvas.onmousemove = function(ev) {
                const rect = canvas.getBoundingClientRect();
                const x = ev.clientX - rect.left - w/2;
                const y = ev.clientY - rect.top - h/2;
                const ang = Math.atan2(y,x);
                let a = ang - (-Math.PI/2);
                if (a < 0) a += Math.PI*2;
                // find hour
                let acc = 0; let hour = 0;
                for (let i=0;i<24;i++){
                    const slice = totals[i]/sum * Math.PI*2;
                    if (a >= acc && a < acc + slice) { hour = i; break; }
                    acc += slice;
                }
                if (hour === lastHour) return; // evitar actualizaciones si no cambia la hora
                lastHour = hour;
                const info = hourly[String(hour)] || {};
                const ta = info.top_artist || [];
                const tt = info.top_track || [];
                const detail = document.getElementById('hourDetail');
                let html = '<strong>Hora: ' + hour + ':00</strong><br/>';
                html += 'Total escuchas: <strong>' + (info.total||0) + '</strong><br/>';
                if (ta.length) html += 'Top artista: <strong>' + ta[0] + '</strong> (' + ta[1] + ')<br/>';
                if (tt.length) html += 'Top canción: <strong>' + tt[1] + '</strong> — ' + tt[0] + ' (' + tt[2] + ')<br/>';
                html += '<small>Haz clic en la porción para abrir el modal con más info.</small>';
                detail.innerHTML = html;
            };

            canvas.onclick = function(ev) {
                // reuse mousemove logic to get hour
                const rect = canvas.getBoundingClientRect();
                const x = ev.clientX - rect.left - w/2;
                const y = ev.clientY - rect.top - h/2;
                const ang = Math.atan2(y,x);
                let a = ang - (-Math.PI/2);
                if (a < 0) a += Math.PI*2;
                let acc = 0; let hour = 0;
                for (let i=0;i<24;i++){
                    const slice = totals[i]/sum * Math.PI*2;
                    if (a >= acc && a < acc + slice) { hour = i; break; }
                    acc += slice;
                }
                const info = hourly[String(hour)] || {};
                const tt = info.top_track || [];
                if (tt && tt.length >= 3) {
                    // open modal with top track info
                    const date = hour + ':00';
                    const artist = tt[0] || '';
                    const track = tt[1] || '';
                    const imageUrl = '';
                    const url = '#';
                    const plays = tt[2] || 0;
                    openModal(date, artist, track, imageUrl, url, plays);
                }
            };
        }

        renderSummary(summaryData);
        renderCalendar();
        
        document.getElementById('modal').onclick = function(event) {
            if (event.target === this) {
                closeModal();
            }
        }
    </script>
</body>
</html>"""
        
        # Escribir archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Calendario generado: {output_file}")
        print(f"  Total de días: {len(track_per_day)}")
        print(f"  Abre el archivo en tu navegador para ver el calendario interactivo")


def display_scrobbles(scrobbles: List[Scrobble], count: int = 50) -> None:
    """
    Muestra los primeros N scrobbles en formato tabla
    
    Args:
        scrobbles: Lista de objetos Scrobble
        count: Número de scrobbles a mostrar
    """
    if not scrobbles:
        print("No hay scrobbles para mostrar")
        return
    
    display_count = min(count, len(scrobbles))
    
    print(f"\n" + "="*120)
    print(f"Mostrando los primeros {display_count} scrobbles de {len(scrobbles)} totales")
    print("="*120)
    
    # Encabezado
    print(f"{'#':<4} {'UTS':<12} {'Artista':<25} {'Track':<35} {'Álbum':<35}")
    print("-"*120)
    
    # Datos
    for i, scrobble in enumerate(scrobbles[:display_count], 1):
        # Truncar campos largos
        artist = scrobble.artist[:23] + ".." if len(scrobble.artist) > 25 else scrobble.artist
        track = scrobble.track[:33] + ".." if len(scrobble.track) > 35 else scrobble.track
        album = scrobble.album[:33] + ".." if len(scrobble.album) > 35 else scrobble.album
        
        print(f"{i:<4} {scrobble.uts:<12} {artist:<25} {track:<35} {album:<35}")
    
    print("="*120 + "\n")
    
    # Información adicional
    print(f"Total de scrobbles cargados: {len(scrobbles)}")
    print(f"Primero: {scrobbles[0].utc_time if scrobbles else 'N/A'}")
    print(f"Último:  {scrobbles[-1].utc_time if scrobbles else 'N/A'}\n")


def display_top_artists(
    results: List[Tuple[str, int]],
    scrobbles_count: int
) -> None:
    """
    Muestra los artistas más escuchados en formato tabla
    
    Args:
        results: Lista de tuplas (artista, cantidad)
        scrobbles_count: Total de scrobbles considerados (para porcentajes)
    """
    if not results:
        print("No hay datos de artistas para mostrar")
        return
    
    print("\n" + "="*80)
    print(f"TOP {len(results)} ARTISTAS MÁS ESCUCHADOS")
    print("="*80)
    print(f"{'#':<4} {'Artista':<50} {'Escuchas':<12} {'Porcentaje':<12}")
    print("-"*80)
    
    for i, (artist, count) in enumerate(results, 1):
        artist_display = artist[:48] + ".." if len(artist) > 50 else artist
        percentage = (count / scrobbles_count * 100) if scrobbles_count > 0 else 0
        print(f"{i:<4} {artist_display:<50} {count:<12} {percentage:>10.2f}%")
    
    print("="*80 + "\n")


def display_top_albums(
    results: List[Tuple[Tuple[str, str], int]],
    scrobbles_count: int
) -> None:
    """
    Muestra los álbumes más escuchados en formato tabla
    
    Args:
        results: Lista de tuplas ((artista, álbum), cantidad)
        scrobbles_count: Total de scrobbles considerados (para porcentajes)
    """
    if not results:
        print("No hay datos de álbumes para mostrar")
        return
    
    print("\n" + "="*100)
    print(f"TOP {len(results)} ÁLBUMES MÁS ESCUCHADOS")
    print("="*100)
    print(f"{'#':<4} {'Artista':<30} {'Álbum':<40} {'Escuchas':<12} {'Porcentaje':<12}")
    print("-"*100)
    
    for i, ((artist, album), count) in enumerate(results, 1):
        artist_display = artist[:28] + ".." if len(artist) > 30 else artist
        album_display = album[:38] + ".." if len(album) > 40 else album
        percentage = (count / scrobbles_count * 100) if scrobbles_count > 0 else 0
        print(f"{i:<4} {artist_display:<30} {album_display:<40} {count:<12} {percentage:>10.2f}%")
    
    print("="*100 + "\n")


def display_top_tracks(
    results: List[Tuple[Tuple[str, str], int]],
    scrobbles_count: int
) -> None:
    """
    Muestra las canciones más escuchadas en formato tabla
    
    Args:
        results: Lista de tuplas ((artista, canción), cantidad)
        scrobbles_count: Total de scrobbles considerados (para porcentajes)
    """
    if not results:
        print("No hay datos de canciones para mostrar")
        return
    
    print("\n" + "="*100)
    print(f"TOP {len(results)} CANCIONES MÁS ESCUCHADAS")
    print("="*100)
    print(f"{'#':<4} {'Artista':<30} {'Canción':<40} {'Escuchas':<12} {'Porcentaje':<12}")
    print("-"*100)
    
    for i, ((artist, track), count) in enumerate(results, 1):
        artist_display = artist[:28] + ".." if len(artist) > 30 else artist
        track_display = track[:38] + ".." if len(track) > 40 else track
        percentage = (count / scrobbles_count * 100) if scrobbles_count > 0 else 0
        print(f"{i:<4} {artist_display:<30} {track_display:<40} {count:<12} {percentage:>10.2f}%")
    
    print("="*100 + "\n")


def display_peak_day_for_track(
    peak_day_result: Tuple[str, int, int]
) -> None:
    """
    Muestra información del día pico de una canción
    
    Args:
        peak_day_result: Tupla (fecha_formateada, cantidad_escuchas, total_escuchas)
    """
    if not peak_day_result:
        print("No hay datos para mostrar")
        return
    
    date_str, count, total = peak_day_result
    percentage = (count / total * 100) if total > 0 else 0
    
    print("\n" + "="*80)
    print("DÍA CON MÁS ESCUCHAS (ZONA HORARIA LOCAL)")
    print("="*80)
    print(f"Fecha:              {date_str}")
    print(f"Escuchas ese día:   {count}")
    print(f"Total escuchas:     {total}")
    print(f"Porcentaje del día: {percentage:.2f}%")
    print("="*80 + "\n")


def display_all_days_for_track(
    days_result: List[Tuple[str, int]],
    artist: str,
    track: str
) -> None:
    """
    Muestra todos los días en que se escuchó una canción
    
    Args:
        days_result: Lista de tuplas (fecha, cantidad)
        artist: Nombre del artista
        track: Nombre de la canción
    """
    if not days_result:
        print("No hay datos para mostrar")
        return
    
    total_listens = sum(count for _, count in days_result)
    
    print("\n" + "="*100)
    print(f"HISTORIAL DE ESCUCHAS: '{track}' de {artist}")
    print(f"Total de días: {len(days_result)} | Total de escuchas: {total_listens}")
    print("="*100)
    print(f"{'#':<4} {'Fecha':<20} {'Escuchas':<12} {'% del total':<15} {'Barra':<40}")
    print("-"*100)
    
    for i, (date_str, count) in enumerate(days_result, 1):
        percentage = (count / total_listens * 100) if total_listens > 0 else 0
        bar_length = int(percentage / 2.5)  # 40 caracteres máximo
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        print(f"{i:<4} {date_str:<20} {count:<12} {percentage:>13.1f}% {bar:<40}")
    
    print("="*100 + "\n")


def display_top_days_overall(
    days_result: List[Tuple[str, int]],
    n: int = 10,
    metric: str = "escuchas"
) -> None:
    """
    Muestra los n días con más actividad global
    
    Args:
        days_result: Lista de tuplas (fecha, cantidad) resultado de get_top_days_overall*
        n: Número de días mostrados (para contexto en el título)
        metric: Tipo de métrica ("escuchas", "artistas", o "canciones")
    """
    if not days_result:
        print("No hay datos para mostrar")
        return
    
    total = sum(count for _, count in days_result)
    num_results = len(days_result)
    
    print("\n" + "="*100)
    print(f"TOP {num_results} DÍAS CON MÁS {metric.upper()}")
    print(f"Total: {total} {metric}")
    print("="*100)
    print(f"{'#':<4} {'Fecha':<20} {metric.capitalize():<12} {'% del total':<15} {'Barra':<40}")
    print("-"*100)
    
    for i, (date_str, count) in enumerate(days_result, 1):
        percentage = (count / total * 100) if total > 0 else 0
        bar_length = int(percentage / 2.5)  # 40 caracteres máximo
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        print(f"{i:<4} {date_str:<20} {count:<12} {percentage:>13.1f}% {bar:<40}")
    
    print("="*100 + "\n")


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("   CARGADOR DE SCROBBLES - Last.fm Stats")
    print("="*60)
    
    try:
        # Crear cargador
        loader = ScrobblesLoader('data')
        
        # Cargar archivo interactivamente
        scrobbles = loader.interactive_load()
        
        if scrobbles:
            # Mostrar primeros 50 scrobbles
            display_scrobbles(scrobbles, count=50)
            
            # Opción de mostrar más
            while True:
                more = input("¿Deseas ver más scrobbles? (s/n): ").strip().lower()
                if more == 's':
                    try:
                        count = int(input("¿Cuántos scrobbles deseas ver?: "))
                        display_scrobbles(scrobbles, count=count)
                    except ValueError:
                        print("Por favor, ingresa un número válido")
                else:
                    break
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
