# Plex Movie Suggester

A simple Flask app that connects to your Plex server and suggests a random unwatched movie, TV show, anime, or other video from your Plex library.  
It displays posters, cast info, and trailer links, with a sleek Plex-themed UI and a dropdown to select your library.

## Features

- Suggests a random unwatched movie, show, anime, or other video from your Plex library
- Shows poster and summary (with fallback images if missing)
- Displays top cast with images (uses Plex or Wikipedia, with fallback)
- Links to trailer and direct "Watch on Plex"
- "Suggest Another" button keeps your library selection
- Dropdown menu to select any video library (Movies, TV, Anime, etc.)
- Responsive, Plex-inspired UI

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
- Allows refreshing for a new suggestion, keeping your library selection.

## Troubleshooting

- Ensure your Plex server is accessible from where you run the app.
- Double-check your Plex token and library name.
- Check logs for errors if the app fails to connect or display items.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## How to update GitHub and Docker Hub with your new README

### 1. Update on GitHub

1. **Commit and push your changes:**
    ```bash
    git add README.md
    git commit -m "Update README with new UI and features"
    git push
    ```
   This updates the README on your GitHub repository.

### 2. Update on Docker Hub

- **If you use automated builds (linked to GitHub):**
  - The README on Docker Hub will update automatically after your next build (triggered by a push or manually).
  - You can trigger a build by pushing a new tag or clicking "Trigger" in Docker Hub's build settings.

- **If you push images manually:**
  1. Go to your repository on Docker Hub.
  2. Click the "Edit" button on the repository page.
  3. Copy the contents of your updated `README.md` and paste it into the "Full Description" field.
  4. Save the changes.

**Tip:**  
Automated builds are recommended for keeping Docker Hub in sync with GitHub.

---