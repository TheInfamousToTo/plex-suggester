# Plex Movie Suggester

A simple Flask app that connects to your Plex server and suggests a random unwatched movie from your library.  
It displays movie posters, cast info, and trailer links, with a sleek Plex-themed UI.

## Features

- Suggests a random unwatched movie from your Plex library
- Shows movie poster and summary
- Displays top cast with images
- Links to movie trailer and direct "Watch on Plex"
- Refresh button to suggest another movie
- Configurable via environment variables

## Environment Variables

- `PLEX_URL`: Your Plex server URL (e.g. `http://192.168.31.81:32400`)
- `PLEX_TOKEN`: Your Plex authentication token
- `PLEX_LIBRARY`: Name of the Plex library to suggest from (default: "Movies")

## Usage

### Running with Docker

```bash
docker run -d -p 5000:5000 \
  -e PLEX_URL="http://your-plex-server:32400" \
  -e PLEX_TOKEN="your-plex-token" \
  -e PLEX_LIBRARY="Movies" \
  theinfamoustoto/plex-suggester:latest
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
- Fetches the specified library (default: "Movies").
- Picks a random unwatched movie and displays its details.
- Allows refreshing for a new suggestion.

## Troubleshooting

- Ensure your Plex server is accessible from where you run the app.
- Double-check your Plex token and library name.
- Check logs for errors if the app fails to connect or display movies.

## License

MIT License. See [LICENSE](LICENSE) for details.