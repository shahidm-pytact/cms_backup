# Docker: Build, Migrate, Run

Guide for building the image, running migrations, and running the app locally or on the server.

---

## Services in docker-compose.yml

| Service      | Purpose             | Port (host) | Notes                                   |
|-------------|---------------------|-------------|-----------------------------------------|
| `db`        | PostgreSQL          | 5433        | Healthcheck, persistent volume.         |
| `migrate`   | Alembic one-off     | —           | Run with `docker compose run --rm migrate`. |
| `api-blue`  | FastAPI (blue slot) | 8000        | Blue-green: one API slot live at a time. |
| `api-green` | FastAPI (green slot)| 8001        | Blue-green: one API slot live at a time. |

---

## Build

```bash
docker build -t cms-api:latest .
```

**What it does:** Builds the app image from the Dockerfile (Python deps, code, entrypoint). Tags it as `cms-api:latest`.

**Why:** Compose uses `image: cms-api:latest` for migrate, api-blue, and api-green. Rebuild after code or migration changes so new containers won’t run.

---

## Migrate

```bash
docker compose run --rm migrate
```

**What it does:** Starts the migrate service once. It runs `alembic upgrade head` and exits. Applies any pending migrations (e.g. new column lengths, tables).

**Why:** DB schema must match the app. Run after adding or changing migrations, or when the DB is behind. Ensure `db` is up first (`docker compose up -d db`) if needed.

---

## Run (local development)

```bash
docker compose up -d db
docker compose run --rm migrate   # once, when schema changes
docker compose up -d api-blue     # or api-green; one slot is enough locally
```

**What it does:** Starts Postgres, runs migrations when needed, and one API instance (e.g. on port 8000).

**Alternative:** `docker compose up -d db api-blue` then run migrate when needed. For local dev you usually run only one API slot; running both is for testing blue-green.

---

## Typical flow

1. **After code or migration changes:**  
   `docker build -t cms-api:latest .` then `docker compose run --rm migrate` then `docker compose up -d db api-blue`

2. **Only run migrations:**  
   `docker compose run --rm migrate` (with `db` already up).

3. **Start/restart local stack:**  
   `docker compose up -d db api-blue`

4. **Stop everything:**  
   `docker compose down`  
   (Avoid `down -v` — that deletes DB data.)

---

## Blue-green (zero-downtime production)

The deploy workflow uses blue-green: two slots (api-blue on 8000, api-green on 8001). Only one is “live” at a time; Nginx proxies to the live port.

1. **Deploy flow:** New image is loaded, migrations run, then the **inactive** slot is started (e.g. api-green on 8001). After the new API passes health checks, the workflow writes `nginx-proxy.conf` with the new port and runs `sudo nginx -s reload`, then stops the old slot.
2. **State:** `.live-port` in the backend dir stores the current live port (8000 or 8001). Each deploy toggles (8000 → 8001 → 8000 → …).
3. **Nginx (required on server):**  
   - Create `/opt/apps/cms-blogs-management/backend/nginx-proxy.conf` (or copy from `nginx-proxy.conf.example`).  
   - In your server block (e.g. `/etc/nginx/conf.d/cms-backend.conf`), include it:
     ```nginx
     location / {
       include /opt/apps/cms-blogs-management/backend/nginx-proxy.conf;
     }
     ```
   - The workflow overwrites `nginx-proxy.conf` with `proxy_pass http://127.0.0.1:8000;` or `8001` and runs `sudo nginx -s reload`. The deploy user (SSH_USER) must have passwordless `sudo nginx -s reload` or `sudo systemctl reload nginx`.

4. **Legacy/orphan containers:** The workflow stops and removes any old `cms-api` container (from before blue-green) and uses `--remove-orphans` so port 8000/8001 stay free for the active slot.

### Changing .env on the server

The container reads `.env` only when it **starts**. If you edit `.env` on the server:

- **Option A:** Restart the live API container:  
  `docker restart cms-api-blue` or `docker restart cms-api-green` (whichever is running).
- **Option B:** Redeploy (push to prod). The new slot will start with the current `.env`.
