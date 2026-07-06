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

## 2. Build and start

Ports 80/443 on this VPS already belong to another site's host-level nginx,
so this app's own nginx container only binds `8089` (see `docker-compose.yml`)
— it does **not** try to claim 80/443.

```bash
docker compose build
docker compose up -d db redis
docker compose up -d web nginx
```

```bash
curl -I http://127.0.0.1:8089/         # from the VPS itself — expect 200
docker compose logs -f web             # check for errors
```

## 3. Migrate + create admin user (manual, on purpose)

Migrations are deliberately NOT run automatically in the container
entrypoint — review what's changing before applying it to prod data.

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Log into `http://127.0.0.1:8089/sd/` (or `http://mnxstore.com/sd/` once the
host vhost from step 4 is in place) and fill in **Site Settings** (logo,
email, phone, address) — powers the footer/navbar/contact page.

## 4. SSL install (via the host's existing nginx, not this repo's Docker setup)

This app's nginx container never touches 80/443 — the box's **host-level**
nginx (the one already fronting the other site) needs a new vhost for
mnxstore.com that reverse-proxies to `127.0.0.1:8089`.

mnxstore.com is proxied through **Cloudflare in Full (strict) mode**, which
requires a valid HTTPS listener on this origin's port 443. This host's
certbot doesn't have the nginx plugin installed and it's unclear how the
other vhosts here get their certs, so instead of fighting that, use a
**Cloudflare Origin Certificate** — free, 15-year validity, no port-80
challenge needed at all, and trusted directly by Cloudflare for Full
(strict):

```
Cloudflare dashboard -> mnxstore.com -> SSL/TLS -> Origin Server
-> Create Certificate (hostnames: mnxstore.com, www.mnxstore.com,
   validity: 15 years)
```

Save the two PEM blocks it gives you onto the server:

```bash
sudo mkdir -p /etc/nginx/ssl/mnxstore
sudo nano /etc/nginx/ssl/mnxstore/cert.pem   # paste "Origin Certificate"
sudo nano /etc/nginx/ssl/mnxstore/key.pem    # paste "Private Key"
sudo chmod 600 /etc/nginx/ssl/mnxstore/key.pem
```

Then install the vhost (already has both the :80 and :443 blocks, pointing
at those cert paths):

```bash
sudo cp nginx/host-vhost.conf.example /etc/nginx/sites-available/mnxstore.com
sudo ln -s /etc/nginx/sites-available/mnxstore.com /etc/nginx/sites-enabled/
sudo nginx -t                      # validate config
sudo systemctl reload nginx
curl -I https://mnxstore.com/      # expect 200, proxied through to :8089
```

(If this host doesn't use the `sites-available`/`sites-enabled` layout —
e.g. everything lives directly in `/etc/nginx/conf.d/` — drop the file
there instead and skip the symlink step.)

No renewal cron needed — Cloudflare Origin Certificates are valid 15 years.

Once `https://mnxstore.com/` works, lock this app down:

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
- **Nginx (this repo's container)** — serves `/static/` and `/media/`
  directly, proxies everything else to Gunicorn, listens on host port 8089
  only. It does not own 80/443 and has no certbot/TLS involvement — that's
  the host's job (see `nginx/host-vhost.conf.example`).
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
