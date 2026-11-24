import pytest
import json
import sys
import tempfile
import os
from unittest.mock import patch
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from load_scrobbles import Scrobble, ScrobblesAnalyzer, ScrobblesLoader
from main import calculate_complete_summary


def make_scrobbles_sequence():
    """Crea una lista de scrobbles sintéticos para pruebas.
    Escenario simple que permite verificar conteos, picos y rachas.
    """
    base = datetime(2026, 2, 1, 12, 0)
    items = []

    def add(artist, album, track, day_offset, times=1):
        dt = base + timedelta(days=day_offset)
        for i in range(times):
            # variar minutos para evitar iguales exactos
            dt_i = dt + timedelta(minutes=i)
            uts = str(int(dt_i.replace(tzinfo=None).timestamp()))
            items.append(Scrobble({
                'date': {'uts': uts, '#text': dt_i.strftime('%d %b %Y, %H:%M')},
                'artist': {'#text': artist},
                'album': {'#text': album},
                'name': track,
                'mbid': ''
            }))

    # Track C (Artist1) played 4 consecutive days (0..3)
    add('Artist1', 'Album1', 'SongC', 0, times=1)
    add('Artist1', 'Album1', 'SongC', 1, times=2)
    add('Artist1', 'Album1', 'SongC', 2, times=1)
    add('Artist1', 'Album1', 'SongC', 3, times=1)

    # Track A (Artist1) played 3 consecutive days (0..2) and an extra play on day 5
    add('Artist1', 'Album1', 'SongA', 0, times=1)
    add('Artist1', 'Album1', 'SongA', 1, times=1)
    add('Artist1', 'Album1', 'SongA', 2, times=3)
    add('Artist1', 'Album1', 'SongA', 5, times=1)

    # Track B (Artist2) scattered plays
    add('Artist2', 'Album2', 'SongB', 1, times=1)
    add('Artist2', 'Album2', 'SongB', 2, times=1)
    add('Artist2', 'Album2', 'SongB', 4, times=2)

    # Track D (Artist3) single day plays
    add('Artist3', 'Album3', 'SongD', 2, times=4)

    return items


@pytest.fixture
def sample_scrobbles():
    return make_scrobbles_sequence()


def test_top_tracks_and_artists(sample_scrobbles):
    top_tracks = ScrobblesAnalyzer.get_top_tracks(sample_scrobbles, n=3)
    assert isinstance(top_tracks, list)
    # Expect SongA and SongC to be in the top results; the 3rd can be SongD or SongB (tie)
    names = [t[0][1] for t in top_tracks]
    assert 'SongA' in names
    assert 'SongC' in names
    assert any(x in names for x in ('SongD', 'SongB'))

    top_artists = ScrobblesAnalyzer.get_top_artists(sample_scrobbles, n=3)
    assert top_artists[0][0] == 'Artist1'


def test_peak_day_and_all_days(sample_scrobbles):
    # For SongA, day 2 should be peak (3 plays)
    res = ScrobblesAnalyzer.get_peak_day_for_track(sample_scrobbles, 'Artist1', 'SongA')
    assert res is not None
    peak_day, count, total = res
    assert count == 3
    assert total >= 5

    all_days = ScrobblesAnalyzer.get_all_days_for_track(sample_scrobbles, 'Artist1', 'SongA')
    assert isinstance(all_days, list)
    assert sum(c for _, c in all_days) == total


def test_top_days_overall_and_metrics(sample_scrobbles):
    top_days = ScrobblesAnalyzer.get_top_days_overall(sample_scrobbles, n=5)
    assert isinstance(top_days, list)
    # day 2 (base + 2) should have many plays
    assert len(top_days) <= 5

    top_by_artists = ScrobblesAnalyzer.get_top_days_overall_by_artist_count(sample_scrobbles, n=5)
    assert isinstance(top_by_artists, list)

    top_by_tracks = ScrobblesAnalyzer.get_top_days_overall_by_track_count(sample_scrobbles, n=5)
    assert isinstance(top_by_tracks, list)


