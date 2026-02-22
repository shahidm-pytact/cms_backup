# Docker: Build, Migrate, Run

Minimal guide for building the image, running migrations, and starting the app.

---

## Build

```bash
docker build -t cms-api:latest .
```

**What it does:** Builds the app image from the Dockerfile (Python deps, code, entrypoint). Tags it as `cms-api:latest`.

**Why:** The compose file uses `image: cms-api:latest`. If you change code or add migrations, rebuild so the image includes them. Without rebuild, containers use an old image and new migrations won’t run.

---

## Migrate

```bash
docker compose run --rm migrate
```

**What it does:** Starts the migrate service once. It runs `alembic upgrade head` and exits. Applies any pending migrations (e.g. new column lengths, tables).

**Why:** DB schema must match the app. Run after adding or changing migrations, or when the DB is behind. `run --rm` runs the container once and removes it; use this when you only want to run migrations without bringing up the full stack.

---

## Run

```bash
docker compose up -d
```

**What it does:** Starts all services in the background: `db` (Postgres), `migrate` (runs once at startup), then `api` (FastAPI). Uses `docker-compose.yml` and `.env`.

**Why:** Full local/prod stack. `-d` runs in the background. For logs in the foreground, use `docker compose up` (no `-d`).

---

## Typical flow

1. **After code or migration changes:**  
   `docker build -t cms-api:latest .` then `docker compose run --rm migrate` then `docker compose up -d`

2. **Only run migrations again:**  
   `docker compose run --rm migrate`

3. **Start/restart everything:**  
   `docker compose up -d`

4. **Stop everything:**  
   `docker compose down`  
   (Avoid `down -v` — that deletes DB data.)
