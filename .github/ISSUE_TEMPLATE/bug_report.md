---
name: Bug report
about: Report a bug to help us improve Plex Suggester
title: '[BUG] '
labels: 'bug'
assignees: 'TheInfamousToTo'

---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

Steps to reproduce the behavior:

1. Go to '...'
2. Click on '....'
3. Enter configuration '....'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Environment Information

**Plex Suggester Setup:**

- Version: [e.g. 1.7.2]
- Deployment method: [Docker Compose/Docker Run/Python Direct]
- Container platform: [e.g. Docker Desktop, Portainer, Unraid]

**Plex Server Setup:**

- Plex version: [e.g. 1.32.8.7639]
- Installation type: [Docker/Native/NAS/Cloud]
- Connection method: [Local network/Remote/VPN]

**System Information:**

- Host OS: [e.g. Ubuntu 22.04, Windows 11, macOS]
- Browser: [e.g. Chrome 116, Firefox 117, Safari 16]
- Device: [Desktop/Mobile/Tablet]

## Configuration

**Docker Compose Configuration (if applicable):**

```yaml
# Paste relevant docker-compose.yml sections here
# Remove sensitive information like PLEX_TOKEN
```

**Environment Variables:**

```bash
# List relevant environment variables (remove sensitive data)
PLEX_URL=http://[REDACTED]:32400
PLEX_LIBRARY=Movies
DEBUG_MODE=false
```

## Logs

**Container Logs:**

```text
# Paste relevant logs from: docker-compose logs plex-suggester
# Or from Flask debug output
```

**Browser Console Errors (if applicable):**

```text
# Press F12 -> Console tab and paste any errors
```

## Screenshots

If applicable, add screenshots to help explain your problem.

## Additional Context

Add any other context about the problem here, such as:

- When did the issue start occurring?
- Does it happen consistently or intermittently?
- Any recent changes to your Plex server or setup?
- Specific movies/shows where the issue occurs?