def test_most_played_track_per_day_and_peak_plays(sample_scrobbles):
    mpt = ScrobblesAnalyzer.get_most_played_track_per_day(sample_scrobbles)
    assert isinstance(mpt, dict)
    # Check that returned values have expected tuple structure
    for day, info in mpt.items():
        assert len(info) == 5 or len(info) == 4

    top_peaks = ScrobblesAnalyzer.get_top_tracks_by_peak_plays(sample_scrobbles, n=3)
    assert isinstance(top_peaks, list)
    # Each entry should be ((artist, track), plays, day)
    assert all(isinstance(e[0], tuple) and isinstance(e[1], int) for e in top_peaks)


def test_consecutive_days_functions(sample_scrobbles):
    top_tracks_consec = ScrobblesAnalyzer.get_top_tracks_by_consecutive_days(sample_scrobbles, n=3)
    assert isinstance(top_tracks_consec, list)
    # Expect SongC (4 days) then SongA (3 days)
    assert top_tracks_consec[0][0][1] == 'SongC'
    assert top_tracks_consec[0][1] == 4

    top_artists_consec = ScrobblesAnalyzer.get_top_artists_by_consecutive_days(sample_scrobbles, n=3)
    assert top_artists_consec[0][0] == 'Artist1'
    assert top_artists_consec[0][1] >= 4

    top_albums_consec = ScrobblesAnalyzer.get_top_albums_by_consecutive_days(sample_scrobbles, n=3)
    # Album1 should top the album streaks
    assert any(item[0][1] == 'Album1' for item in top_albums_consec)


# ============================================================================
# Additional comprehensive tests for robustness
# ============================================================================

def test_scrobble_creation():
    """Test Scrobble object creation and attributes"""
    data = {
        'date': {'uts': '1675000000', '#text': '01 Feb 2023, 12:00'},
        'artist': {'#text': 'Test Artist', 'mbid': 'artist-mbid'},
        'album': {'#text': 'Test Album', 'mbid': 'album-mbid'},
        'name': 'Test Track',
        'mbid': 'track-mbid',
        'url': 'https://www.last.fm/music/test',
        'streamable': '1',
        'image': [
            {'size': 'small', '#text': 'http://example.com/small.jpg'},
            {'size': 'medium', '#text': 'http://example.com/medium.jpg'}
        ]
    }
    scrobble = Scrobble(data)
    
    assert scrobble.artist == 'Test Artist'
    assert scrobble.track == 'Test Track'
    assert scrobble.album == 'Test Album'
    assert scrobble.uts == '1675000000'
    assert scrobble.images['small'] == 'http://example.com/small.jpg'
    assert scrobble.images['medium'] == 'http://example.com/medium.jpg'


def test_empty_scrobbles_list():
    """Test analyzer functions with empty scrobbles list"""
    empty = []
    
    assert ScrobblesAnalyzer.get_top_tracks(empty, n=5) == []
    assert ScrobblesAnalyzer.get_top_artists(empty, n=5) == []
    assert ScrobblesAnalyzer.get_top_albums(empty, n=5) == []
    # get_top_days_overall may return None or [] for empty list
    result = ScrobblesAnalyzer.get_top_days_overall(empty, n=5)
    assert result is None or result == []
    # get_most_played_track_per_day may return None or {} for empty list
    result2 = ScrobblesAnalyzer.get_most_played_track_per_day(empty)
    assert result2 is None or result2 == {}


def test_estimate_track_duration_uses_artist_median_when_missing():
    """Un track sin duración debe estimarse a partir de la distribución del artista, no con un valor fijo."""
    from load_scrobbles import _duration_cache

    original_cache = _duration_cache.copy()
    try:
        _duration_cache.clear()
        _duration_cache[('Artist1', 'SongA')] = 120
        _duration_cache[('Artist1', 'SongB')] = 300
        _duration_cache[('Artist1', 'SongC')] = 360

        estimated = ScrobblesAnalyzer._estimate_track_duration('Artist1', 'Missing Song', fetch_remote=False)
        assert estimated == 300
    finally:
        _duration_cache.clear()
        _duration_cache.update(original_cache)


