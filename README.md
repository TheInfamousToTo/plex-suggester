![Plex Suggester Logo](assets/logo.png)

# Plex Movie Suggester

**Version 1.5.0**

A modern Flask app that connects to your Plex server and suggests a random unwatched movie, TV show, anime, or other video from your Plex library.  
Features a sleek, responsive Plex-themed UI with modern glass morphism design, interactive elements, and **secure JWT-based authentication**.

---

## 🚀 What's New in v1.5.0

- **Hybrid Authentication System:**  
  Supports both environment variable configuration (backward compatible) and web-based Plex token authentication.
- **Seamless Integration:**  
  Automatically handles JWT authentication with external like/dislike/watch backend services.
- **Settings Management:**  
  Built-in settings modal allows users to securely manage their Plex tokens when not using environment variables.
- **Enhanced UI/UX:**  
  Settings button repositioned next to dropdown as elegant icon-only design; fixed blur overlay gaps for seamless full-screen coverage; improved responsive design for all devices.
- **Bearer Token API:**  
  API requests use Bearer token authentication when required for enhanced security.
- **Improved Security:**  
  Plex tokens are validated server-side and JWT tokens are issued for secure API access to external services.
- **Backward Compatibility:**  
  Fully compatible with existing Docker deployments using environment variables.

---

## 🚀 What's New in v1.4.1

- **Enhanced Button Layout:**  
  Trailer button is now positioned alongside "Watch on Plex" and "Suggest Another" buttons for better user experience.
- **Consistent Plex Theming:**  
  Trailer button now uses the same brown/gold Plex color scheme as the rest of the interface.
- **Improved UI Consistency:**  
  All action buttons now follow the same design language and hover effects.

---

## 🚀 What's New in v1.4

- **Modern UI Overhaul:**  
  Complete visual redesign with glass morphism effects, modern typography (Inter + Poppins fonts), and enhanced animations.
- **Watch Count Tracking:**  
  Track how many users clicked "Watch on Plex" for each item with an eye icon counter.
- **Enhanced Cast Section:**  
  Modern grid layout with glass cards, improved hover effects, and better responsive design.
- **Improved Interactive Elements:**  
  Better buttons with gradient effects, shimmer animations, and consistent Plex theming.
- **GitHub Integration:**  
  Quick access to the project repository via a GitHub icon in the top-left corner.
- **External Trailer Support:**  
  Watch trailers directly from YouTube/internet sources instead of Plex-hosted trailers.
- **Enhanced Typography:**  
  Gradient text effects for titles and improved readability throughout.

---

## 🚀 What's New in v1.3.2

- **Plex Poster Proxy:**  
  Poster images are now always visible, even when the app is hosted behind a Cloudflare Tunnel or reverse proxy. Posters are fetched from your Plex server by the Flask backend and served to the frontend, so they are accessible from anywhere.
- **Version bump:**  
  Updated version to 1.3.2

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
- **Frontend User ID:**  
  Each user gets a unique, persistent ID stored in their browser. JWTs are generated server-side using this ID as the `sub` claim.
- **No Secret in Frontend:**  
  JWT secrets are never exposed to the frontend. All JWTs are issued by the backend.

---

## Features

- **Hybrid Authentication System** - supports both environment variables and web-based Plex token configuration
- **Automatic JWT Integration** - seamlessly handles authentication with external backend services
- **Built-in Settings Management** - configure Plex tokens directly in the web interface (when not using environment variables)
- **Enhanced UI/UX** - icon-only settings button positioned next to dropdown, improved blur overlay coverage
- Suggests a random unwatched movie, show, anime, or other video from your Plex library
- **Modern glass morphism UI** with enhanced visual effects and animations
- **Posters are always visible** (even when hosted behind a tunnel), thanks to backend proxying
- Shows poster and summary with beautiful card designs and gradient effects
- **Enhanced cast section** with modern grid layout and interactive cards
- Displays top cast with images (tries Plex, IMDB, AniList, Wikipedia, then fallback)
- Links to trailer and direct "Watch on Plex"
- **External trailer integration** with YouTube/internet sources for better accessibility
- **Watch count tracking** displays how many users clicked "Watch on Plex" for each item
- **GitHub integration** with quick access to project repository
- "Suggest Another" button with modern styling keeps your library selection
- **Custom dropdown menu** with Plex theming and smooth animations
- Dropdown menu to select any video library (Movies, TV, Anime, etc.)
- **Fully responsive design** optimized for mobile, tablet, and desktop
- **Like/Dislike buttons** with real-time counts and modern icons
- **Professional typography** using Inter and Poppins fonts
- **Bearer token API security** for authenticated requests to external services

