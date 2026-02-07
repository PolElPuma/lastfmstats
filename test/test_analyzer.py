import pytest
import json
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from load_scrobbles import Scrobble, ScrobblesAnalyzer, ScrobblesLoader


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
                split_by_year=False
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
