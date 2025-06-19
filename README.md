![Plex Suggester Logo](assets/logo.png)

# Plex Movie Suggester 

**Version 1.3**

A simple Flask app that connects to your Plex server and suggests a random unwatched movie, TV show, anime, or other video from your Plex library.  
It displays posters, cast info (with robust fallback images), and trailer links, with a sleek Plex-themed UI and a dropdown to select your library.

---

## 🚀 What's New in v1.3

- **Like/Dislike Functionality:**  
  Users can now like or dislike movies and shows.  
  - Like/Dislike counts are displayed and update in real time.
- **Dislike Support:**  
  Dislike button and count added.
- **JWT Authentication:**  
  All like/dislike actions require a valid JWT token.
- **UI Cleanup:**  
  Like/Dislike buttons no longer display emojis, for a cleaner look.

---

## Features

- Suggests a random unwatched movie, show, anime, or other video from your Plex library
- Shows poster and summary (with fallback images if missing)
- Displays top cast with images (tries Plex, IMDB, AniList, Wikipedia, then always a Plex logo fallback)
- Links to trailer and direct "Watch on Plex"
- "Suggest Another" button keeps your library selection
- Dropdown menu to select any video library (Movies, TV, Anime, etc.)
- Responsive, Plex-inspired UI
- **NEW:** Like/Dislike buttons with real-time counts (v1.3)

## Environment Variables

- `PLEX_URL`: Your Plex server URL (e.g. `http://192.168.1.100:32400`)
- `PLEX_TOKEN`: Your Plex authentication token
- `PLEX_LIBRARY`: Default Plex library to suggest from (default: "Movies")

## Usage

### Running with Docker

```bash
docker run -d -p 5000:5000 \
  -e PLEX_URL="http://your-plex-server:32400" \
  -e PLEX_TOKEN="your-plex-token" \
  -e PLEX_LIBRARY="Movies" \
  theinfamoustoto/plex-suggester:latest
```

### Running with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: "3.8"
services:
  plex-suggester:
    image: theinfamoustoto/plex-suggester:latest
    container_name: plex-suggester
    ports:
      - "5000:5000"
    environment:
      PLEX_URL: "http://your-plex-server:32400"
      PLEX_TOKEN: "your-plex-token"
      PLEX_LIBRARY: "Movies"
    restart: unless-stopped
```

Then start the service:

```bash
docker compose up -d
```

### Running Locally

1. Clone the repository:
    ```bash
    git clone https://github.com/theinfamoustoto/plex-suggester.git
    cd plex-suggester
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set environment variables:
    ```bash
    export PLEX_URL="http://your-plex-server:32400"
    export PLEX_TOKEN="your-plex-token"
    export PLEX_LIBRARY="Movies"
    ```

4. Run the app:
    ```bash
    python app.py
    ```
    The app will be available at [http://localhost:5000](http://localhost:5000).

## Docker

The provided [Dockerfile](Dockerfile) uses Python 3.11-slim and runs the app with Gunicorn for production readiness.

## Project Structure

- [`app.py`](app.py): Main Flask application.
- [`requirements.txt`](requirements.txt): Python dependencies.
- [`templates/`](templates/): HTML templates for the web UI.
- [`Dockerfile`](Dockerfile): Docker configuration.

## How it Works

- Connects to your Plex server using the provided URL and token.
- Fetches all video libraries (Movies, TV, Anime, etc.).
- Picks a random unwatched item from the selected library and displays its details.
- Always provides a fallback image for cast and posters.
- Allows refreshing for a new suggestion, keeping your library selection.
- **NEW in v1.3:** Users can like or dislike a movie/show, and see the current counts.

## 🔑 Like/Dislike API (v1.3+)

- **Like a movie:**  
  `POST /like/<movie_id>` (JWT required)
- **Unlike a movie:**  
  `DELETE /like/<movie_id>` (JWT required)
- **Dislike a movie:**  
  `POST /dislike/<movie_id>` (JWT required)
- **Remove dislike:**  
  `DELETE /dislike/<movie_id>` (JWT required)
- **Get like count:**  
  `GET /like-count/<movie_id>`
- **Get dislike count:**  
  `GET /dislike-count/<movie_id>`

## Troubleshooting

- Ensure your Plex server is accessible from where you run the app.
- Double-check your Plex token and library name.
- Check logs for errors if the app fails to connect or display items.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements

This project is inspired by the need for a simple, user-friendly way to discover new content in Plex libraries. Thanks to the Plex API for making this possible.

## Contact

For any questions or feedback, please open an issue or contact me on GitHub.

## Credits

This project was created by [theinfamoustoto]
