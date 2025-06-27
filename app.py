import os
import random
import re
import requests
import urllib.parse
import jwt
import datetime
from functools import wraps
from flask import Flask, render_template, request, send_file, jsonify
from plexapi.server import PlexServer
import wikipediaapi
from io import BytesIO

app = Flask(__name__)

# JWT Secret Key - should be set via environment variable in production
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

# Plex config from environment
PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("PLEX_LIBRARY", "Movies")

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='PlexMovieSuggester/1.0 (example@mail.com)',  # Replace with your contact info
    language='en'
)

def verify_plex_token(plex_token, plex_url=None):
    """Verify if the provided Plex token is valid"""
    try:
        url = plex_url or PLEX_URL
        if not url:
            return False
        plex = PlexServer(url, plex_token)
        # Try to access server info to verify token
        plex.machineIdentifier
        return True
    except Exception:
        return False

def generate_jwt_token(plex_token):
    """Generate JWT token for authenticated user"""
    payload = {
        'plex_token': plex_token,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Token format is invalid'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if payload is None:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        # Add plex_token to request context
        request.plex_token = payload['plex_token']
        return f(*args, **kwargs)
    
    return decorated

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

def get_anilist_actor_image(actor_name):
    """
    Try to fetch anime voice actor image from AniList GraphQL API.
    Returns image URL or None.
    """
    try:
        query = '''
        query ($search: String) {
          Staff(search: $search) {
            image {
              large
              medium
            }
          }
        }
        '''
        variables = {"search": actor_name}
        url = "https://graphql.anilist.co"
        response = requests.post(url, json={"query": query, "variables": variables}, timeout=3)
        data = response.json()
        image = (
            data.get("data", {})
                .get("Staff", {})
                .get("image", {})
                .get("large")
        )
        return image
    except Exception:
        return None

def get_plex_libraries(plex_token=None):
    # Use provided token or fallback to environment variable
    token = plex_token or PLEX_TOKEN
    if not PLEX_URL or not token:
        return []
    try:
        plex = PlexServer(PLEX_URL, token)
        # Include all video types (movie, show, etc.)
        return [
            {"title": section.title, "type": section.type}
            for section in plex.library.sections()
            if section.type in ("movie", "show", "anime", "other", "artist")
        ]
    except Exception:
        return []

def get_random_movie(library_name=None, plex_token=None):
    # Use provided token or fallback to environment variable
    token = plex_token or PLEX_TOKEN
    if not PLEX_URL or not token:
        return "⚠️ Please set PLEX_URL and PLEX_TOKEN environment variables.", None

    try:
        plex = PlexServer(PLEX_URL, token)
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
            # Use proxy route instead of direct Plex URL
            item.poster_url = f"/poster{item.thumb}"
        else:
            item.poster_url = "https://avatars.githubusercontent.com/u/72304665?v=4"

        # Top 5 cast with images (Plex thumb, then IMDB, then Wikipedia, else always placeholder)
        cast = []
        for actor in getattr(item, "roles", [])[:5]:
            # 1. Try Plex thumb
            if getattr(actor, "thumb", None):
                actor_thumb = f"{PLEX_URL}{actor.thumb}?X-Plex-Token={token}"
            else:
                # 2. Try IMDB (via DuckDuckGo image search)
                actor_thumb = get_imdb_actor_image(actor.tag)
                # 3. Try AniList (for anime/voice actors)
                if not actor_thumb:
                    actor_thumb = get_anilist_actor_image(actor.tag)
                # 4. Try Wikipedia
                if not actor_thumb:
                    actor_thumb = get_wikipedia_actor_image(actor.tag)
                # 5. Fallback to placeholder if all else fails
                if not actor_thumb:
                    actor_thumb = "https://avatars.githubusercontent.com/u/72304665?v=4"
            cast.append({
                "name": actor.tag,
                "thumb": actor_thumb
            })
        item.cast = cast

        # External Trailer URL (YouTube/TMDB)
        try:
            item.external_trailer_url = get_external_trailer_url(item.title, getattr(item, 'year', None))
        except Exception:
            item.external_trailer_url = None

        # Plex Trailer URL (if available) - keeping for compatibility
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

def get_external_trailer_url(title, year=None):
    """
    Try to fetch external trailer URL from YouTube or TMDB.
    Returns trailer URL or None.
    """
    try:
        # Clean title for search
        search_title = title.replace(":", "").replace("-", " ")
        if year:
            search_query = f"{search_title} {year} trailer"
        else:
            search_query = f"{search_title} trailer"
        
        # Try YouTube search via DuckDuckGo (simple approach)
        query = urllib.parse.quote_plus(search_query + " site:youtube.com")
        search_url = f"https://duckduckgo.com/html/?q={query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers, timeout=5)
        html = response.text
        
        # Look for YouTube URLs in the response
        youtube_pattern = r'https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        matches = re.findall(youtube_pattern, html)
        
        if matches:
            # Return the first YouTube URL found
            return f"https://www.youtube.com/watch?v={matches[0]}"
            
    except Exception:
        pass
    
    # Fallback: try a simple YouTube search URL
    try:
        if year:
            search_term = f"{title} {year} official trailer"
        else:
            search_term = f"{title} official trailer"
        
        search_term = urllib.parse.quote_plus(search_term)
        return f"https://www.youtube.com/results?search_query={search_term}"
    except Exception:
        pass
    
    return None


@app.route("/auth/plex", methods=["POST"])
def plex_auth():
    """Authenticate with Plex token and return JWT"""
    try:
        data = request.get_json()
        if not data or 'plex_token' not in data:
            return jsonify({'error': 'Plex token is required'}), 400
        
        plex_token = data['plex_token']
        
        # Verify the Plex token
        if not verify_plex_token(plex_token):
            return jsonify({'error': 'Invalid Plex token'}), 401
        
        # Generate JWT token
        jwt_token = generate_jwt_token(plex_token)
        
        return jsonify({
            'token': jwt_token,
            'message': 'Authentication successful'
        })
    
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@app.route("/api/libraries", methods=["GET"])
@token_required
def api_libraries():
    """Get Plex libraries for authenticated user"""
    try:
        libraries = get_plex_libraries(request.plex_token)
        return jsonify({'libraries': libraries})
    except Exception as e:
        return jsonify({'error': f'Failed to fetch libraries: {str(e)}'}), 500

@app.route("/api/suggest", methods=["GET"])
@token_required
def api_suggest():
    """Get random movie suggestion for authenticated user"""
    try:
        library_name = request.args.get("library")
        error, movie = get_random_movie(library_name, request.plex_token)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Convert movie object to dictionary for JSON response
        movie_data = {
            'title': getattr(movie, 'title', ''),
            'year': getattr(movie, 'year', ''),
            'summary': getattr(movie, 'summary', ''),
            'poster_url': getattr(movie, 'poster_url', ''),
            'watch_url': getattr(movie, 'watch_url', ''),
            'trailer_url': getattr(movie, 'trailer_url', ''),
            'external_trailer_url': getattr(movie, 'external_trailer_url', ''),
            'cast': getattr(movie, 'cast', [])
        }
        
        return jsonify({'movie': movie_data})
    except Exception as e:
        return jsonify({'error': f'Failed to get suggestion: {str(e)}'}), 500

@app.route("/", methods=["GET"])
def home():
    selected_library = request.args.get("library") or LIBRARY_NAME
    # Use environment token if available for backward compatibility
    token = PLEX_TOKEN
    libraries = get_plex_libraries(token)
    error, movie = get_random_movie(selected_library, token)
    return render_template("index.html", error=error, movie=movie, libraries=libraries, selected_library=selected_library, has_env_token=bool(PLEX_TOKEN), plex_token=PLEX_TOKEN if PLEX_TOKEN else "")

@app.route("/poster/<path:item_key>")
def proxy_poster(item_key):
    # item_key will be like 'library/metadata/12345/thumb'
    # Use environment token if available, otherwise require authentication
    if PLEX_TOKEN:
        token = PLEX_TOKEN
    else:
        # Require authentication if no environment token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return "Unauthorized", 401
        try:
            jwt_token = auth_header.split(" ")[1]
            payload = verify_jwt_token(jwt_token)
            if payload is None:
                return "Unauthorized", 401
            token = payload['plex_token']
        except (IndexError, KeyError):
            return "Unauthorized", 401
    
    plex_url = f"{PLEX_URL}/{item_key}?X-Plex-Token={token}"
    try:
        resp = requests.get(plex_url, timeout=5)
        resp.raise_for_status()
        return send_file(BytesIO(resp.content), mimetype=resp.headers.get("Content-Type", "image/jpeg"))
    except Exception:
        # fallback image
        return requests.get("https://via.placeholder.com/250x375?text=No+Image").content, 200, {'Content-Type': 'image/jpeg'}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
