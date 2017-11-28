import operator

import requests
import urllib3
import xmltodict
from plexapi.library import ShowSection, MovieSection
from plexapi.server import PlexServer
from plexapi.video import Show

PLEX_URL = ""
PLEX_TOKEN = ""

# Analysis Parameters
CAST_RANGE = 5
SHOW_MULTIPLIER = True
SHOW_DEFAULT_RATING = float(5)
GENRE_RANGE = 3
PLAYLIST_SIZE = 10

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_plex_api(path="", method="GET", plextv=False, **kwargs):
    url = "https://plex.tv" if plextv else PLEX_URL.rstrip("/")
    headers = {"X-Plex-Token": PLEX_TOKEN, "Accept": "application/json"}
    params = {}
    if kwargs:
        params.update(kwargs)

    try:
        if method.upper() == "GET":
            r = requests.get(url + path,
                             headers=headers, params=params, verify=False)
        elif method.upper() == "POST":
            r = requests.post(url + path,
                              headers=headers, params=params, verify=False)
        elif method.upper() == "PUT":
            r = requests.put(url + path,
                             headers=headers, params=params, verify=False)
        elif method.upper() == "DELETE":
            r = requests.delete(url + path,
                                headers=headers, params=params, verify=False)
        else:
            print("Invalid request method provided: {method}".format(method=method))
            return

        if r and len(r.content):
            if "application/json" in r.headers["Content-Type"]:
                return r.json()
            elif "application/xml" in r.headers["Content-Type"]:
                return xmltodict.parse(r.content)
            else:
                return r.content
        else:
            return r.content

    except Exception as e:
        print("Error fetching from Plex API: {err}".format(err=e))


def get_user_tokens(server_id):
    api_users = fetch_plex_api("/api/users", plextv=True)
    api_shared_servers = fetch_plex_api("/api/servers/{server_id}/shared_servers".format(server_id=server_id),
                                        plextv=True)
    user_ids = {user["@id"]: user.get("@username", user.get("@title")) for user in api_users["MediaContainer"]["User"]}
    users = {user_ids[user["@userID"]]: user["@accessToken"] for user in
             api_shared_servers["MediaContainer"]["SharedServer"]}
    return users


def main():
    plex_server = PlexServer(PLEX_URL, PLEX_TOKEN)
    users_plex = [plex_server]
    plex_users = get_user_tokens(plex_server.machineIdentifier)
    users_plex.extend([PlexServer(PLEX_URL, u) for n, u in plex_users.items()])

    for plex in users_plex:
        result = analysis(plex)
        for playlist in plex.playlists():
            if playlist.title.startswith("Recommend for "):
                playlist.delete()

        for section, shows in result.items():
            playlist_title = "Recommend for " + section
            media = [get_first_episode(s) for s in shows]
            if len(media) > 0:
                plex.createPlaylist(playlist_title, media)


def get_first_episode(show):
    return show.episode(season=1, episode=1) if isinstance(show, Show) else show


def analysis(plex):
    result = {}
    for section in plex.library.sections():
        if not isinstance(section, ShowSection) and not isinstance(section, MovieSection):
            continue
        result[section.title] = analysis_show(section)
    return result


def analysis_show(section):
    shows = section.all()
    watched_shows = [s for s in shows if s.isWatched or s.viewCount > 0]
    unwatch_shows = [s for s in shows if not s.isWatched and s.viewCount <= 0]
    cast_score = {}
    genre_score = {}
    for show in watched_shows:
        rating = show.rating if show.rating is not None else SHOW_DEFAULT_RATING
        show_multiplier = rating / 10 if SHOW_MULTIPLIER else 1
        for index, cast in enumerate(show.actors):
            cast_score[cast.tag] = calculate_range_score(index, CAST_RANGE) * show_multiplier

        for index, genre in enumerate(show.genres):
            genre_score[genre.tag] = calculate_range_score(index, GENRE_RANGE, in_range_diff=False, base_score=20,
                                                           out_range_score=1) * show_multiplier
    show_score = {}
    for show in unwatch_shows:
        rating = show.rating if show.rating is not None else SHOW_DEFAULT_RATING
        show_multiplier = rating / 10 if SHOW_MULTIPLIER else 1
        show_score[show] = 0
        for cast in [a for a in show.actors if a.tag in cast_score]:
            show_score[show] += cast_score[cast.tag]

        for genre in [g for g in show.genres if g.tag in genre_score]:
            show_score[show] += genre_score[genre.tag]

        show_score[show] *= show_multiplier
    recommend = sorted(show_score.items(), key=operator.itemgetter(1), reverse=True)[:PLAYLIST_SIZE]
    return [r[0] for r in recommend]


def calculate_range_score(position, in_range, in_range_diff=True, in_range_diff_multiplier=1.0, base_score=0.1,
                          out_range_score=0.1):
    if in_range <= 0:
        return base_score

    if position >= in_range:
        return base_score + out_range_score

    if in_range_diff:
        return base_score + (in_range - position) * in_range_diff_multiplier
    else:
        return base_score + in_range


if __name__ == "__main__":
    main()
