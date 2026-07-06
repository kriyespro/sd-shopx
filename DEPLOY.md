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
curl -I http://mnxstore.com/           # expect 200
curl -I http://159.195.52.197:8089/    # same site, on the requested test port
docker compose logs -f web             # check for errors
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

## 4. SSL install (Let's Encrypt via the `certbot` container)

Nginx runs *inside Docker*, not on the host, so this uses the webroot method
against the `certbot` service already defined in `docker-compose.yml` — no
`apt install certbot` on the host needed.

```bash
docker compose up -d certbot
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d mnxstore.com -d www.mnxstore.com \
  --email you@mnxstore.com --agree-tos --no-eff-email
```

This only works while port 80 is reachable from the public internet (Let's
Encrypt's HTTP-01 challenge always validates over port 80 — the 8089 test
port doesn't factor in here at all).

Once it succeeds, wire the cert into nginx:

```bash
cat nginx/nginx-ssl.conf.example >> nginx/nginx.conf
docker compose exec nginx nginx -s reload
curl -I https://mnxstore.com/      # expect 200
```

Auto-renewal (certs expire every 90 days) — add to the host's crontab:

```bash
crontab -e
# add:
0 3 * * * cd /path/to/mnxstore && docker compose run --rm certbot renew -q && docker compose exec nginx nginx -s reload
```

Then lock down DEBUG now that HTTPS actually works:

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
  directly, proxies everything else to Gunicorn. Listens on host ports 80
  (required for Let's Encrypt validation + eventual HTTPS redirect), 8089
  (requested test port, same site), and 443 (SSL, once step 4 is done).
- **Certbot** — runs as its own `certbot` service in `docker-compose.yml`,
  shares a webroot volume with nginx for ACME challenges.
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