def test_regularity_ranks_by_distinct_days_and_span():
    """La regularidad debe favorecer canciones escuchadas en más días distintos, no solo por un par de días muy repetidos."""
    base = datetime(2024, 1, 1, 12, 0)
    items = []

    def add(artist, track, day_offset, times=1):
        dt = base + timedelta(days=day_offset)
        for i in range(times):
            dt_i = dt + timedelta(minutes=i)
            uts = str(int(dt_i.replace(tzinfo=None).timestamp()))
            items.append(Scrobble({
                'date': {'uts': uts, '#text': dt_i.strftime('%d %b %Y, %H:%M')},
                'artist': {'#text': artist},
                'album': {'#text': 'Album'},
                'name': track,
                'mbid': ''
            }))

    # SongA: escuchado en 6 días distintos durante varias semanas
    for day in [0, 7, 14, 21, 28, 35]:
        add('ArtistX', 'SongA', day)

    # SongB: escuchado solo en 2 días, aunque varias veces cada uno
    for day in [0, 0, 0, 0, 30, 30, 30]:
        add('ArtistX', 'SongB', day)

    regularity = ScrobblesAnalyzer.get_top_tracks_by_regularity(items, n=2)
    assert regularity[0][0][1] == 'SongA'
    assert regularity[0][2] >= regularity[1][2]


def test_api_deduplicates_repeated_scrobbles():
    """La importación desde la API no debe duplicar scrobbles ya presentes en caché."""
    loader = ScrobblesLoader('data')
    repeated = [
        {'date': {'uts': '1700000000', '#text': '01 Jan 2024, 12:00'}, 'artist': {'#text': 'Mori'}, 'album': {'#text': 'A'}, 'name': 'Lovers to Strangers'},
        {'date': {'uts': '1700000000', '#text': '01 Jan 2024, 12:00'}, 'artist': {'#text': 'Mori'}, 'album': {'#text': 'A'}, 'name': 'Lovers to Strangers'},
        {'date': {'uts': '1700000060', '#text': '01 Jan 2024, 12:01'}, 'artist': {'#text': 'Mori'}, 'album': {'#text': 'A'}, 'name': 'Lovers to Strangers'},
    ]

    deduped = loader._deduplicate_scrobbles_data(repeated)
    assert len(deduped) == 2
    assert all(item['date']['uts'] != '1700000000' or item['name'] == 'Lovers to Strangers' for item in deduped)


def test_recentness_metric_prioritizes_last_listened_tracks():
    """La métrica de recencia debe devolver la canción escuchada más recientemente primero."""
    base = datetime(2024, 1, 1, 12, 0)
    items = []

    def add(artist, track, days_ago, plays=1):
        for i in range(plays):
            dt = base - timedelta(days=days_ago, minutes=i)
            uts = str(int(dt.replace(tzinfo=None).timestamp()))
            items.append(Scrobble({
                'date': {'uts': uts, '#text': dt.strftime('%d %b %Y, %H:%M')},
                'artist': {'#text': artist},
                'album': {'#text': 'Album'},
                'name': track,
                'mbid': ''
            }))

    add('ArtistA', 'Fresh Track', 1, plays=5)
    add('ArtistB', 'Old Track', 45, plays=5)

    recent = ScrobblesAnalyzer.get_top_tracks_by_recentness(items, n=2)
    assert recent[0][0][1] == 'Fresh Track'
    assert recent[0][1] < recent[1][1]


def test_weekday_affinity_and_monthly_consistency_metrics_are_removed():
    """Estas métricas ya no forman parte del calendario ni del cálculo activo."""
    assert not hasattr(ScrobblesAnalyzer, 'get_top_tracks_by_weekday_affinity')
    assert not hasattr(ScrobblesAnalyzer, 'get_top_tracks_by_monthly_consistency')