## Environment Variables

- `PLEX_URL`: Your Plex server URL (e.g. `http://192.168.1.100:32400`) - **Required**
- `PLEX_TOKEN`: Your Plex authentication token - **Optional** (can be set via web interface)
- `PLEX_LIBRARY`: Default Plex library to suggest from (default: "Movies")
- `JWT_SECRET_KEY`: Secret key for JWT token signing (default provided, change in production)

**Note:** When `PLEX_TOKEN` is provided as an environment variable, the app will use it directly and skip the web-based authentication prompt. The app will still obtain JWT tokens for external API integrations (like like/dislike/watch functionality) as needed.

## Usage

### Running with Docker

```bash
docker run -d -p 5000:5000 \
  -e PLEX_URL="http://your-plex-server:32400" \
  -e PLEX_TOKEN="your-plex-token" \
  -e JWT_SECRET_KEY="your-secure-secret-key" \
  theinfamoustoto/plex-suggester:latest
```

**Note:** When `PLEX_TOKEN` is provided, the app will use it directly and users won't be prompted for authentication. The app will still handle JWT authentication for external service integrations automatically.

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
      PLEX_TOKEN: "your-plex-token"  # Recommended for Docker deployments
      PLEX_LIBRARY: "Movies"
      JWT_SECRET_KEY: "change-this-secret-key-in-production"
    restart: unless-stopped
```

Then start the service:

```bash
docker compose up -d
```

**Important:** Make sure to change the `JWT_SECRET_KEY` to a secure random value in production.

## Getting Your Plex Token

When you first access the application, you'll be prompted to enter your Plex token. Here's how to find it:

1. **Quick Method (via Plex Web):**
   - Open Plex in your web browser
   - Navigate to any movie or show
   - Click the "..." menu and select "Get Info"
   - Click "View XML" at the bottom
   - Look for `X-Plex-Token` in the URL

2. **Alternative Methods:**
   - Visit the [official Plex support guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
   - Use browser developer tools to inspect network requests to your Plex server

3. **Settings Management:**
   - Once entered, your token is stored securely in your browser
   - Use the Settings button in the app to update or clear your token
   - Tokens are validated against your Plex server before being accepted

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
    export JWT_SECRET_KEY="your-secure-secret-key"
    # PLEX_TOKEN is optional - you can set it via the web interface
    # export PLEX_TOKEN="your-plex-token"
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
- **How it Works** section updated to reflect modern UI and enhanced features
- **Like/Dislike/Watch API** with comprehensive tracking capabilities
- **Enhanced visual design** with glass morphism and modern animations
- **Always provides fallback images** for cast and posters with Plex-themed placeholders
- Allows refreshing for new suggestions while keeping library selection
- **Real-time engagement tracking** with like, dislike, and watch counts
- **Secure JWT authentication** for all user interactions
- **Modern responsive design** that works beautifully on all devices

## 🔑 Like/Dislike/Watch API (v1.3+)

- **Like a movie:**  
  `POST /like/<movie_id>`
- **Unlike a movie:**  
  `DELETE /like/<movie_id>`
- **Dislike a movie:**  
  `POST /dislike/<movie_id>`
- **Remove dislike:**  
  `DELETE /dislike/<movie_id>`
- **Track watch:**  
  `POST /watch/<movie_id>`
- **Get like count:**  
  `GET /like-count/<movie_id>`
- **Get dislike count:**  
  `GET /dislike-count/<movie_id>`
- **Get watch count:**  
  `GET /watch-count/<movie_id>`

## Troubleshooting

- Ensure your Plex server is accessible from where you run the app (the app must be able to reach Plex).
- Double-check your Plex token and library name.
- If posters are not visible, ensure the backend can reach your Plex server.
- Check logs for errors if the app fails to connect or display items.
- **For like/dislike/watch functionality:** If these features return 401 errors, ensure that:
  - The external backend service (`https://plex-like.satrawi.cc` in the example) is running and accessible
  - Your Plex token is valid and can authenticate with the external backend
  - The JWT tokens are being obtained correctly (check browser console for authentication messages)

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
