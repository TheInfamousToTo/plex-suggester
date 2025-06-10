import os
import random
import requests
from flask import Flask, render_template
from plexapi.server import PlexServer
import wikipediaapi

app = Flask(__name__)

# Plex config from environment
PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("PLEX_LIBRARY", "Movies")

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='PlexMovieSuggester/1.0 (your-email@example.com)',  # Replace with your contact info
    language='en'
)

def get_wikipedia_actor_image(actor_name):
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={actor_name}&prop=pageimages&format=json&pithumbsize=200"
        resp = requests.get(url).json()
        pages = resp.get("query", {}).get("pages", {})
        for pageid, pagedata in pages.items():
            thumbnail = pagedata.get("thumbnail", {})
            if thumbnail:
                return thumbnail.get("source")
        return None
    except Exception:
        return None

def get_random_movie():
    if not PLEX_URL or not PLEX_TOKEN:
        return "⚠️ Please set PLEX_URL and PLEX_TOKEN environment variables.", None

    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        server_id = plex.machineIdentifier
        movies = plex.library.section(LIBRARY_NAME).search(unwatched=True)
        if not movies:
            return "✅ No unwatched movies found!", None

        movie = random.choice(movies)

        # Poster URL with token
        movie.poster_url = f"{PLEX_URL}{movie.thumb}?X-Plex-Token={PLEX_TOKEN}" if movie.thumb else None

        # Top 5 cast with images (plex thumb or Wikipedia fallback)
        cast = []
        for actor in movie.roles[:5]:
            if actor.thumb:
                actor_thumb = f"{PLEX_URL}{actor.thumb}?X-Plex-Token={PLEX_TOKEN}"
            else:
                actor_thumb = get_wikipedia_actor_image(actor.tag)
            cast.append({
                "name": actor.tag,
                "thumb": actor_thumb
            })
        movie.cast = cast

        # Trailer URL (if available)
        try:
            trailer = next((e for e in movie.extras() if 'trailer' in e.type.lower()), None)
            movie.trailer_url = trailer.url if trailer else None
        except Exception:
            movie.trailer_url = None

        # Watch on Plex URL
        movie.watch_url = f"{PLEX_URL}/web/index.html#!/server/{server_id}/details?key={movie.key}"

        return None, movie

    except Exception as e:
        return f"❌ Error: {e}", None


@app.route("/")
def home():
    error, movie = get_random_movie()
    return render_template("index.html", error=error, movie=movie)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