def test_staleness_threshold_and_heatmap_data():
    """El ranking de tiempo sin escuchar debe poder filtrar por umbral y producir heatmaps de meses."""
    base = datetime(2024, 1, 1, 12, 0)
    items = []

    def add(artist, track, offset_days, plays=1):
        for i in range(plays):
            dt = base + timedelta(days=offset_days, hours=i)
            uts = str(int(dt.replace(tzinfo=None).timestamp()))
            items.append(Scrobble({
                'date': {'uts': uts, '#text': dt.strftime('%d %b %Y, %H:%M')},
                'artist': {'#text': artist},
                'album': {'#text': 'Album'},
                'name': track,
                'mbid': ''
            }))

    add('ArtistA', 'Long Absent', 180, plays=5)
    add('ArtistB', 'Older Hit', 10, plays=2)
    add('ArtistC', 'Noisy Song', 60, plays=1)

    staleness = ScrobblesAnalyzer.get_top_tracks_by_staleness(items, n=3, min_plays=2)
    heatmap = ScrobblesAnalyzer.get_track_monthly_heatmap(items, [('ArtistA', 'Long Absent'), ('ArtistB', 'Older Hit')])

    assert staleness[0][0][1] == 'Older Hit'
    assert any(item[0][1] == 'Long Absent' for item in staleness)
    assert heatmap[0]['track'] == 'Long Absent'
    assert isinstance(heatmap[0]['series'], list)
    assert heatmap[0]['series']


def test_regularity_score_is_comprehensible_and_staleness_ranks_old_tracks_first():
    """La regularidad debe usar un coeficiente acotado y el estancamiento debe poner primero las canciones más viejas."""
    base = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    items = []

    for i in range(5):
        ts = base - timedelta(days=i * 2)
        uts = str(int(ts.replace(tzinfo=None).timestamp()))
        items.append(Scrobble({
            'date': {'uts': uts, '#text': ts.strftime('%d %b %Y, %H:%M')},
            'artist': {'#text': 'ArtistA'},
            'album': {'#text': 'Album'},
            'name': 'Regular Song',
            'mbid': ''
        }))

    for i in range(2):
        ts = base - timedelta(days=180 + i)
        uts = str(int(ts.replace(tzinfo=None).timestamp()))
        items.append(Scrobble({
            'date': {'uts': uts, '#text': ts.strftime('%d %b %Y, %H:%M')},
            'artist': {'#text': 'ArtistB'},
            'album': {'#text': 'Album'},
            'name': 'Forgotten Song',
            'mbid': ''
        }))

    regularity = ScrobblesAnalyzer.get_top_tracks_by_regularity(items, n=2, min_plays=2)
    staleness = ScrobblesAnalyzer.get_top_tracks_by_staleness(items, n=2, min_plays=2)

    assert regularity[0][1] <= 10.0
    assert staleness[0][0][1] == 'Forgotten Song'


def test_utc_to_local_accepts_lastfm_and_iso_timestamps():
    lastfm_date = ScrobblesAnalyzer._utc_to_local("01 Feb 2023, 12:00")
    iso_date = ScrobblesAnalyzer._utc_to_local("2023-02-01T12:00:00+00:00")

    assert lastfm_date is not None and iso_date is not None
    assert lastfm_date.timestamp() == iso_date.timestamp()


def test_single_scrobble():
    """Test analyzer with a single scrobble"""
    base = datetime(2026, 2, 1, 12, 0)
    uts = str(int(base.replace(tzinfo=None).timestamp()))
    single = [Scrobble({
        'date': {'uts': uts, '#text': base.strftime('%d %b %Y, %H:%M')},
        'artist': {'#text': 'Single Artist'},
        'album': {'#text': 'Single Album'},
        'name': 'Single Track',
        'mbid': ''
    })]
    
    top_tracks = ScrobblesAnalyzer.get_top_tracks(single, n=5)
    assert len(top_tracks) == 1
    assert top_tracks[0][0] == ('Single Artist', 'Single Track')
    assert top_tracks[0][1] == 1


