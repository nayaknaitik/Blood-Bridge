# Blood Bridge

Blood Bridge connects blood donors with recipients and blood banks. Same functionality as before; refactored to a clean JSON API backend with template-driven frontend and fetch/AJAX for dynamic data.

## Structure

```
BloodBridge/
├── app/
│   ├── __init__.py          # Flask app factory, DynamoDB init
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── donor.py
│   │   └── request.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # /api/auth: register, login, logout, session, choose-role, delete user (admin)
│   │   ├── donors.py         # /api/donors: my-donations, schedule
│   │   ├── requests.py       # /api/requests: create, my, pending, all (admin)
│   │   ├── matching.py       # /api/matching: inventory, dashboard
│   │   ├── health.py         # /api/health, /api/contact
│   │   └── pages.py          # HTML shells: /, /login, /register, /dashboard, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dynamodb_client.py  # DynamoDB tables wrapper
│   │   ├── database_service.py
│   │   ├── matching_service.py
│   │   ├── validation.py
│   │   └── auth_service.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── api.js        # All API calls
│   │       └── app.js        # DOM, forms, flash
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── register.html
│       ├── login.html
│       ├── dashboard.html
│       ├── choose_role.html
│       ├── request_blood.html
│       ├── schedule_donation.html
│       ├── view_requests_for_donors.html
│       ├── admin_dashboard.html
│       ├── contact.html
│       └── about.html
├── logs/
├── scripts/
│   └── create_dynamodb_tables.py  # Create DynamoDB tables (run once)
├── app.py                    # Entry: python app.py
├── config.py
├── wsgi.py                   # Production: gunicorn wsgi:app
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Backend

- **JSON only** from API routes. Standard response: `{ "success": true|false, "message": "...", "data": ... }`.
- **Page routes** (in `pages.py`) serve Jinja HTML shells only; no business logic in page handlers.
- **Validation** in `app/services/validation.py`.
- **Business logic** in `app/services/` (auth, matching, database).
- **Database** access only via `app/services/database_service.py` (DynamoDB).

## Frontend

- **Jinja** for layout and structure.
- **Dynamic data** via JavaScript `fetch`; all API calls go through `static/js/api.js`.
- **DOM and forms** in `static/js/app.js` (no inline API URLs in templates).

## Run

1. **Environment**

   - Copy `.env` and set `SECRET_KEY`, AWS credentials (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), and table names if you use custom ones.
   - Create DynamoDB tables once: `python scripts/create_dynamodb_tables.py` (requires AWS credentials and boto3).

2. **Development**

   ```bash
   python app.py
   ```

   App runs at `http://127.0.0.1:5000`.

3. **Production**

   ```bash
   gunicorn wsgi:app
   ```

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login (sets session) |
| POST | /api/auth/logout | Logout |
| GET | /api/auth/session | Current session |
| POST | /api/auth/choose-role | Set donor/recipient role |
| POST | /api/auth/users/<id>/delete | Admin: delete user |
| GET | /api/donors/my-donations | My donations |
| POST | /api/donors/schedule | Schedule donation |
| POST | /api/requests | Create blood request |
| GET | /api/requests/my | My requests (recipient) |
| GET | /api/requests/pending | Pending requests (donors view) |
| GET | /api/requests/all | Admin: all requests |
| GET | /api/matching/inventory | Inventory by blood group |
| GET | /api/matching/dashboard | Dashboard payload by role |
| GET | /api/health | Health check |
| POST | /api/contact | Contact form |

## Authentication

- Session-based. After login, session holds `user_id`, `name`, `user_email`, `role`, `current_role`.
- Private routes require `user_id` in session; admin-only routes require `role === 'admin'`.
- Logout clears session; cookie is HttpOnly, SameSite=Lax.

## Features (unchanged)

- Register / login / choose role (donor or recipient).
- Donor: schedule donation, view my donations, view urgent requests.
- Recipient: request blood, view my requests and availability.
- Blood bank role: dashboard with inventory, recent donors, pending requests.
- Admin: user management, requests, donations, inventory, delete user.
- Contact form, about page.
