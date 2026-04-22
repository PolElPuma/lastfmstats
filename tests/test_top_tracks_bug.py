#!/usr/bin/env python3
"""Test para reproducir el bug de reemplazo de canción en el top"""
import sys
sys.path.insert(0, 'src')

from load_scrobbles import Scrobble, ScrobblesAnalyzer
from datetime import datetime, timedelta

def create_test_scrobbles():
    """Crea un conjunto de scrobbles para probar el bug"""
    scrobbles = []
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    
    # Canción 1: "The Beatles - Across the Universe" - 50 veces
    for i in range(50):
        data = {
            'artist': {'#text': 'The Beatles'},
            'name': 'Across the Universe',
            'date': {
                'uts': str(int((base_date + timedelta(hours=i)).timestamp())),
                '#text': (base_date + timedelta(hours=i)).isoformat()
            },
            'image': [
                {'#text': '', 'size': 'small'},
                {'#text': '', 'size': 'medium'},
                {'#text': '', 'size': 'large'},
                {'#text': '', 'size': 'extralarge'}
            ],
            'url': 'https://www.last.fm/music/The+Beatles/_/Across+the+Universe'
        }
        scrobbles.append(Scrobble(data))
    
    # Canción 2: "Pink Floyd - Comfortably Numb" - 40 veces
    for i in range(40):
        data = {
            'artist': {'#text': 'Pink Floyd'},
            'name': 'Comfortably Numb',
            'date': {
                'uts': str(int((base_date + timedelta(hours=50+i)).timestamp())),
                '#text': (base_date + timedelta(hours=50+i)).isoformat()
            },
            'image': [
                {'#text': '', 'size': 'small'},
                {'#text': '', 'size': 'medium'},
                {'#text': '', 'size': 'large'},
                {'#text': '', 'size': 'extralarge'}
            ],
            'url': 'https://www.last.fm/music/Pink+Floyd/_/Comfortably+Numb'
        }
        scrobbles.append(Scrobble(data))
    
    # Última canción: "David Bowie - Space Oddity" - 1 sola vez, pero es el último scrobble
    data = {
        'artist': {'#text': 'David Bowie'},
        'name': 'Space Oddity',
        'date': {
            'uts': str(int((base_date + timedelta(hours=100)).timestamp())),
            '#text': (base_date + timedelta(hours=100)).isoformat()
        },
        'image': [
            {'#text': '', 'size': 'small'},
            {'#text': '', 'size': 'medium'},
            {'#text': '', 'size': 'large'},
            {'#text': '', 'size': 'extralarge'}
        ],
        'url': 'https://www.last.fm/music/David+Bowie/_/Space+Oddity'
    }
    scrobbles.append(Scrobble(data))
    
    return scrobbles

def test_top_tracks_integrity():
    """Verifica que el top tracks no sea reemplazado por el último scrobble"""
    print("🧪 Test: Verificar integridad del top tracks")
    print("=" * 60)
    
    scrobbles = create_test_scrobbles()
    
    # Obtener top 2 tracks
    top_tracks = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=2)
    
    print(f"Total scrobbles: {len(scrobbles)}")
    print(f"Último scrobble: David Bowie - Space Oddity")
    print(f"\nTop 2 tracks:")
    
    expected_top = [
        (('The Beatles', 'Across the Universe'), 50),
        (('Pink Floyd', 'Comfortably Numb'), 40)
    ]
    
    assert len(top_tracks) == 2, f"❌ esperado 2 tracks, obtuvo {len(top_tracks)}"
    
    for i, ((artist, track), count) in enumerate(top_tracks, 1):
        expected_artist, expected_track = expected_top[i-1][0]
        expected_count = expected_top[i-1][1]
        
        print(f"  {i}. {artist} - {track} ({count} escuchas)")
        
        assert artist == expected_artist, f"❌ Posición {i}: Se esperaba artista '{expected_artist}', se obtuvo '{artist}'"
        assert track == expected_track, f"❌ Posición {i}: Se esperaba track '{expected_track}', se obtuvo '{track}'"
        assert count == expected_count, f"❌ Posición {i}: Se esperaba {expected_count} escuchas, se obtuvieron {count}"
    
    # Verificar que David Bowie NO esté en el top
    artists_in_top = [artist for (artist, _), _ in top_tracks]
    assert 'David Bowie' not in artists_in_top, "❌ David Bowie (último scrobble) no debería estar en el top"
    
    print("\n✅ Test PASSED: Top tracks es correcto y no contiene el último scrobble")