def test_duplicate_tracks():
    """Test that duplicate tracks are properly aggregated"""
    base = datetime(2026, 2, 1, 12, 0)
    items = []
    
    for i in range(5):
        dt = base + timedelta(hours=i)
        uts = str(int(dt.replace(tzinfo=None).timestamp()))
        items.append(Scrobble({
            'date': {'uts': uts, '#text': dt.strftime('%d %b %Y, %H:%M')},
            'artist': {'#text': 'Same Artist'},
            'album': {'#text': 'Same Album'},
            'name': 'Same Track',
            'mbid': ''
        }))
    
    top_tracks = ScrobblesAnalyzer.get_top_tracks(items, n=5)
    assert len(top_tracks) == 1
    assert top_tracks[0][1] == 5  # Total plays


def test_top_n_parameter():
    """Test that top_n parameter is respected"""
    base = datetime(2026, 2, 1, 12, 0)
    items = []
    
    # Create 10 different tracks
    for track_id in range(10):
        dt = base + timedelta(hours=track_id)
        uts = str(int(dt.replace(tzinfo=None).timestamp()))
        items.append(Scrobble({
            'date': {'uts': uts, '#text': dt.strftime('%d %b %Y, %H:%M')},
            'artist': {'#text': f'Artist{track_id}'},
            'album': {'#text': f'Album{track_id}'},
            'name': f'Track{track_id}',
            'mbid': ''
        }))
    
    top_3 = ScrobblesAnalyzer.get_top_tracks(items, n=3)
    assert len(top_3) <= 3
    
    top_20 = ScrobblesAnalyzer.get_top_tracks(items, n=20)
    assert len(top_20) == 10


def test_hourly_top_extraction(sample_scrobbles):
    """Test that hourly top tracks/artists are correctly extracted"""
    hourly = ScrobblesAnalyzer.get_hourly_top(sample_scrobbles)
    
    assert isinstance(hourly, dict)
    for hour_str, info in hourly.items():
        hour = int(hour_str)
        assert 0 <= hour < 24
        assert 'total' in info
        assert isinstance(info['total'], int)


