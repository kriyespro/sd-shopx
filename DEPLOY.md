# Deploy — mnxstore.com (159.195.52.197)

VPS + Docker + Gunicorn + Nginx. Assumes a fresh Ubuntu/Debian server with
Docker + the Docker Compose plugin installed.

## 0. DNS (do this first, it needs time to propagate)

At your domain registrar, add:

```
A     mnxstore.com        159.195.52.197
A     www.mnxstore.com    159.195.52.197
```

Check it's live before continuing:

```bash
dig +short mnxstore.com
# should print 159.195.52.197
```

## 1. First-time server setup

SSH into `159.195.52.197`, then:

```bash
git clone https://github.com/kriyespro/sd-shopx.git mnxstore && cd mnxstore
cp .env.example .env
nano .env
```

Fill in `.env` — `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` are already set
correctly for mnxstore.com in `.env.example`. You still need to set:
- `SECRET_KEY` (generate below)
- `POSTGRES_PASSWORD`
- **Leave `DEBUG=True` for now** — flip it after the SSL cert is issued (step 4)

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 2. Build and start (HTTP only, DEBUG=True)

```bash
docker compose build
docker compose up -d db redis
docker compose up -d web nginx
```

```bash
curl -I http://mnxstore.com/       # expect 200
docker compose logs -f web         # check for errors
```

## 3. Migrate + create admin user (manual, on purpose)

Migrations are deliberately NOT run automatically in the container
entrypoint — review what's changing before applying it to prod data.

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Log into `https://mnxstore.com/sd/` and fill in **Site Settings** (logo,
email, phone, address) — powers the footer/navbar/contact page.

## 4. HTTPS (Let's Encrypt), then lock down DEBUG

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d mnxstore.com -d www.mnxstore.com
```

certbot edits the nginx container's config on the host mount and reloads it.
Once `https://mnxstore.com/` works:

```bash
nano .env        # set DEBUG=False
docker compose up -d web
```

`DEBUG=False` is what switches on Redis (cache + sessions), Postgres-backed
security cookies, HSTS, and the SSL redirect — all defined at the bottom of
`config/settings.py`. Don't flip it before the cert exists, or the SSL
redirect will loop with nothing to redirect to.

## 5. Redeploying after a code change

```bash
git pull
docker compose build web
docker compose up -d web
docker compose exec web python manage.py migrate   # only if there's a new migration — review it first
```

## What's already wired for this

- **Postgres** — set in `.env` (`POSTGRES_*`), `config/settings.py` switches
  off sqlite automatically once `POSTGRES_DB` is present.
- **Redis** — cache + session backend, only active when `DEBUG=False`.
- **Gunicorn** — 3 workers, behind Nginx as reverse proxy.
- **Nginx** — `server_name mnxstore.com www.mnxstore.com 159.195.52.197`
  already set in `nginx/nginx.conf`; serves `/static/` and `/media/`
  directly, proxies everything else to Gunicorn.
- **Whitenoise** — belt-and-suspenders static serving inside the Django
  process itself, in case the Nginx static volume isn't mounted somewhere.
- **Security headers** — HSTS, secure cookies, SSL redirect, `X_FRAME_OPTIONS`,
  all gated behind `DEBUG=False` (see bottom of `config/settings.py`).

## Not yet done (Phase 4/5 items, per dev_plan.txt)

- S3/Cloudinary for media (currently a local Docker volume — fine for one
  server, won't survive a server rebuild or scale past one instance)
- Payment gateway integration
- Email backend (order confirmations currently don't send anything)
- CI/CD — this is a manual `git pull && docker compose build` flow