def test_most_played_per_day():
    """Verifica que get_most_played_track_per_day no corrompa los datos"""
    print("\n🧪 Test: Verificar get_most_played_track_per_day")
    print("=" * 60)
    
    scrobbles = create_test_scrobbles()
    
    most_played = ScrobblesAnalyzer.get_most_played_track_per_day(scrobbles)
    
    if most_played:
        print(f"Total días con scrobbles: {len(most_played)}")
        
        # Verificar que cada entrada tenga la estructura correcta
        for day, (artist, track, img, url, count) in list(most_played.items())[:3]:
            print(f"  {day}: {artist} - {track} ({count} veces)")
            assert isinstance(artist, str), f"❌ artist debe ser string, obtuvo {type(artist)}"
            assert isinstance(track, str), f"❌ track debe ser string, obtuvo {type(track)}"
            assert isinstance(count, int), f"❌ count debe ser int, obtuvo {type(count)}"
        
        print("\n✅ Test PASSED: get_most_played_track_per_day es correcto")
    else:
        print("⚠ No hay datos en most_played")


def test_peak_plays():
    """Verifica que get_top_tracks_by_peak_plays sea correcto"""
    print("\n🧪 Test: Verificar get_top_tracks_by_peak_plays")
    print("=" * 60)
    
    scrobbles = create_test_scrobbles()
    
    peak_plays = ScrobblesAnalyzer.get_top_tracks_by_peak_plays(scrobbles, n=3)
    
    if peak_plays:
        print(f"Top {len(peak_plays)} canciones por pico:")
        for (artist, track), plays, day in peak_plays:
            print(f"  {artist} - {track}: {plays} en {day}")
            assert isinstance(artist, str), f"❌ artist debe ser string"
            assert isinstance(track, str), f"❌ track debe ser string"
            assert isinstance(plays, int), f"❌ plays debe ser int"
        
        print("\n✅ Test PASSED: get_top_tracks_by_peak_plays es correcto")
    else:
        print("⚠ No hay datos en peak_plays")


def test_data_sharing_issues():
    """Verifica si hay problemas de referencias compartidas"""
    print("\n🧪 Test: Detectar problemas de referencias compartidas")
    print("=" * 60)
    
    scrobbles = create_test_scrobbles()
    
    # Obtener top tracks múltiples veces
    top_frames_1 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=2)
    top_frames_2 = ScrobblesAnalyzer.get_top_tracks(scrobbles, n=2)
    
    # Comparar que sean idénticos en valor (aunque diferentes objetos)
    for (a1, t1), c1 in top_frames_1:
        found = False
        for (a2, t2), c2 in top_frames_2:
            if a1 == a2 and t1 == t2 and c1 == c2:
                found = True
                break
        assert found, f"❌ Track perdido en segunda llamada: {a1} - {t1}"
    
    print("✅ Test PASSED: Sin problemas de referencias compartidas")


if __name__ == "__main__":
    try:
        test_top_tracks_integrity()
        test_most_played_per_day()
        test_peak_plays()
        test_data_sharing_issues()
        print("\n" + "="*60)
        print("✅ Todos los tests pasaron correctamente")
    except AssertionError as e:
        print(f"\n❌ Test fallido: {e}")
        sys.exit(1)
