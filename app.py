import os
import random
import re
import requests
from flask import Flask, render_template, request
from plexapi.server import PlexServer
import wikipediaapi

app = Flask(__name__)

# Plex config from environment
PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("PLEX_LIBRARY", "Movies")

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='PlexMovieSuggester/1.0 (bees751@hotmail.com)',  # Replace with your contact info
    language='en'
)

def get_wikipedia_actor_image(actor_name):
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={actor_name}&prop=pageimages&format=json&pithumbsize=200"
        resp = requests.get(url, timeout=2).json()
        pages = resp.get("query", {}).get("pages", {})
        for pageid, pagedata in pages.items():
            thumbnail = pagedata.get("thumbnail", {})
            if thumbnail:
                return thumbnail.get("source")
    except Exception:
        pass
    return None  # Always return None if anything fails

def get_imdb_actor_image(actor_name):
    """
    Try to fetch actor image from IMDB via DuckDuckGo image search as a workaround.
    Returns image URL or None.
    """
    try:
        # Use DuckDuckGo image search as a simple, free workaround (not official IMDB API)
        search_url = f"https://duckduckgo.com/?q={actor_name}+imdb&iax=images&ia=images"
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(search_url, headers=headers, timeout=3).text
        # Find first image URL in the HTML (very basic, not robust)
        match = re.search(r'"image":"(https://[^"]+?)"', html)
        if match:
            return match.group(1).replace("\\/", "/")
    except Exception:
        pass
    return None

def get_plex_libraries():
    if not PLEX_URL or not PLEX_TOKEN:
        return []
    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        # Include all video types (movie, show, etc.)
        return [
            {"title": section.title, "type": section.type}
            for section in plex.library.sections()
            if section.type in ("movie", "show", "anime", "other", "artist")
        ]
    except Exception:
        return []

def get_random_movie(library_name=None):
    if not PLEX_URL or not PLEX_TOKEN:
        return "⚠️ Please set PLEX_URL and PLEX_TOKEN environment variables.", None

    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        server_id = plex.machineIdentifier
        lib_name = library_name or LIBRARY_NAME
        section = plex.library.section(lib_name)
        # Suggest a random unwatched movie or show
        if section.type == "movie":
            items = section.search(unwatched=True)
        elif section.type in ("show", "anime"):
            # Suggest a random show with unwatched episodes
            shows = section.search()
            items = [show for show in shows if any(not ep.isWatched for ep in show.episodes())]
        else:
            items = section.search(unwatched=True)

        if not items:
            return "✅ No unwatched items found!", None

        item = random.choice(items)

        # Poster URL with token or fallback
        if getattr(item, "thumb", None):
            item.poster_url = f"{PLEX_URL}{item.thumb}?X-Plex-Token={PLEX_TOKEN}"
        else:
            item.poster_url = "https://avatars.githubusercontent.com/u/72304665?v=4"

        # Top 5 cast with images (Plex thumb, then IMDB, then Wikipedia, else always placeholder)
        cast = []
        for actor in getattr(item, "roles", [])[:5]:
            # 1. Try Plex thumb
            if getattr(actor, "thumb", None):
                actor_thumb = f"{PLEX_URL}{actor.thumb}?X-Plex-Token={PLEX_TOKEN}"
            else:
                # 2. Try IMDB (via DuckDuckGo image search)
                actor_thumb = get_imdb_actor_image(actor.tag)
                if not actor_thumb:
                    # 3. Try Wikipedia
                    actor_thumb = get_wikipedia_actor_image(actor.tag)
                # 4. Fallback to placeholder if all else fails
                if not actor_thumb:
                    actor_thumb = "https://avatars.githubusercontent.com/u/72304665?v=4"
            cast.append({
                "name": actor.tag,
                "thumb": actor_thumb
            })
        item.cast = cast

        # Trailer URL (if available)
        try:
            trailer = next((e for e in getattr(item, "extras", lambda: [])() if 'trailer' in e.type.lower()), None)
            item.trailer_url = trailer.url if trailer else None
        except Exception:
            item.trailer_url = None

        # Watch on Plex URL
        item.watch_url = f"{PLEX_URL}/web/index.html#!/server/{server_id}/details?key={item.key}"

        # Add summary fallback
        if not getattr(item, "summary", None):
            item.summary = "No summary available."

        # Add year fallback
        if not getattr(item, "year", None):
            item.year = ""

        # Add title fallback
        if not getattr(item, "title", None):
            item.title = "Untitled"

        return None, item

    except Exception as e:
        return f"❌ Error: {e}", None


@app.route("/", methods=["GET"])
def home():
    selected_library = request.args.get("library") or LIBRARY_NAME
    libraries = get_plex_libraries()
    error, movie = get_random_movie(selected_library)
    return render_template("index.html", error=error, movie=movie, libraries=libraries, selected_library=selected_library)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
