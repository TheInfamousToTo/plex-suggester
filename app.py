import os
import random
import re
import requests
import urllib.parse
import jwt
import datetime
from functools import wraps
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from plexapi.server import PlexServer
import wikipediaapi
from io import BytesIO

app = Flask(__name__)

# JWT Secret Key - should be set via environment variable in production
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

# Enable sessions for caching
app.secret_key = os.getenv("FLASK_SECRET_KEY", JWT_SECRET_KEY)

# Backend API configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "https://plex-like.satrawi.cc")

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

def get_backend_jwt_token(plex_token):
    """Get JWT token from backend service using Plex token"""
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/auth/plex",
            json={"plex_token": plex_token},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        return None
    except Exception as e:
        print(f"Failed to get backend JWT token: {e}")
        return None

def require_jwt_auth(f):
    """Decorator to require JWT authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header with Bearer token required'}), 401
        
        try:
            # Extract token
            token = auth_header.split(' ')[1]
            
            # Verify token (basic verification - the backend will do the real verification)
            # We mainly use this to ensure the frontend is sending a proper token format
            if not token or len(token) < 10:
                raise ValueError("Invalid token format")
            
            # Pass through to the actual function
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token'}), 401
    
    return decorated_function

def make_backend_request(method, endpoint, headers=None, json_data=None, params=None):
    """Make authenticated request to backend API"""
    url = f"{BACKEND_API_URL}{endpoint}"
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            json=json_data,
            params=params,
            timeout=10
        )
        return response
    except Exception as e:
        print(f"Backend request failed: {e}")
        return None

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

def get_random_movie_lightweight(library_name=None, plex_token=None):
    """Optimized version for match rooms - only gets essential data"""
    # Use provided token or fallback to environment variable
    token = plex_token or PLEX_TOKEN
    if not PLEX_URL or not token:
        return "⚠️ Please set PLEX_URL and PLEX_TOKEN environment variables.", None

    try:
        plex = PlexServer(PLEX_URL, token)
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

        # Only get essential data - no expensive operations
        # Poster URL with token or fallback
        if getattr(item, "thumb", None):
            # Use proxy route instead of direct Plex URL
            item.poster_url = f"/poster{item.thumb}"
        else:
            item.poster_url = "https://avatars.githubusercontent.com/u/72304665?v=4"

        # Watch on Plex URL
        try:
            item.watch_url = f"{PLEX_URL}/web/index.html#!/server/{plex.machineIdentifier}/details?key=/library/metadata/{item.ratingKey}"
        except Exception:
            item.watch_url = None

        return None, item

    except Exception as e:
        return f"❌ Error getting random movie: {str(e)}", None

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

# ==================== MOVIE MATCH API ENDPOINTS ====================

@app.route("/api/match/rooms", methods=["POST"])
@token_required
def create_match_room():
    """Create a new movie matching room using backend service"""
    try:
        data = request.get_json()
        room_name = data.get('name', 'Movie Night')
        library_filter = data.get('library', 'Movies')
        min_participants = data.get('min_participants', 2)
        creator_username = data.get('creator_username', 'Anonymous')
        
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        # Create room data for backend
        room_data = {
            'name': room_name,
            'library_filter': library_filter,
            'min_participants': min_participants,
            'creator_username': creator_username
        }
        
        # Make request to backend
        response = make_backend_request(
            'POST',
            '/match/rooms',
            headers={'Authorization': f'Bearer {backend_token}'},
            json_data=room_data
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Failed to create room') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to create room: {str(e)}'}), 500

@app.route("/api/match/rooms", methods=["GET"])
@token_required  
def list_match_rooms():
    """List all active movie matching rooms using backend service"""
    try:
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        # Make request to backend
        response = make_backend_request(
            'GET',
            '/match/rooms',
            headers={'Authorization': f'Bearer {backend_token}'}
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Failed to list rooms') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to list rooms: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>/join", methods=["POST"])
@token_required
def join_match_room(room_id):
    """Join a movie matching room using backend service"""
    try:
        data = request.get_json()
        username = data.get('username', 'Anonymous')
        
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        join_data = {
            'username': username
        }
        
        response = make_backend_request(
            'POST',
            f'/match/rooms/{room_id}/join',
            headers={'Authorization': f'Bearer {backend_token}'},
            json_data=join_data
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Failed to join room') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to join room: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>", methods=["GET"])
@token_required
def get_match_room(room_id):
    """Get room information using backend service"""
    try:
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        response = make_backend_request(
            'GET',
            f'/match/rooms/{room_id}',
            headers={'Authorization': f'Bearer {backend_token}'}
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Room not found') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to get room info: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>/next-movie", methods=["GET"])
@token_required
def get_next_movie_for_match(room_id):
    """Get next movie for user to swipe on - optimized version"""
    try:
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        # Use session-based caching for user swipes to reduce API calls
        from flask import session
        cache_key = f"swipes_{room_id}_{hash(request.plex_token)}"
        
        # Check if we have cached swipes (refresh every 30 seconds)
        import time
        current_time = time.time()
        cached_data = session.get(cache_key)
        cache_valid = (cached_data and 
                      isinstance(cached_data, dict) and 
                      'timestamp' in cached_data and 
                      current_time - cached_data['timestamp'] < 30)
        
        if cache_valid:
            swiped_movies = set(cached_data['swiped_movies'])
            library_name = cached_data['library_name']
        else:
            # Fetch both room info and user swipes
            import concurrent.futures
            
            def get_swipes():
                response = make_backend_request(
                    'GET',
                    f'/match/rooms/{room_id}/user-swipes',
                    headers={'Authorization': f'Bearer {backend_token}'}
                )
                if response and response.status_code == 200:
                    return set(response.json().get('swiped_movies', []))
                return set()
            
            def get_room():
                response = make_backend_request(
                    'GET',
                    f'/match/rooms/{room_id}',
                    headers={'Authorization': f'Bearer {backend_token}'}
                )
                if response and response.status_code == 200:
                    return response.json().get('library_filter', 'Movies')
                return 'Movies'
            
            # Execute both requests in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                swipes_future = executor.submit(get_swipes)
                room_future = executor.submit(get_room)
                
                swiped_movies = swipes_future.result()
                library_name = room_future.result()
            
            # Cache the results
            session[cache_key] = {
                'swiped_movies': list(swiped_movies),
                'library_name': library_name,
                'timestamp': current_time
            }
        
        # Try up to 3 times to find an unswiped movie (reduced from 5)
        for _ in range(3):
            error, movie = get_random_movie_lightweight(library_name, request.plex_token)
            if error:
                continue
            
            movie_id = str(movie.ratingKey)
            if movie_id not in swiped_movies:
                # Convert movie object to dictionary with minimal data
                movie_data = {
                    'id': movie_id,
                    'title': getattr(movie, 'title', ''),
                    'year': getattr(movie, 'year', ''),
                    'summary': getattr(movie, 'summary', ''),
                    'poster_url': getattr(movie, 'poster_url', ''),
                }
                return jsonify({'movie': movie_data})
        
        # No more movies found
        return jsonify({'message': 'No more movies to swipe'}), 204
        
    except Exception as e:
        return jsonify({'error': f'Failed to get next movie: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>/swipe", methods=["POST"])
@token_required
def swipe_movie_in_room(room_id):
    """Record a swipe on a movie using backend service"""
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        movie_title = data.get('movie_title', '')
        movie_year = data.get('movie_year')
        direction = data.get('direction')  # 'left', 'right', 'super'
        
        if not all([movie_id, direction]):
            return jsonify({'error': 'movie_id and direction required'}), 400
        
        if direction not in ['left', 'right', 'super']:
            return jsonify({'error': 'direction must be left, right, or super'}), 400
        
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        swipe_data = {
            'movie_id': movie_id,
            'movie_title': movie_title,
            'movie_year': movie_year,
            'direction': direction
        }
        
        response = make_backend_request(
            'POST',
            f'/match/rooms/{room_id}/swipe',
            headers={'Authorization': f'Bearer {backend_token}'},
            json_data=swipe_data
        )
        
        if response and response.status_code == 200:
            # Invalidate the cache for this user/room since they swiped
            from flask import session
            cache_key = f"swipes_{room_id}_{hash(request.plex_token)}"
            if cache_key in session:
                del session[cache_key]
            
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Failed to record swipe') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to record swipe: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>/matches", methods=["GET"])
@token_required
def get_room_matches(room_id):
    """Get current matches for the room using backend service"""
    try:
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        response = make_backend_request(
            'GET',
            f'/match/rooms/{room_id}/matches',
            headers={'Authorization': f'Bearer {backend_token}'}
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = response.json().get('detail', 'Failed to get matches') if response else 'Backend unavailable'
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to get matches: {str(e)}'}), 500

@app.route("/api/match/rooms/<room_id>/movies/<int:count>", methods=["GET"])
@token_required
def get_multiple_movies_for_match(room_id, count):
    """Get multiple movies for matching room - super fast batch implementation"""
    try:
        # Limit count to prevent abuse
        if count > 10:
            count = 10
        if count < 1:
            count = 1
            
        # Get backend JWT token
        backend_token = get_backend_jwt_token(request.plex_token)
        if not backend_token:
            return jsonify({'error': 'Failed to authenticate with backend'}), 401
        
        # Use session-based caching for batch requests too
        from flask import session
        import time
        cache_key = f"swipes_{room_id}_{hash(request.plex_token)}"
        current_time = time.time()
        cached_data = session.get(cache_key)
        cache_valid = (cached_data and 
                      isinstance(cached_data, dict) and 
                      'timestamp' in cached_data and 
                      current_time - cached_data['timestamp'] < 30)
        
        if cache_valid:
            swiped_movies = set(cached_data['swiped_movies'])
            library_name = cached_data['library_name']
        else:
            # Fetch user swipes and room info in parallel
            import concurrent.futures
            
            def get_swiped_movies():
                response = make_backend_request(
                    'GET',
                    f'/match/rooms/{room_id}/user-swipes',
                    headers={'Authorization': f'Bearer {backend_token}'}
                )
                if response and response.status_code == 200:
                    return set(response.json().get('swiped_movies', []))
                return set()
            
            def get_room_info():
                response = make_backend_request(
                    'GET',
                    f'/match/rooms/{room_id}',
                    headers={'Authorization': f'Bearer {backend_token}'}
                )
                if response and response.status_code == 200:
                    return response.json().get('library_filter', 'Movies')
                return 'Movies'
            
            # Execute both requests concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                swiped_future = executor.submit(get_swiped_movies)
                room_future = executor.submit(get_room_info)
                
                swiped_movies = swiped_future.result()
                library_name = room_future.result()
            
            # Cache the results
            session[cache_key] = {
                'swiped_movies': list(swiped_movies),
                'library_name': library_name,
                'timestamp': current_time
            }
        
        # Generate movies quickly
        movies = []
        attempts = 0
        max_attempts = count * 2  # Reduced attempts for speed
        
        while len(movies) < count and attempts < max_attempts:
            attempts += 1
            error, movie = get_random_movie_lightweight(library_name, request.plex_token)
            if error:
                continue
            
            movie_id = str(movie.ratingKey)
            if movie_id not in swiped_movies:
                # Minimal movie data for speed
                movie_data = {
                    'id': movie_id,
                    'title': getattr(movie, 'title', ''),
                    'year': getattr(movie, 'year', ''),
                    'summary': getattr(movie, 'summary', ''),
                    'poster_url': getattr(movie, 'poster_url', ''),
                }
                movies.append(movie_data)
                swiped_movies.add(movie_id)  # Prevent duplicates in same batch
        
        return jsonify({'movies': movies})
            
    except Exception as e:
        return jsonify({'error': f'Failed to get movies: {str(e)}'}), 500

# ==================== END MOVIE MATCH API ENDPOINTS ====================

# ==================== WATCHLIST & WATCH TRACKING API ENDPOINTS ====================

@app.route("/api/watchlist/add", methods=["POST"])
@require_jwt_auth
def add_to_watchlist():
    """Add a movie to user's watchlist via backend API"""
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        movie_title = data.get('movie_title')
        
        if not movie_id or not movie_title:
            return jsonify({'error': 'movie_id and movie_title are required'}), 400
        
        # Get JWT token from request headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        jwt_token = auth_header.split(' ')[1]
        
        # Forward to backend API
        response = requests.post(
            f"{BACKEND_API_URL}/api/watchlist/add",
            json={
                'movie_id': movie_id,
                'movie_title': movie_title
            },
            headers={
                'Authorization': f'Bearer {jwt_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Backend API error'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Failed to add to watchlist: {str(e)}'}), 500

@app.route("/api/watch/mark", methods=["POST"])
@require_jwt_auth
def mark_as_watched():
    """Mark a movie as watched via backend API"""
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        movie_title = data.get('movie_title')
        
        if not movie_id or not movie_title:
            return jsonify({'error': 'movie_id and movie_title are required'}), 400
        
        # Get JWT token from request headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        jwt_token = auth_header.split(' ')[1]
        
        # Forward to backend API
        response = requests.post(
            f"{BACKEND_API_URL}/api/watch/mark",
            json={
                'movie_id': movie_id,
                'movie_title': movie_title
            },
            headers={
                'Authorization': f'Bearer {jwt_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Backend API error'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Failed to mark as watched: {str(e)}'}), 500

@app.route("/api/watchlist", methods=["GET"])
@require_jwt_auth
def get_watchlist():
    """Get user's watchlist via backend API"""
    try:
        # Get JWT token from request headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        jwt_token = auth_header.split(' ')[1]
        
        # Forward to backend API
        response = requests.get(
            f"{BACKEND_API_URL}/api/watchlist",
            headers={
                'Authorization': f'Bearer {jwt_token}'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Backend API error'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Failed to get watchlist: {str(e)}'}), 500

@app.route("/api/watch/history", methods=["GET"])
@require_jwt_auth
def get_watch_history():
    """Get user's watch history via backend API"""
    try:
        # Get JWT token from request headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        jwt_token = auth_header.split(' ')[1]
        
        # Forward to backend API
        response = requests.get(
            f"{BACKEND_API_URL}/api/watch/history",
            headers={
                'Authorization': f'Bearer {jwt_token}'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Backend API error'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Failed to get watch history: {str(e)}'}), 500

# ==================== END WATCHLIST & WATCH TRACKING ====================

@app.route("/", methods=["GET"])
def home():
    selected_library = request.args.get("library") or LIBRARY_NAME
    # Use environment token if available for backward compatibility
    token = PLEX_TOKEN
    libraries = get_plex_libraries(token)
    error, movie = get_random_movie(selected_library, token)
    return render_template("index.html", error=error, movie=movie, libraries=libraries, selected_library=selected_library, has_env_token=bool(PLEX_TOKEN), plex_token=PLEX_TOKEN if PLEX_TOKEN else "")

@app.route("/match")
def movie_match():
    """Serve the movie matching interface"""
    return render_template("match.html", 
                         has_env_token=bool(PLEX_TOKEN), 
                         plex_token=PLEX_TOKEN if PLEX_TOKEN else "",
                         backend_api_url=BACKEND_API_URL)

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
        # Use session for connection pooling and faster requests
        session = requests.Session()
        resp = session.get(plex_url, timeout=3, stream=True)  # Reduced timeout, use streaming
        resp.raise_for_status()
        
        # Create response with caching headers for better performance
        from flask import Response
        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk
        
        response = Response(generate(), mimetype=resp.headers.get("Content-Type", "image/jpeg"))
        
        # Add aggressive caching headers
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
        response.headers['ETag'] = f'"{hash(item_key)}"'  # Simple ETag
        
        # Check if client has cached version
        if request.headers.get('If-None-Match') == response.headers['ETag']:
            return '', 304  # Not Modified
        
        return response
        
    except Exception as e:
        print(f"Poster proxy error: {e}")
        # Return a fast fallback response with caching
        from flask import Response
        fallback_response = Response(
            b'', 
            status=302,
            headers={'Location': 'https://via.placeholder.com/250x375/333/e5a00d?text=No+Poster'}
        )
        return fallback_response


@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return send_from_directory('assets', 'favicon.ico', mimetype='image/x-icon')

@app.route('/icon.png')
def icon():
    """Serve the icon"""
    return send_from_directory('assets', 'icon.png', mimetype='image/png')

@app.route('/logo.png')
def logo():
    """Serve the logo"""
    return send_from_directory('assets', 'logo.png', mimetype='image/png')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
