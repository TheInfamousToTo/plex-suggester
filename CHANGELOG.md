# Changelog

All notable changes to the Plex Suggester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.2] - 2025-07-06

### Added
- **Favicon Support** - Professional branding with new Plex-style logo
  - Added new Plex-style logo with orange arrow design
  - Implemented favicon routes in Flask app (`/favicon.ico`, `/icon.png`, `/logo.png`)
  - Updated HTML templates with proper favicon links for all browsers
  - Added support for Apple touch icons and legacy browser compatibility
  - Improved user experience with branded favicon in browser tabs

### Technical Improvements
- Enhanced Flask routing with proper MIME types for favicon assets
- Added `send_from_directory` functionality for static asset serving
- Cross-browser favicon compatibility with multiple format support

## [1.7.0] - 2025-06-27

### Added
- **Enhanced Plex Match Actions** - Direct integration with Plex functionality
  - "Add to Plex Watchlist" button for matched movies
  - "Mark as Watched" button to track viewing progress
  - "Open in Plex" button for direct app/web access
  - Smart button states and visual feedback
- **Real-time Match Notifications** - Instant alerts for new matches
  - Popup notifications when new matches are found
  - Auto-polling every 10 seconds while in match rooms
  - Dismissible notifications with smooth animations
  - Optional notification sound for better UX
- **Enhanced Match Display** - Richer match information
  - Movie posters in match cards
  - Movie summaries with intelligent truncation
  - Improved visual design with better spacing
  - Action buttons with hover effects and state management
- **Backend API Extensions** - New endpoints for enhanced functionality
  - `/api/watchlist/add` - Add movies to user watchlist
  - `/api/watch/mark` - Mark movies as watched
  - `/api/watchlist` - Get user's watchlist
  - `/api/watch/history` - Get user's watch history
  - Database tables for watchlist and watch tracking

### Changed
- Updated match cards with modern layout and enhanced information display
- Improved notification system with better visual feedback
- Enhanced error handling and user feedback throughout
- Better state management for match room sessions

### Technical Details
- Added PostgreSQL tables: `watchlist` and `watch_history`
- Implemented JWT-authenticated API endpoints for watch tracking
- Added real-time polling system for match notifications
- Enhanced frontend state management for notifications
- Added database migration script for new tables

## [1.6.0] - 2025-06-27

### Added
- **Plex Match Feature** - Tinder-style movie matching for group viewing decisions
  - Create and join match rooms with custom names and settings
  - Swipe left (pass), right (like), or super like movies with animated buttons
  - Real-time match detection when multiple users like the same movie
  - Room management with participant tracking and expiration handling
  - Active rooms grid display with detailed room information
- **FastAPI Backend Integration** - Seamless integration with plex-backend service
  - JWT-based authentication for secure match room operations
  - RESTful API endpoints for room creation, joining, and movie fetching
  - Session-based caching for improved performance
  - Lightweight movie data fetching optimized for match scenarios
- **Performance Optimizations** - Ultra-fast loading with intelligent caching
  - Movie queue preloading system (3-5 movies ahead)
  - Batch movie fetching endpoint for faster preloading
  - Poster image preloading and in-memory caching
  - Optimized poster proxy with ETag support and aggressive caching
  - Asynchronous swipe processing for instant UI response
- **Enhanced UI/UX** - Mobile-first design with smooth animations
  - Responsive match room interface with Plex-themed styling
  - Smooth swipe animations and loading indicators
  - Touch-optimized buttons with proper target sizes
  - Glass morphism design language consistent with main app
  - Loading states and error handling throughout

### Changed
- Updated main navigation to include "Movie Match" button
- Improved JWT token handling across frontend and backend
- Enhanced error messaging and user feedback systems
- Optimized API request patterns to reduce server load

### Technical Details
- Added `/api/match/*` route handlers in Flask frontend
- Implemented poster caching with streaming and ETag support
- Added session-based user swipe caching to reduce API calls
- Created lightweight movie fetching function for match mode
- Integrated with plex-backend match endpoints seamlessly

## [1.5.0] - 2024-12-XX

### Added
- **Hybrid Authentication System** - supports both environment variables and web-based Plex token configuration
- **Seamless Integration** - automatically handles JWT authentication with external services
- **Settings Management** - built-in settings modal for secure Plex token management
- **Enhanced UI/UX** - settings button repositioned with icon-only design
- **Bearer Token API** - enhanced security for API requests
- **Improved Security** - server-side Plex token validation with JWT issuance

### Changed
- Settings button now uses elegant icon-only design next to dropdown
- Fixed blur overlay gaps for seamless full-screen coverage
- Enhanced responsive design for all devices
- Maintained backward compatibility with existing Docker deployments

## [1.4.1] - 2024-XX-XX

### Changed
- Enhanced button layout with trailer button alongside other action buttons
- Consistent Plex theming for trailer button with brown/gold color scheme
- Improved UI consistency across all action buttons

## [1.4.0] - 2024-XX-XX

### Added
- **Modern UI Overhaul** - complete visual redesign with glass morphism effects
- **Watch Count Tracking** - track user engagement with eye icon counters
- **Enhanced Cast Section** - modern grid layout with interactive cards
- **External Trailer Support** - YouTube/internet trailer integration
- **GitHub Integration** - quick repository access via GitHub icon

### Changed
- Complete typography overhaul with Inter + Poppins fonts
- Enhanced animations and gradient effects throughout
- Better responsive design for all screen sizes

## [1.3.2] - 2024-XX-XX

### Added
- **Plex Poster Proxy** - posters always visible even behind reverse proxies
- Backend poster fetching and serving for universal accessibility

### Changed
- Version bump to 1.3.2

## [1.3.0] - 2024-XX-XX

### Added
- **Like/Dislike Functionality** - user engagement tracking
- **JWT Authentication** - secure API access for user actions
- **Real-time Updates** - like/dislike counts update dynamically
- **Frontend User ID** - persistent user identification in browser

### Changed
- Cleaner UI without emoji buttons
- Enhanced security with JWT implementation
- No JWT secrets exposed to frontend

## [1.2.0] - 2024-XX-XX

### Added
- Basic movie suggestion functionality
- Plex server integration
- Responsive web interface

### Features
- Random unwatched movie suggestions
- Library filtering (Movies, TV Shows, Anime)
- Basic poster and metadata display
- "Watch on Plex" integration

---

## Upcoming Features
- Real-time notifications for new matches
- Advanced filtering options for match rooms
- Integration with Plex watchlist for matched movies
- Export match results and statistics
- Mobile app companion (planned)
