# Kedarmart — Django + Python backend

The HTML/CSS/JavaScript storefront is now served by Django with a database and session-protected JSON API. Django's admin manages products, variants, prices, stock, coupons, orders, tracking, moderated reviews and newsletter subscribers.

## Run on Windows

An isolated `.venv` and seeded SQLite database are already prepared. In PowerShell from this project:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. Create your own private administrator account:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Visit http://127.0.0.1:8000/admin/. No default admin password is created.

For a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_catalog
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py runserver
```

The seed command adds the eight supplied products without overwriting admin edits. Prices remain unset until confirmed by the company.

## Backend behavior

- Database-backed catalog, search and categories.
- Registration/login/logout with Django password hashing, password validators, CSRF protection and HTTP-only session cookies.
- Guest session cart/wishlist merged into the customer account on login and persisted in the database.
- Product variants, cart quantities and saved delivery addresses; address update is supported by the API.
- Checkout records an availability enquiry for unpriced products, or an order pending confirmation for priced products. Prices and coupons are calculated on the server.
- Checkout validates options and stock, snapshots product information, reserves stock for priced orders and prevents duplicate submissions using a customer-specific checkout UUID.
- Customer-specific order history and tracking; staff update status and tracking in admin.
- Moderated reviews and newsletter subscriptions stored in the database.

Online payments require a payment provider and credentials. Shipping charges and commercial terms remain pending. Enquiries do not reserve stock. Priced pending orders reserve stock; staff must reconcile reservations when cancelling orders. Do not confirm orders before resolving payment and final purchase terms. Automated emails and password reset emails are not configured. Rate limits use process-local cache; configure a shared cache before running multiple workers.

The earlier Sites URL remains a static review version. Sites' Worker hosting cannot execute Django; deploy this Python application on a Python-capable host for online backend access. Django injects `backend.js` into the storefront; the static preview does not load it.

## Production deployment

Install `requirements-production.txt`. Set variables from `.env.example` in the host dashboard or terminal; `.env` is not automatically loaded. Production requires `DJANGO_DEBUG=false`, a random `DJANGO_SECRET_KEY` and explicit allowed hostnames. Use HTTPS; secure cookies, HTTPS redirects and HSTS are enabled with debug off. Configure the trusted HTTPS reverse proxy correctly; only set `SECURE_PROXY_SSL_HEADER` if the proxy strips client-supplied forwarded headers.

Use PostgreSQL through the documented `DB_*` variables. SQLite is for local development; on a host it requires a persistent `DB_PATH` and one application instance. Back up the database. Never commit credentials or database files.

```sh
python manage.py migrate
python manage.py seed_catalog
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn kedarmart.wsgi:application --bind 0.0.0.0:8000
```

On Windows use `waitress-serve --listen=127.0.0.1:8000 kedarmart.wsgi:application` behind HTTPS. Use the development server only for local work.

## Verification

```powershell
.\.venv\Scripts\python.exe manage.py test store
.\.venv\Scripts\python.exe manage.py check
npm test
```

Backend tests cover CSRF, customer isolation, registration/login, hashing, guest selection merge, quantities, options, enquiries, stock reservation, server-side coupon calculations, duplicate checkout protection, subscription deduplication and review moderation. Frontend checks cover static behavior and API integration. Browser visual QA is unavailable here.

## JSON API

All paths end with `/`. Mutations require JSON and the `X-CSRFToken` returned by `GET /api/session/`. Sessions use same-origin cookies.

| Endpoint | Methods | Purpose |
| --- | --- | --- |
| `/api/session/` | GET | CSRF token, customer and saved selections |
| `/api/products/`, `/api/products/<slug>/` | GET | Catalog, with optional `q` and `category` filters |
| `/api/register/`, `/api/login/`, `/api/logout/` | POST | Customer authentication |
| `/api/cart/` | GET, POST, DELETE | Product slug, quantity and optional variant ID |
| `/api/wishlist/` | GET, POST, DELETE | Saved products |
| `/api/addresses/`, `/api/addresses/<id>/` | GET, POST, PUT, DELETE | Customer delivery addresses |
| `/api/coupon/` | POST | Validate an admin-configured code |
| `/api/checkout/` | POST | Address ID, UUID checkout key, optional coupon/note |
| `/api/orders/`, `/api/orders/<reference>/` | GET | Customer-owned orders and tracking |
| `/api/reviews/<slug>/` | GET | Approved reviews |
| `/api/reviews/` | POST | Submit a review for moderation |
| `/api/newsletter/` | POST | Save subscriber email |

Company text and catalog come from the supplied requirements. Packaging is illustrative; lifestyle imagery uses Unsplash and fonts use Google Fonts.
