# EVE Healthcare — Diagnostic Test Booking API

A backend service for diagnostic test bookings with simulated payments, built with Django and Django REST Framework.

## Tech Stack

- **Python 3.9+** / **Django 4.2** / **Django REST Framework**
- **SQLite** (local dev) / **PostgreSQL** (Docker)
- **JWT Authentication** via `djangorestframework-simplejwt`
- **Swagger/OpenAPI** docs via `drf-spectacular`

## Quick Start (Local — No Docker)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Seed sample data (3 diagnostic centres with tests)
python manage.py seed_data

# 5. Run the server
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`.
Swagger docs at `http://localhost:8000/api/docs/`.

## Quick Start (Docker)

```bash
docker-compose up --build
```

The service starts at `http://localhost:8000` with PostgreSQL.

## Running Tests

```bash
python manage.py test
```

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup/` | No | Register a new user |
| POST | `/api/auth/login/` | No | Login, returns JWT tokens |
| POST | `/api/auth/token/refresh/` | No | Refresh access token |
| GET | `/api/auth/profile/` | Yes | Get current user profile |

### Diagnostic Centres & Tests

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/centres/` | No | List all centres (paginated) |
| GET | `/api/centres/{id}/` | No | Centre detail with tests |
| GET | `/api/centres/tests/` | No | List all active tests |
| GET | `/api/centres/tests/{id}/` | No | Test detail |

### Bookings

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/bookings/` | Yes | List user's bookings |
| POST | `/api/bookings/` | Yes | Create a booking |
| GET | `/api/bookings/{id}/` | Yes | Booking detail |
| POST | `/api/bookings/{id}/cancel/` | Yes | Cancel a booking |

### Payments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/payments/` | Yes | Initiate simulated payment |
| POST | `/api/payments/webhook/` | No | Idempotent payment webhook |

## Example Requests

### 1. Sign Up

```bash
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "username": "patient", "password": "SecurePass123!"}'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "SecurePass123!"}'
```

Response:
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

### 3. List Centres

```bash
curl http://localhost:8000/api/centres/
```

### 4. Create Booking

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "test": "<test_uuid>",
    "centre": "<centre_uuid>",
    "appointment_datetime": "2026-10-15T10:00:00Z"
  }'
```

### 5. Initiate Payment

```bash
curl -X POST http://localhost:8000/api/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"booking_id": "<booking_uuid>"}'
```

### 6. Webhook (Simulated Provider Callback)

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_unique_123",
    "transaction_id": "txn_from_payment_response",
    "status": "SUCCESS"
  }'
```

## Database Schema

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users     │     │diagnostic_centres│     │diagnostic_tests  │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK)      │     │ id (UUID, PK)    │     │ id (UUID, PK)    │
│ email (uniq) │     │ name             │     │ name             │
│ username     │     │ location         │     │ description      │
│ phone        │     │ created_at       │     │ centre_id (FK)   │
│ password     │     └──────────────────┘     │ price            │
└──────────────┘                              │ is_active        │
       │                                      │ created_at       │
       │                                      └──────────────────┘
       │                                             │
       ▼                                             ▼
┌──────────────────┐     ┌──────────────────┐  ┌──────────────────┐
│    bookings      │     │    payments      │  │  webhook_events  │
├──────────────────┤     ├──────────────────┤  ├──────────────────┤
│ id (UUID, PK)    │◄────│ booking_id (FK)  │  │ event_id (PK)    │
│ user_id (FK)     │     │ id (UUID, PK)    │  │ processed_at     │
│ test_id (FK)     │     │ transaction_id   │  └──────────────────┘
│ centre_id (FK)   │     │ amount           │
│ appointment_dt   │     │ status           │
│ amount           │     │ created_at       │
│ status           │     └──────────────────┘
│ created_at       │
│ updated_at       │
└──────────────────┘
```

**Key relationships:**
- A `DiagnosticCentre` has many `DiagnosticTests`
- A `Booking` references a user, test, and centre
- A `Payment` belongs to a `Booking` (one booking can have multiple payment attempts)
- `WebhookEvent` ensures idempotent webhook processing (event_id as PK)

**Booking states:** PENDING → CONFIRMED (on successful payment) or FAILED (on failed payment). PENDING/CONFIRMED → CANCELLED (user action).

## Important Assumptions

1. **Payment simulation** randomly returns SUCCESS or FAILED (50/50) — no real gateway integration.
2. **Webhook idempotency** uses the `event_id` field as a primary key. Duplicate events return 200 OK without re-processing.
3. **Users can only see/manage their own bookings** — enforced at the queryset level.
4. **Test-centre validation** ensures a test belongs to the selected centre before booking.
5. **Appointments must be in the future** — past dates are rejected.
6. **Amount is auto-calculated** from the test price at booking time (not user-supplied).
7. **Centres and tests are read-only** via the API — managed through Django admin.
8. **Rate limiting** is configured (30 req/min anonymous, 60 req/min authenticated).

## What I Would Improve With More Time

- **Redis caching** for centre/test listings (high-read, low-write data)
- **Celery** for async payment processing and webhook retry logic
- **Webhook signature verification** (HMAC) for security
- **Comprehensive integration tests** with full booking-to-payment flow
- **CI/CD pipeline** with GitHub Actions
- **Database indexing** on commonly queried fields
- **Appointment slot management** to prevent double-booking time slots
- **Email notifications** on booking confirmation/cancellation
- **Admin API** for managing centres and tests programmatically
