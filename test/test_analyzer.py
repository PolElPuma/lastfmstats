import pytest
from datetime import datetime, timedelta
from load_scrobbles import Scrobble, ScrobblesAnalyzer


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


if __name__ == '__main__':
    pytest.main(['-q'])
