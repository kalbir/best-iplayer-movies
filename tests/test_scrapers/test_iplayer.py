import json
from unittest.mock import Mock, patch

from scrapers.iplayer import IPlayerScraper


def promo(episode_id, title):
    return {
        'episodeId': episode_id,
        'url': f'/iplayer/episode/{episode_id}',
        'headline': title,
        'description': None,
        'image': {'src': f'https://ichef.bbci.co.uk/{episode_id}.jpg'},
    }


def films_page(*urns):
    """The films page embeds its carousels as a JSON string in window.__INITIAL_DATA__."""
    data = {'data': {
        'global-navigation': {'data': {'signInLabel': 'Sign in'}},
        **{f'simple-promo-collection?urn={urn}': {'data': {'urn': urn, 'total': 0, 'promos': []}} for urn in urns},
    }}
    return f'<script>window.__INITIAL_DATA__={json.dumps(json.dumps(data))};</script>'


def fake_get(films_html, carousels):
    """carousels maps urn -> list of pages, each a list of promos."""
    def get(url, params=None, headers=None):
        response = Mock()
        response.raise_for_status = Mock()
        if params is None:
            response.text = films_html
        else:
            pages = carousels[params['urn']]
            page = params['currentCarouselPage']
            # iPlayer repeats the last page when asked past the end
            promos = pages[min(page, len(pages)) - 1]
            response.json.return_value = {'total': sum(len(p) for p in pages), 'promos': promos}
        return response
    return get


@patch('scrapers.iplayer.time.sleep')
def test_collects_every_film_across_carousels_and_pages(_sleep):
    carousels = {
        'featured': [[promo('a', 'Aftersun'), promo('b', 'Brief Encounter')], [promo('c', 'Carol')]],
        'comedy': [[promo('b', 'Brief Encounter'), promo('d', 'Dr. Strangelove')]],
    }
    with patch('scrapers.iplayer.requests.get', side_effect=fake_get(films_page('featured', 'comedy'), carousels)):
        movies = IPlayerScraper().get_current_movies()

    assert sorted(m['title'] for m in movies) == ['Aftersun', 'Brief Encounter', 'Carol', 'Dr. Strangelove']
    aftersun = next(m for m in movies if m['title'] == 'Aftersun')
    assert aftersun['url'] == 'https://www.bbc.co.uk/iplayer/episode/a'
    assert aftersun['thumbnail'] == 'https://ichef.bbci.co.uk/a.jpg'


@patch('scrapers.iplayer.time.sleep')
def test_stops_paging_when_a_carousel_repeats_itself(_sleep):
    # total overstates what the carousel will actually return
    def get(url, params=None, headers=None):
        response = fake_get(films_page('featured'), {'featured': [[promo('a', 'Aftersun')]]})(url, params, headers)
        if params:
            response.json.return_value['total'] = 99
        return response

    with patch('scrapers.iplayer.requests.get', side_effect=get) as requests_get:
        movies = IPlayerScraper().get_current_movies()

    assert [m['title'] for m in movies] == ['Aftersun']
    assert requests_get.call_count == 3  # films page, page 1, page 2 (a repeat)