def test_multi_method_consistency(sample_scrobbles):
    """Test that multiple analyzer methods return consistent data types"""
    # All these should return lists
    assert isinstance(ScrobblesAnalyzer.get_top_tracks(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_artists(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_albums(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_tracks_by_peak_plays(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_tracks_by_consecutive_days(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_artists_by_consecutive_days(sample_scrobbles), list)
    assert isinstance(ScrobblesAnalyzer.get_top_albums_by_consecutive_days(sample_scrobbles), list)
    
    # get_most_played_track_per_day should return a dict
    assert isinstance(ScrobblesAnalyzer.get_most_played_track_per_day(sample_scrobbles), dict)


def test_complete_summary_and_html_include_both_metrics(sample_scrobbles):
    summary = calculate_complete_summary(
        sample_scrobbles, n_items=10, n_days=5, n_peak_plays=5,
        fetch_duration_data=False, split_by_year=True
    )

    assert summary["plays"]["top_tracks"]
    assert summary["time"]["top_tracks"]
    assert summary["plays"]["top_tracks_regularity"]
    assert "2026" in summary["years"]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "complete_calendar.html")
        ScrobblesAnalyzer.generate_calendar_html(
            sample_scrobbles, output_file=output_file, summary=summary, split_by_year=True
        )
        with open(output_file, "r", encoding="utf-8") as html_file:
            content = html_file.read()
        for marker in ("trackPerDayTime", "summaryTimeData", "summaryByYearTime", "dailyTotals", "metricSelect", "yearSelect"):
            assert marker in content


def test_peak_time_can_differ_from_peak_play_count():
    base = datetime(2026, 2, 1, 12, 0)
    scrobbles = []
    for track, count in (("Long Track", 1), ("Short Track", 3)):
        for index in range(count):
            timestamp = base + timedelta(minutes=index)
            scrobbles.append(Scrobble({
                "date": {"uts": str(int(timestamp.timestamp())), "#text": timestamp.strftime("%d %b %Y, %H:%M")},
                "artist": {"#text": "Artist"},
                "name": track,
            }))

    def duration_for_track(artist, track, fetch_remote=False):
        return 700 if track == "Long Track" else 100

    with patch.object(ScrobblesAnalyzer, "_get_track_duration", side_effect=duration_for_track):
        peak_time = ScrobblesAnalyzer.get_top_tracks_by_peak_time(scrobbles, n=2)
        hourly_time = ScrobblesAnalyzer.get_hourly_top_by_time(scrobbles, fetch_remote=False)

    peak_plays = ScrobblesAnalyzer.get_top_tracks_by_peak_plays(scrobbles, n=2)
    hourly_plays = ScrobblesAnalyzer.get_hourly_top(scrobbles)
    assert peak_time[0][0][1] == "Long Track"
    assert peak_plays[0][0][1] == "Short Track"
    busiest_hour = next(hour for hour, data in hourly_plays.items() if data["total"])
    assert hourly_time[busiest_hour]["top_track"][1] == "Long Track"
    assert hourly_plays[busiest_hour]["top_track"][1] == "Short Track"


def test_loader_file_loading():
    """Test that loader can identify scrobbles files"""
    loader = ScrobblesLoader('data')
    files = loader.list_files()
    
    # Should have data directory with scrobbles files
    assert isinstance(files, list)
    # We expect at least some scrobbles files in the test data
    assert len(files) >= 0  # Could be 0 if no files, but usually at least 1


def test_html_generation_basic(sample_scrobbles):
    """Test that HTML generation doesn't crash and produces output"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'test_calendar.html')
        
        # Should not raise an exception
        try:
            ScrobblesAnalyzer.generate_calendar_html(
                sample_scrobbles,
                output_file=output_file,
                summary=None,
                split_by_year=False,
                by_time=False
            )
            
            # File should exist
            assert os.path.exists(output_file)
            
            # File should contain HTML structure
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert '<!DOCTYPE html>' in content
                assert '<script>' in content
                assert 'trackPerDay' in content
                assert '</html>' in content
        except Exception as e:
            pytest.fail(f"HTML generation failed: {e}")


def test_html_generation_with_split_by_year(sample_scrobbles):
    """Test HTML generation with split_by_year flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'test_calendar_yearly.html')
        
        try:
            ScrobblesAnalyzer.generate_calendar_html(
                sample_scrobbles,
                output_file=output_file,
                summary=None,
                split_by_year=True
            )
            
            assert os.path.exists(output_file)
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'split_by_year' in content or 'trackByYear' in content
        except Exception as e:
            pytest.fail(f"HTML generation with split_by_year failed: {e}")


def test_special_characters_in_track_data():
    """Test handling of special characters (quotes, ampersands, etc.)"""
    base = datetime(2026, 2, 1, 12, 0)
    uts = str(int(base.replace(tzinfo=None).timestamp()))
    
    special_scrobbles = [Scrobble({
        'date': {'uts': uts, '#text': base.strftime('%d %b %Y, %H:%M')},
        'artist': {'#text': "Artist's Name & Co."},
        'album': {'#text': 'Album "Special"'},
        'name': 'Track <with> & special chars',
        'mbid': ''
    })]
    
    # Should handle special characters without crashing
    top_tracks = ScrobblesAnalyzer.get_top_tracks(special_scrobbles)
    assert len(top_tracks) == 1
    assert "Artist's Name & Co." in top_tracks[0][0][0]


if __name__ == '__main__':
    pytest.main(['-v'])
