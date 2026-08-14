# BachNest Backend — Refined Implementation Specification for Claude Code

**Document type:** Backend Engineering Master Specification  
**Based on:** BachNest PRD & System Architecture Specification v1.0.0  
**Purpose:** Give Claude Code a single, implementation-oriented source of truth for building the BachNest backend.  
**Backend:** FastAPI + Python 3.11+ + PostgreSQL 16/PostGIS + SQLAlchemy 2 Async + Alembic + Redis + Celery  
**API style:** REST `/api/v1` + WebSocket for real-time features  
**Primary currency:** BDT  
**Primary target:** Bangladesh bachelor rental use case  
**Implementation strategy:** MVP first, production-safe foundations, then advanced integrations.

**Critical product instruction:** Read Section 1A before implementing any feature. The backend exists to support BachNest's core mission of building trust and managing the complete bachelor rental lifecycle—not merely property listing.

---

## 0. IMPORTANT: HOW CLAUDE SHOULD USE THIS DOCUMENT

Claude should treat this document as the backend implementation contract.

### 0.1 General rules

1. Do not invent endpoints, fields, roles, business rules, or database relationships unless explicitly marked as an extension.
2. Preserve the domain terminology used here: `BACHELOR`, `OWNER`, `ADMIN`, `SUPER_ADMIN`, `PROPERTY`, `ROOM`, `SEAT`, `BOOKING`, `TENANCY`, `INVOICE`, `PAYMENT`, `COMPLAINT`, `SOS`.
3. Prefer a modular monolith over microservices for the FYDP/MVP.
4. Keep business logic out of FastAPI route functions. Routes should validate input, authorize the request, call a service, and return a response.
5. Use SQLAlchemy 2.x async APIs and Alembic migrations.
6. Every protected endpoint must enforce both authentication and authorization.
7. Never trust IDs supplied by clients. Always verify ownership/tenancy access in the service layer.
8. Never store raw passwords. Use Argon2id where available.
9. Never store sensitive KYC documents as public URLs. Use private object storage and short-lived signed URLs.
10. Payment webhooks must be idempotent.
11. Important state transitions must be validated server-side.
12. Add tests for every service containing non-trivial business logic.
13. Do not implement real payment/KYC/SMS providers before the provider interface and mock implementation are working.
14. Keep external integrations behind adapters/interfaces so they can be replaced later.

### 0.2 MVP priority

Implement in this order:

**P0 — Required**
- Project setup
- Database + migrations
- Authentication
- JWT access/refresh flow
- RBAC
- User profile
- KYC submission/status
- Owner property CRUD
- Room and seat CRUD
- Public property search
- Booking request/decision
- Tenancy creation
- Invoice generation
- Payment record + mock gateway
- Complaint/ticket lifecycle
- Notifications
- Basic admin moderation
- Audit logging
- API documentation
- Automated tests

**P1 — Important**
- PostGIS radius search
- Roommate preferences + compatibility score
- Digital notices
- Reviews
- Redis caching
- Celery scheduled invoice/reminder jobs
- Emergency SOS + WebSocket

**P2 — Advanced**
- Real bKash/SSLCommerz integration
- NID OCR/face verification
- Digital contract PDF
- S3/Cloudinary production storage
- Community marketplace
- Advanced analytics
- Production deployment and observability

---

# 1. PRODUCT CONTEXT

BachNest is a two-sided rental lifecycle platform designed around bachelors looking for rooms/seats and property owners managing tenants.

The original PRD identifies five major problems:

1. Trust deficit between bachelors and owners.
2. Fragmented and unverified room discovery.
3. Poor rent, utility, complaint, and notice management.
4. Roommate incompatibility.
5. Emergency vulnerability.

The backend therefore needs to support the complete lifecycle:

```text
User Registration
      ↓
Authentication
      ↓
KYC Verification
      ↓
Property Discovery / Property Publishing
      ↓
Room / Seat Selection
      ↓
Booking Request
      ↓
Owner Decision
      ↓
Tenancy
      ↓
Monthly Invoice
      ↓
Payment
      ↓
Complaint / Notice / Emergency
      ↓
Move-out
      ↓
Review / Trust Score
```

The original PRD explicitly defines verified listings, KYC-backed users, geospatial search, digital rent/payment workflows, maintenance ticketing, notices, reviews, and SOS as core platform capabilities.

---

# 1A. PROJECT PURPOSE, CORE MISSION & PROBLEM-SOLUTION CONTEXT

> **CRITICAL: Claude must understand this section before implementing any backend module.**

## 1A.1 One-line project purpose

**“BachNest helps bachelors find trusted rooms and manage their entire rental journey in one place.”**

This is the core product purpose from the BachNest PRD. Therefore, the backend must not be treated as only a room-listing API. It is a **trusted, transparent, two-sided rental lifecycle management platform**.

The two primary sides are:

```text
BACHELOR / TENANT
        ↕
   BACHNEST PLATFORM
        ↕
PROPERTY OWNER / LANDLORD
```

Administrators provide verification, moderation, dispute handling, compliance, and safety oversight.

## 1A.2 Main problem being solved

BachNest addresses five connected problems in the bachelor rental market.

### Problem 1 — Trust deficit

There is a two-way trust problem.

**Owners may worry about:**
- unpaid rent,
- property damage,
- illegal subletting,
- tenant identity,
- security risks,
- lack of reliable tenant records.

**Bachelors may worry about:**
- arbitrary rent increases,
- privacy invasion,
- sudden eviction,
- withheld security deposits,
- misleading property information,
- unreliable landlords.

BachNest addresses this with:

```text
Identity Verification
        ↓
KYC
        ↓
Verified Profiles
        ↓
Trust Score + Reviews
        ↓
More Trustworthy Rental Interaction
```

The backend must enforce verification requirements wherever a business rule requires them.

### Problem 2 — Fragmented and unverified room discovery

Traditional room hunting can depend on Facebook groups, informal advertisements, “To-Let” posters, brokers, and word of mouth.

This makes it difficult to compare:
- actual rent,
- deposit,
- availability,
- amenities,
- location,
- house rules,
- owner credibility.

BachNest solves this using a structured inventory:

```text
Property
   ↓
Room
   ↓
Seat / Bed
```

combined with:

```text
Location
Budget
Room Type
Amenities
House Rules
Availability
Verification
```

Backend requirements:
- structured property data,
- room/seat inventory,
- publication status,
- admin verification,
- PostGIS search,
- filters,
- availability management.

### Problem 3 — Fragmented rental operations

After finding a room, rent, utilities, complaints, notices, agreements, and payment proof can be handled through disconnected channels.

BachNest brings them into one lifecycle:

```text
Search
  ↓
Booking
  ↓
Tenancy
  ↓
Digital Agreement
  ↓
Monthly Invoice
  ↓
Payment
  ↓
Receipt
  ↓
Complaint / Notice
  ↓
Move-out
  ↓
Review
```

The backend must therefore maintain a reliable rental and financial lifecycle rather than isolated CRUD records.

### Problem 4 — Roommate incompatibility

Shared accommodation can create conflict due to:
- smoking preference,
- sleep schedule,
- cleanliness,
- study habits,
- dietary preference,
- cooking habits,
- guest preference,
- lifestyle.

BachNest addresses this with a roommate compatibility system:

```text
User Preferences
       +
Existing Roommates / Room Preferences
       ↓
Compatibility Engine
       ↓
Compatibility Score
       ↓
Better Roommate Decision
```

For MVP, use a transparent rule-based scoring system. Do not claim it is machine learning unless an actual ML model is implemented.

### Problem 5 — Safety and emergency vulnerability

Bachelors may live away from family and immediate support.

BachNest therefore includes an emergency workflow:

```text
SOS Trigger
    ↓
Emergency Alert
    ↓
GPS Location
    ↓
Emergency Contacts
    ↓
Flatmates / Owner / Safety Team
    ↓
Real-time Notification
    ↓
Incident Logging
```

SOS information is sensitive and must be access-controlled.

## 1A.3 Core mission

The core mission is:

> **Bridge the trust gap between bachelor tenants and property owners while making the complete rental journey transparent, verifiable, manageable, and safer.**

This creates five backend objectives.

### Objective A — Build trust

Provide:
- identity verification,
- KYC,
- verified listings,
- trust score,
- two-sided reviews,
- audit logs.

### Objective B — Make discovery reliable

Provide:
- structured property listings,
- room/seat inventory,
- geospatial search,
- filters,
- availability,
- transparent rent/deposit information.

### Objective C — Digitize the rental lifecycle

Provide:
- booking,
- owner approval,
- tenancy,
- digital agreement support,
- monthly invoices,
- payment records,
- receipts,
- move-in/move-out records.

### Objective D — Improve tenant-owner operations

Provide:
- complaint/maintenance ticketing,
- SLA tracking,
- digital notices,
- tenant roster management,
- payment reminders,
- financial records.

### Objective E — Improve safety

Provide:
- emergency contacts,
- one-touch SOS,
- real-time emergency alerts,
- GPS coordinates,
- incident logging,
- controlled emergency access.

## 1A.4 What BachNest is NOT

Do not misunderstand BachNest as only:

```text
❌ A room-listing website
❌ A Facebook-group replacement
❌ A simple property CRUD system
❌ A payment application
❌ A roommate chat application
```

It is a **rental lifecycle platform** combining:

```text
Discovery
+
Trust
+
Booking
+
Tenancy
+
Billing
+
Maintenance
+
Communication
+
Roommate Compatibility
+
Reviews
+
Emergency Safety
+
Administration
```

## 1A.5 Target users and their purpose

### Bachelor / Tenant

Typical journey:

```text
Register
→ Verify Identity
→ Search
→ Compare
→ Book
→ Become Tenant
→ Pay Rent
→ Raise Complaints
→ Receive Notices
→ Find Compatible Roommates
→ Use SOS if necessary
→ Review Owner
```

### Property Owner

Typical journey:

```text
Register
→ Verify Identity / Property
→ Create Property
→ Create Rooms/Seats
→ Publish Listing
→ Receive Booking
→ Approve Tenant
→ Manage Tenancy
→ Generate Invoices
→ Track Payments
→ Handle Complaints
→ Publish Notices
→ Review Tenant
```

### Platform Admin / Trust & Safety Officer

Typical journey:

```text
KYC Verification
→ Listing Moderation
→ User Moderation
→ Dispute Arbitration
→ Complaint Oversight
→ Emergency Monitoring
→ Audit / Compliance
```

## 1A.6 Complete product journey

```text
                    BACHNEST
                       │
        ┌──────────────┴──────────────┐
        │                             │
    BACHELOR                         OWNER
        │                             │
     Register                      Register
        │                             │
       KYC                           KYC
        │                             │
        └────────── TRUST ────────────┘
                       │
                 Property Search
                       │
                Property Details
                       │
                 Room / Seat
                       │
                    Booking
                       │
               Owner Decision
                       │
                    Tenancy
                       │
          ┌────────────┼────────────┐
          │            │            │
       Billing      Complaint      Notice
          │            │            │
       Payment      Resolution   Read Receipt
          │            │            │
          └────────────┼────────────┘
                       │
                    Move-out
                       │
                    Reviews
                       │
                  Trust Update
```

Emergency SOS is available during the active rental relationship:

```text
Active Tenancy
      │
      ├── Normal Rental Operations
      │
      └── SOS
           ↓
      Emergency Alert
           ↓
      Contacts / Flatmates / Owner / Safety Team
```

## 1A.7 Definition of project success

The backend should support this complete demonstration:

> A bachelor registers, verifies identity, searches for a trusted room near a desired location, filters by budget and lifestyle requirements, views a verified property, requests a room/seat, receives owner approval, becomes a tenant, receives monthly invoices, pays digitally, receives receipts, submits maintenance complaints, receives building notices, can trigger an SOS during an emergency, and eventually completes the tenancy and reviews the owner.

At the same time:

> A property owner can verify their identity, publish structured property/room information, receive and manage booking requests, maintain a tenant roster, generate and track rent invoices, receive payments, manage complaints, publish notices, and receive reviews.

And:

> An administrator can verify KYC, moderate listings, handle disputes, monitor complaints/emergencies, and inspect audit records.

## 1A.8 Why each backend module exists

| Backend module | Purpose in BachNest |
|---|---|
| Authentication | Secure user identity |
| KYC | Establish identity-based trust |
| Trust Score | Represent verified rental reputation |
| Property CRUD | Create structured listings |
| PostGIS Search | Make room discovery efficient |
| Room/Seat Inventory | Represent actual availability |
| Booking | Formalize rental requests |
| Tenancy | Represent the actual rental relationship |
| Billing | Make rent and utilities transparent |
| Payment | Create verifiable financial records |
| Complaint | Formalize maintenance accountability |
| Notice | Improve owner-tenant communication |
| Roommate Matching | Reduce compatibility conflicts |
| Reviews | Build two-sided reputation |
| SOS | Improve emergency safety |
| Audit Logs | Provide accountability |
| Admin | Protect platform trust |

## 1A.9 Backend decision principle

For every backend feature, ask:

> **How does this feature help BachNest create a more trusted, transparent, manageable, or safer bachelor rental journey?**

If a requirement is ambiguous, this principle should guide the implementation without inventing unrelated product functionality.

# 2. BACKEND ARCHITECTURE

## 2.1 Architecture style

Use a **modular monolith with clean architecture boundaries**.

```text
Client
  │
  ├── REST JSON
  └── WebSocket
        │
        ▼
FastAPI
  │
  ├── API / Routers
  │
  ├── Dependencies
  │     ├── Authentication
  │     ├── RBAC
  │     └── DB / Redis
  │
  ├── Services
  │     ├── Auth
  │     ├── KYC
  │     ├── Property
  │     ├── Search
  │     ├── Booking
  │     ├── Tenancy
  │     ├── Billing
  │     ├── Payment
  │     ├── Complaint
  │     ├── Notice
  │     ├── Review
  │     ├── Emergency
  │     └── Notification
  │
  ├── Repositories / SQLAlchemy
  │
  ├── PostgreSQL + PostGIS
  │
  ├── Redis
  │
  └── Celery Workers
```

## 2.2 Layer responsibilities

### API layer

Responsible for:
- HTTP method and route.
- Request parsing.
- Pydantic validation.
- Authentication dependency.
- Role checks.
- Calling services.
- HTTP response mapping.

Do NOT put:
- complex SQL,
- payment calculations,
- booking state machines,
- trust-score algorithms,
- invoice calculations

inside route functions.

### Service layer

Responsible for:
- business rules,
- transactions,
- state transitions,
- ownership checks,
- calculations,
- external adapter calls,
- domain validation.

### Repository/data layer

Responsible for:
- SQLAlchemy queries,
- persistence,
- reusable database operations.

For a small FYDP implementation, repositories may be kept lightweight. Do not create unnecessary abstractions for every one-line query.

### Worker layer

Responsible for:
- scheduled invoice creation,
- reminders,
- notification dispatch,
- KYC OCR,
- asynchronous processing.

---

# 3. RECOMMENDED PROJECT STRUCTURE

```text
bachnest-backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── kyc.py
│   │           ├── properties.py
│   │           ├── rooms.py
│   │           ├── seats.py
│   │           ├── search.py
│   │           ├── bookings.py
│   │           ├── tenancies.py
│   │           ├── billing.py
│   │           ├── payments.py
│   │           ├── complaints.py
│   │           ├── notices.py
│   │           ├── reviews.py
│   │           ├── emergency.py
│   │           ├── notifications.py
│   │           └── admin.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── constants.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── seed.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── kyc.py
│   │   ├── roommate_preference.py
│   │   ├── property.py
│   │   ├── room.py
│   │   ├── room_seat.py
│   │   ├── property_media.py
│   │   ├── booking.py
│   │   ├── tenancy.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   ├── complaint.py
│   │   ├── notice.py
│   │   ├── emergency.py
│   │   ├── emergency_contact.py
│   │   ├── review.py
│   │   ├── notification.py
│   │   └── audit_log.py
│   │
│   ├── schemas/
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── kyc.py
│   │   ├── roommate.py
│   │   ├── property.py
│   │   ├── room.py
│   │   ├── search.py
│   │   ├── booking.py
│   │   ├── tenancy.py
│   │   ├── billing.py
│   │   ├── payment.py
│   │   ├── complaint.py
│   │   ├── notice.py
│   │   ├── review.py
│   │   ├── emergency.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── kyc_service.py
│   │   ├── property_service.py
│   │   ├── room_service.py
│   │   ├── search_service.py
│   │   ├── roommate_service.py
│   │   ├── booking_service.py
│   │   ├── tenancy_service.py
│   │   ├── billing_service.py
│   │   ├── payment_service.py
│   │   ├── complaint_service.py
│   │   ├── notice_service.py
│   │   ├── review_service.py
│   │   ├── emergency_service.py
│   │   ├── notification_service.py
│   │   └── audit_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── property_repository.py
│   │   ├── booking_repository.py
│   │   ├── tenancy_repository.py
│   │   ├── invoice_repository.py
│   │   └── complaint_repository.py
│   │
│   ├── integrations/
│   │   ├── storage/
│   │   │   ├── base.py
│   │   │   └── local_storage.py
│   │   ├── payments/
│   │   │   ├── base.py
│   │   │   └── mock_gateway.py
│   │   ├── sms/
│   │   │   ├── base.py
│   │   │   └── mock_sms.py
│   │   └── kyc/
│   │       ├── base.py
│   │       └── mock_kyc.py
│   │
│   ├── websockets/
│   │   ├── connection_manager.py
│   │   └── sos_dispatcher.py
│   │
│   └── workers/
│       ├── celery_app.py
│       ├── invoice_tasks.py
│       ├── reminder_tasks.py
│       └── notification_tasks.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

# 4. DATABASE DESIGN

## 4.1 Core entities

```text
User
 ├── UserKYC
 ├── RoommatePreference
 ├── EmergencyContact
 ├── Property [as owner]
 ├── Booking [as tenant]
 ├── Tenancy [as tenant/owner]
 ├── Invoice
 ├── Payment
 ├── Complaint
 ├── Notice
 ├── EmergencyAlert
 ├── Review
 └── AuditLog

Property
 ├── Rooms
 ├── Media
 ├── Notices
 ├── Bookings
 ├── Tenancies
 ├── Complaints
 └── EmergencyAlerts

Room
 └── RoomSeats

Booking
 └── Tenancy

Tenancy
 ├── Invoices
 ├── Complaints
 └── Reviews

Invoice
 └── Payments
```

## 4.2 Required PostgreSQL extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

Use UUID primary keys.

Use PostGIS `geometry(Point, 4326)` for property coordinates.

---

# 5. DATABASE REFINEMENT RULES

The source PRD provides the main schema. The following are implementation refinements, not replacements of the original product intent.

## 5.1 Add timestamps consistently

Every mutable business entity should have:

```text
created_at
updated_at
```

Use timezone-aware timestamps.

## 5.2 Add uniqueness constraints where business logic requires them

Examples:

```text
users.phone UNIQUE
users.email UNIQUE
user_kyc.user_id UNIQUE
roommate_preferences.user_id UNIQUE
room_seats(room_id, seat_identifier) UNIQUE
payments.transaction_reference UNIQUE
invoices.invoice_number UNIQUE
```

## 5.3 Add indexes

Minimum indexes:

```text
users(email)
users(phone)
properties(owner_id)
properties(location) USING GIST
properties(city)
properties(area_neighborhood)
rooms(property_id, is_available)
room_seats(room_id, is_occupied)
bookings(tenant_id, booking_status)
bookings(property_id, room_id, booking_status)
tenancies(tenant_id, status)
tenancies(owner_id, status)
invoices(tenant_id, billing_month_year)
invoices(due_date, status)
payments(invoice_id)
complaints(property_id, status)
emergency_alerts(user_id, is_active)
audit_logs(actor_id, entity_name, entity_id)
```

---

# 6. ENUMS AND STATE MACHINES

## 6.1 Roles

```python
class UserRole(str, Enum):
    BACHELOR = "BACHELOR"
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
```

## 6.2 KYC

```text
UNVERIFIED
   ↓
PENDING
   ├── APPROVED
   └── REJECTED
```

A rejected KYC may be resubmitted.

## 6.3 Booking

Use the source PRD states:

```text
REQUESTED
   ├── REJECTED
   └── APPROVED_BY_OWNER
             ↓
        DEPOSIT_PAID
             ↓
           ACTIVE
             ↓
         COMPLETED

Any valid active booking may be CANCELLED according to cancellation rules.
```

### Booking invariants

- Only a `BACHELOR` can create a booking request.
- The target property must be published and available.
- The target room must be available.
- If `seat_id` is supplied, it must belong to the room.
- A seat cannot be booked by two active tenants.
- Owner can only approve/reject bookings for their own property.
- Creating tenancy must happen inside a database transaction.
- Occupancy must be updated atomically.

## 6.4 Tenancy

```text
ACTIVE
   ├── NOTICE_SERVED
   │       ↓
   │   TERMINATED
   │
   └── EVICTED
```

## 6.5 Invoice

```text
DRAFT
  ↓
ISSUED
  ├── PARTIALLY_PAID
  │       ↓
  │     PAID
  ├── PAID
  ├── OVERDUE
  └── CANCELLED
```

Never allow a paid invoice to become unpaid.

## 6.6 Complaint

```text
OPEN
 ↓
ACKNOWLEDGED
 ↓
IN_PROGRESS
 ↓
RESOLVED
 ↓
CLOSED

OPEN / ACKNOWLEDGED / IN_PROGRESS / RESOLVED
                    ↓
                 REOPENED
```

Every status transition must be validated.

---

# 7. AUTHENTICATION AND AUTHORIZATION

## 7.1 Registration

### Request

```json
{
  "phone": "017XXXXXXXX",
  "email": "user@example.com",
  "password": "strong-password",
  "full_name": "User Name",
  "role": "BACHELOR",
  "gender": "OTHER"
}
```

### Rules

- Normalize phone.
- Normalize email to lowercase.
- Validate password strength.
- Reject duplicate email/phone.
- Hash password.
- Create user.
- Return access/refresh token pair only after the chosen verification policy is satisfied.

For MVP, email/phone verification may be mocked.

## 7.2 Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "identifier": "email-or-phone",
  "password": "..."
}
```

Return:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 900
}
```

## 7.3 Token strategy

Recommended:

```text
Access token: 15 minutes
Refresh token: 7 days
```

Use JWT.

Refresh-token rotation should be implemented if feasible.

Never place:
- password,
- NID number,
- NID image,
- private KYC URL

inside JWT payload.

## 7.4 Authorization dependencies

Implement reusable dependencies:

```python
get_current_user()
require_authenticated_user()
require_roles(UserRole.OWNER)
require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)
require_kyc_approved()
```

## 7.5 Object-level authorization

Example:

```text
OWNER A owns Property P
OWNER B does not own Property P

OWNER A -> PATCH /properties/P       allowed
OWNER B -> PATCH /properties/P       403
```

Never rely only on the role.

---

# 8. USER AND KYC MODULE

## 8.1 User endpoints

```http
GET   /api/v1/users/me
PATCH /api/v1/users/me
GET   /api/v1/users/{id}
```

Do not expose sensitive KYC information publicly.

## 8.2 KYC endpoints

```http
POST  /api/v1/kyc
GET   /api/v1/kyc/me
PATCH /api/v1/kyc/{id}/resubmit
GET   /api/v1/admin/kyc
PATCH /api/v1/admin/kyc/{id}/decision
```

## 8.3 KYC submission

Support:
- NID/passport number,
- front document,
- back document where applicable,
- student ID,
- institution,
- department,
- employment proof,
- employer.

For MVP, implement a `MockKYCProvider`.

Provider interface:

```python
class KYCProvider(Protocol):
    async def verify(self, document_data: dict) -> KYCVerificationResult:
        ...
```

This allows future OCR/identity APIs without changing the KYC service.

---

# 9. PROPERTY MODULE

## 9.1 Owner property creation

```http
POST /api/v1/properties
```

Required:

```text
title
description
property_type
address_line
area_neighborhood
city
location.lat
location.lng
```

Optional:

```text
postal_code
total_floors
property_floor
flat_number
lift
generator
CCTV
gate closing time
visitor policy
```

## 9.2 Property lifecycle

Recommended:

```text
DRAFT
  ↓
PUBLISHED
  ↓
UNPUBLISHED
```

The original schema uses `is_published` and `is_verified_by_admin`. Preserve those fields.

Business rule:

```text
is_published = true
AND
is_verified_by_admin = true
```

should be required for public discovery if admin verification is enabled.

For MVP development, seed/demo data may be admin-verified manually.

## 9.3 Property endpoints

```http
POST   /api/v1/properties
GET    /api/v1/properties/{id}
PATCH  /api/v1/properties/{id}
DELETE /api/v1/properties/{id}

GET    /api/v1/owner/properties
PATCH  /api/v1/properties/{id}/publish
```

---

# 10. ROOM AND SEAT INVENTORY

## 10.1 Room endpoints

```http
POST   /api/v1/properties/{property_id}/rooms
GET    /api/v1/properties/{property_id}/rooms
GET    /api/v1/rooms/{room_id}
PATCH  /api/v1/rooms/{room_id}
DELETE /api/v1/rooms/{room_id}
```

## 10.2 Seat endpoints

```http
POST   /api/v1/rooms/{room_id}/seats
GET    /api/v1/rooms/{room_id}/seats
PATCH  /api/v1/seats/{seat_id}
DELETE /api/v1/seats/{seat_id}
```

## 10.3 Occupancy rules

Never trust `current_occupancy` from a client.

Calculate/update occupancy server-side.

For shared rooms:

```text
capacity = total number of seats
occupied = number of active occupied seats
available = capacity - occupied
```

When assigning a tenant to a seat, use a transaction and row locking where necessary to prevent race conditions.

---

# 11. PROPERTY MEDIA

MVP can use local storage.

Production can use:
- AWS S3
- Cloudinary

Recommended abstraction:

```python
class StorageProvider(Protocol):
    async def upload(...)
    async def delete(...)
    async def create_signed_url(...)
```

Do not store large binary files in PostgreSQL.

Store metadata and private object keys/URLs.

---

# 12. SEARCH AND POSTGIS

## 12.1 Public search endpoint

```http
GET /api/v1/search/map
```

Query parameters:

```text
lat
lng
radius_km
budget_min
budget_max
room_type
property_type
area
city
attached_bath
balcony
AC
lift
generator
wifi
furnished
```

## 12.2 Radius search

Use PostGIS.

Conceptually:

```sql
ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
    :radius_meters
)
```

Order by distance:

```sql
ST_Distance(
    location::geography,
    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
)
```

Important: longitude is `lng`, latitude is `lat`.

## 12.3 Bounding box search

For map viewport:

```text
min_lat
min_lng
max_lat
max_lng
```

Use `ST_MakeEnvelope`.

## 12.4 Search response

```json
{
  "items": [
    {
      "property_id": "uuid",
      "title": "Affordable Bachelor Flat",
      "area": "Mirpur",
      "city": "Dhaka",
      "latitude": 23.80,
      "longitude": 90.36,
      "starting_rent": 6500,
      "available_rooms": 2,
      "tags": ["WIFI", "LIFT", "NON_SMOKING"],
      "distance_km": 1.8,
      "cover_image_url": "..."
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 50
}
```

---

# 13. ROOMMATE COMPATIBILITY

The PRD specifies matching based on lifestyle, dietary preferences, profession, study habits, guests, and cleanliness.

## 13.1 MVP scoring

Use a transparent weighted score.

Example:

```text
Smoking compatibility       25%
Sleep schedule              20%
Cleanliness                 20%
Guest preference            10%
Dietary preference          10%
Study habit                 10%
Occupation                   5%
--------------------------------
Total                       100%
```

Do not call this machine learning in the MVP. It is a rule-based compatibility algorithm.

## 13.2 Compatibility function

```python
score = weighted_sum(
    smoking_match,
    sleep_match,
    cleanliness_match,
    guest_match,
    dietary_match,
    study_match,
    occupation_match,
)
```

Return:

```json
{
  "candidate_user_id": "uuid",
  "compatibility_score": 86.5,
  "matched_preferences": [
    "non_smoker",
    "early_bird",
    "cleanliness"
  ]
}
```

---

# 14. BOOKING MODULE

## 14.1 Create booking

```http
POST /api/v1/bookings/request
```

Request:

```json
{
  "property_id": "uuid",
  "room_id": "uuid",
  "seat_id": "uuid",
  "requested_move_in_date": "2026-09-01",
  "token_deposit_amount": 2000
}
```

## 14.2 Validation

Before creating:

1. User is authenticated.
2. User role is `BACHELOR`.
3. KYC policy is satisfied.
4. Property exists.
5. Property is published.
6. Property is verified.
7. Room belongs to property.
8. Room is available.
9. Seat belongs to room if provided.
10. Seat is not occupied.
11. User does not already have a conflicting active booking/tenancy.
12. Token amount is valid.

## 14.3 Owner decision

```http
PATCH /api/v1/bookings/{booking_id}/decision
```

Request:

```json
{
  "decision": "APPROVE",
  "reason": null
}
```

or:

```json
{
  "decision": "REJECT",
  "reason": "Room no longer available."
}
```

Owner can only decide on bookings for their own property.

## 14.4 Booking approval transaction

Approval should:

```text
BEGIN
  lock booking
  validate REQUESTED
  validate inventory
  update booking status
  create tenancy or prepare tenancy workflow
  reserve inventory
  create audit event
COMMIT
```

---

# 15. TENANCY MODULE

## 15.1 Create tenancy

A tenancy represents an actual rental relationship.

Fields:

```text
booking_id
property_id
room_id
seat_id
tenant_id
owner_id
agreed_monthly_rent
agreed_security_deposit
lease_start_date
lease_end_date
notice_period_days
agreement status
tenancy status
```

## 15.2 Tenancy endpoints

```http
GET   /api/v1/tenancies/me
GET   /api/v1/tenancies/{id}
PATCH /api/v1/tenancies/{id}/notice
PATCH /api/v1/tenancies/{id}/terminate
```

Only relevant tenant, property owner, or authorized admin may access tenancy data.

---

# 16. BILLING AND INVOICING

## 16.1 Invoice formula

```text
total =
    base_rent
  + service_charge
  + electricity
  + water
  + gas
  + internet
  + other_fines_adjustments
```

Use `Decimal`, never floating point, for money.

## 16.2 Billing service

```python
def calculate_invoice_total(invoice_data) -> Decimal:
    ...
```

## 16.3 Monthly invoice generation

Celery scheduled task:

```text
1st day of month
   ↓
find ACTIVE tenancies
   ↓
for each tenancy:
   create invoice
   calculate utilities
   set due date
   create notification
```

Prevent duplicate invoices with a database uniqueness rule such as:

```text
(tenancy_id, billing_month_year) UNIQUE
```

This is an important implementation refinement.

## 16.4 Split utilities

Support:

```text
EQUAL
PROPORTIONAL
```

MVP can implement equal split first.

Example:

```text
Internet = 1200 BDT
Occupants = 3

Each = 1200 / 3 = 400 BDT
```

Use `Decimal` and define rounding behavior explicitly.

---

# 17. PAYMENT MODULE

## 17.1 Architecture

Do not tightly couple billing to a specific payment provider.

```text
PaymentService
      │
      ├── MockGateway
      ├── SSLCommerzGateway
      ├── BKashGateway
      └── FutureGateway
```

Interface:

```python
class PaymentGateway(Protocol):
    async def create_checkout(self, payment_request): ...
    async def verify_payment(self, callback_data): ...
    async def refund(self, transaction_id, amount): ...
```

## 17.2 MVP payment flow

```text
Client
 ↓
POST /payments/checkout
 ↓
PaymentService
 ↓
MockGateway
 ↓
pending payment
 ↓
webhook/callback
 ↓
verify
 ↓
idempotency check
 ↓
record payment
 ↓
update invoice
 ↓
create receipt
```

## 17.3 Webhook security

Never trust a payment callback just because it says `SUCCESS`.

Validate:
- provider signature,
- transaction ID,
- amount,
- invoice ID,
- merchant credentials,
- payment status.

Use idempotency.

If the same webhook arrives twice:

```text
first request  -> process
second request -> return already processed
```

Do not double-credit the invoice.

---

# 18. COMPLAINT / MAINTENANCE MODULE

## 18.1 Create complaint

```http
POST /api/v1/complaints
```

Fields:

```text
property_id
room_id
title
description
category
priority
evidence
```

## 18.2 Access rules

A tenant can create complaints only for a property/tenancy they are associated with.

Owner can manage complaints for owned properties.

Admin can access all complaints.

## 18.3 SLA

Example configurable SLA:

```text
LOW        → 72 hours
MEDIUM     → 48 hours
HIGH       → 24 hours
EMERGENCY  → immediate
```

Store an SLA deadline when the ticket is created.

Do not hard-code the number throughout the application. Put it in configuration/constants.

## 18.4 Status endpoint

```http
PATCH /api/v1/complaints/{id}/status
```

Validate allowed transitions.

---

# 19. NOTICE BOARD

## 19.1 Owner

```http
POST   /api/v1/properties/{property_id}/notices
GET    /api/v1/properties/{property_id}/notices
PATCH  /api/v1/notices/{id}
DELETE /api/v1/notices/{id}
```

## 19.2 Tenant

```http
GET /api/v1/tenancies/me/notices
POST /api/v1/notices/{id}/read
```

The backend should verify that the tenant actually belongs to the target property.

---

# 20. REVIEWS

The PRD specifies a two-sided review system and a blind-review period.

## 20.1 Review creation

```http
POST /api/v1/reviews
```

Only users involved in the relevant completed tenancy can review each other.

## 20.2 Anti-abuse rules

- reviewer must be part of tenancy,
- reviewee must be the opposite party,
- one review per reviewer/reviewee/tenancy,
- rating must be 1–5,
- review should not be publicly visible until the blind-review condition is satisfied.

## 20.3 Review visibility

Implement:

```text
is_public = false
```

until:
- both sides have reviewed, OR
- review period expires.

---

# 21. TRUST SCORE

The original PRD defines a 0–100 dynamic trust score.

For MVP, use deterministic rules.

Example:

```text
KYC approved                  +20
Phone verified                +10
Email verified                +5
Completed tenancy             +10
Good payment history          +20
Positive reviews              +20
Verified employment/student   +10
--------------------------------
Maximum                      100
```

Do not allow client-side trust score updates.

Create a service:

```python
calculate_trust_score(user_id)
```

Keep score calculation auditable.

Future versions may replace this with an ML model.

---

# 22. EMERGENCY SOS

## 22.1 Trigger endpoint

```http
POST /api/v1/emergency/trigger-sos
```

Request:

```json
{
  "lat": 23.7937,
  "lng": 90.4066,
  "alert_type": "SECURITY_INTRUDER",
  "emergency_message": "Immediate help needed."
}
```

## 22.2 Flow

```text
User presses SOS
      ↓
Authenticate JWT
      ↓
Validate location
      ↓
Create emergency_alert
      ↓
Find emergency contacts
      ↓
Find relevant roommates / owner
      ↓
Publish Redis event
      ↓
WebSocket broadcast
      ↓
Queue SMS/push notifications
      ↓
Write audit log
```

## 22.3 Emergency security

- Never expose SOS data publicly.
- Only authorized recipients/admins may receive location.
- Store minimal necessary location data.
- Log who resolved the incident.
- Rate-limit SOS endpoint while never making emergency access impossible.

---

# 23. WEBSOCKET DESIGN

Endpoint:

```text
/ws/v1/emergency
```

Authentication should happen during connection.

Suggested events:

```text
TRIGGER_SOS
SOS_BROADCAST_ALERT
SOS_ACKNOWLEDGED
SOS_RESOLVED
PING
PONG
```

Example server event:

```json
{
  "event": "SOS_BROADCAST_ALERT",
  "data": {
    "alert_id": "uuid",
    "sender": {
      "user_id": "uuid",
      "full_name": "User"
    },
    "coordinates": {
      "lat": 23.7937,
      "lng": 90.4066
    },
    "triggered_at": "2026-08-14T18:15:00Z"
  }
}
```

Use Redis Pub/Sub if multiple backend instances are running.

---

# 24. NOTIFICATION SYSTEM

Create a generic notification service.

Channels:

```text
IN_APP
EMAIL
SMS
PUSH
```

Interface:

```python
class NotificationProvider(Protocol):
    async def send(...): ...
```

MVP can implement:
- in-app database notification,
- console/log based mock SMS,
- mock email.

Production providers can be added later.

Notification events:

```text
USER_REGISTERED
KYC_SUBMITTED
KYC_APPROVED
BOOKING_CREATED
BOOKING_APPROVED
BOOKING_REJECTED
INVOICE_CREATED
PAYMENT_SUCCESS
PAYMENT_FAILED
INVOICE_OVERDUE
COMPLAINT_CREATED
COMPLAINT_UPDATED
NOTICE_PUBLISHED
SOS_TRIGGERED
SOS_RESOLVED
```

---

# 25. AUDIT LOGGING

The PRD requires audit logs for sensitive operations.

Log at least:

```text
actor_id
action_type
entity_name
entity_id
ip_address
user_agent
previous_state
new_state
created_at
```

Audit events should include:

```text
LOGIN_SUCCESS
LOGIN_FAILED
KYC_SUBMITTED
KYC_APPROVED
KYC_REJECTED
PROPERTY_CREATED
PROPERTY_UPDATED
PROPERTY_PUBLISHED
BOOKING_CREATED
BOOKING_APPROVED
BOOKING_REJECTED
TENANCY_CREATED
INVOICE_CREATED
PAYMENT_RECEIVED
COMPLAINT_CREATED
COMPLAINT_STATUS_CHANGED
SOS_TRIGGERED
SOS_RESOLVED
ADMIN_ACTION
```

Do not log passwords, raw access tokens, or sensitive document contents.

---

# 26. STANDARD API RESPONSE FORMAT

Use a consistent response format.

## Success

```json
{
  "success": true,
  "message": "Property created successfully.",
  "data": {
    "id": "uuid"
  }
}
```

## Error

```json
{
  "success": false,
  "message": "You are not authorized to modify this property.",
  "error": {
    "code": "FORBIDDEN",
    "details": null
  }
}
```

For validation errors:

```json
{
  "success": false,
  "message": "Validation failed.",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "email",
        "message": "Invalid email address."
      }
    ]
  }
}
```

Recommended HTTP statuses:

```text
200 OK
201 CREATED
204 NO CONTENT
400 BAD REQUEST
401 UNAUTHORIZED
403 FORBIDDEN
404 NOT FOUND
409 CONFLICT
422 VALIDATION ERROR
429 RATE LIMITED
500 INTERNAL SERVER ERROR
```

---

# 27. ERROR HANDLING

Create custom exceptions:

```python
class AppException(Exception):
    status_code: int
    code: str
    message: str
```

Examples:

```text
ResourceNotFoundError
PermissionDeniedError
ConflictError
InvalidStateTransitionError
PaymentVerificationError
KYCRequiredError
InvalidBookingError
```

FastAPI exception handlers should convert these into the standard error response.

Never return raw Python exceptions to clients.

---

# 28. CONFIGURATION

`.env.example` should include:

```env
APP_NAME=BachNest API
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bachnest

REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:3000

STORAGE_PROVIDER=local
STORAGE_BUCKET=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=

PAYMENT_PROVIDER=mock
BKASH_APP_KEY=
BKASH_APP_SECRET=
SSLCOMMERZ_STORE_ID=
SSLCOMMERZ_STORE_PASSWORD=

SMS_PROVIDER=mock
SMS_API_KEY=

EMAIL_PROVIDER=mock
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

Never commit `.env`.

---

# 29. DATABASE MIGRATIONS

Use Alembic.

Workflow:

```bash
alembic revision --autogenerate -m "create users and auth tables"
alembic upgrade head
```

Before generating migrations:
1. Check SQLAlchemy models.
2. Check relationships.
3. Check enum changes.
4. Check indexes.
5. Review generated migration manually.

Never blindly trust autogenerated migrations.

---

# 30. SEED DATA

Create development seed data.

Minimum:

```text
1 SUPER_ADMIN
2 ADMIN
3 OWNER
10 BACHELOR
5 PROPERTIES
10 ROOMS
10+ SEATS
several bookings
several active tenancies
sample invoices
sample complaints
sample notices
```

Seed data must use fake identities and fake documents.

Never use real NID/passport data.

---

# 31. API ENDPOINT MASTER LIST

## Auth

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/verify-phone
POST /api/v1/auth/verify-email
```

## Users

```text
GET   /api/v1/users/me
PATCH /api/v1/users/me
GET   /api/v1/users/{id}
```

## KYC

```text
POST  /api/v1/kyc
GET   /api/v1/kyc/me
PATCH /api/v1/kyc/{id}/resubmit
GET   /api/v1/admin/kyc
PATCH /api/v1/admin/kyc/{id}/decision
```

## Properties

```text
POST   /api/v1/properties
GET    /api/v1/properties/{id}
PATCH  /api/v1/properties/{id}
DELETE /api/v1/properties/{id}
GET    /api/v1/owner/properties
PATCH  /api/v1/properties/{id}/publish
```

## Rooms

```text
POST   /api/v1/properties/{property_id}/rooms
GET    /api/v1/properties/{property_id}/rooms
GET    /api/v1/rooms/{room_id}
PATCH  /api/v1/rooms/{room_id}
DELETE /api/v1/rooms/{room_id}
```

## Seats

```text
POST   /api/v1/rooms/{room_id}/seats
GET    /api/v1/rooms/{room_id}/seats
PATCH  /api/v1/seats/{seat_id}
DELETE /api/v1/seats/{seat_id}
```

## Search

```text
GET /api/v1/search/map
GET /api/v1/search/properties
GET /api/v1/search/roommates
```

## Bookings

```text
POST  /api/v1/bookings/request
GET   /api/v1/bookings/me
GET   /api/v1/bookings/{id}
PATCH /api/v1/bookings/{id}/decision
POST  /api/v1/bookings/{id}/cancel
```

## Tenancies

```text
GET   /api/v1/tenancies/me
GET   /api/v1/tenancies/{id}
PATCH /api/v1/tenancies/{id}/notice
PATCH /api/v1/tenancies/{id}/terminate
```

## Billing

```text
GET  /api/v1/billing/invoices
GET  /api/v1/billing/invoices/{id}
POST /api/v1/billing/invoices/{id}/calculate
```

## Payments

```text
POST /api/v1/payments/checkout
POST /api/v1/payments/webhook
GET  /api/v1/payments/{id}
```

## Complaints

```text
POST  /api/v1/complaints
GET   /api/v1/complaints
GET   /api/v1/complaints/{id}
PATCH /api/v1/complaints/{id}/status
POST  /api/v1/complaints/{id}/reopen
```

## Notices

```text
POST   /api/v1/properties/{property_id}/notices
GET    /api/v1/properties/{property_id}/notices
PATCH  /api/v1/notices/{id}
DELETE /api/v1/notices/{id}
POST   /api/v1/notices/{id}/read
```

## Reviews

```text
POST /api/v1/reviews
GET  /api/v1/users/{id}/reviews
```

## Emergency

```text
POST /api/v1/emergency/trigger-sos
GET  /api/v1/emergency/{id}
PATCH /api/v1/emergency/{id}/resolve
WS   /ws/v1/emergency
```

## Admin

```text
GET   /api/v1/admin/dashboard
GET   /api/v1/admin/users
PATCH /api/v1/admin/users/{id}/status
GET   /api/v1/admin/properties/pending
PATCH /api/v1/admin/properties/{id}/verify
GET   /api/v1/admin/complaints
GET   /api/v1/admin/emergency
GET   /api/v1/admin/audit-logs
```

---

# 32. API DOCUMENTATION

FastAPI should expose:

```text
/docs
/redoc
/openapi.json
```

Every endpoint must have:
- summary,
- description,
- request schema,
- response schema,
- possible error responses,
- authorization requirement.

Use tags:

```text
Auth
Users
KYC
Properties
Rooms
Search
Bookings
Tenancies
Billing
Payments
Complaints
Notices
Reviews
Emergency
Admin
```

---

# 33. TESTING STRATEGY

Use:

```text
pytest
pytest-asyncio
httpx
```

## 33.1 Unit tests

Test:

```text
password hashing
JWT generation
JWT validation
trust score
roommate compatibility
invoice calculation
utility split
late fee calculation
booking state transition
complaint state transition
permission checks
```

## 33.2 Integration tests

Test:

```text
registration → login
owner → property → room
bachelor → search → booking
booking → approval → tenancy
tenancy → invoice
invoice → payment
tenant → complaint
owner → complaint resolution
SOS → event creation
```

## 33.3 Critical concurrency tests

Test:
- two users trying to book the same seat,
- duplicate payment webhook,
- duplicate monthly invoice generation.

These must not create duplicate inventory allocation, payment credit, or invoice.

---

# 34. SECURITY CHECKLIST

Before considering backend MVP complete:

- [ ] Passwords hashed securely.
- [ ] JWT secret loaded from environment.
- [ ] Refresh token handling implemented.
- [ ] RBAC implemented.
- [ ] Object-level authorization implemented.
- [ ] SQL injection prevented through ORM/parameterized queries.
- [ ] Input validation through Pydantic.
- [ ] File type/size validation.
- [ ] KYC files private.
- [ ] Rate limiting on login and sensitive endpoints.
- [ ] CORS restricted in production.
- [ ] Security headers handled at gateway/proxy layer.
- [ ] Payment webhook signature verification.
- [ ] Webhook idempotency.
- [ ] Audit logs for sensitive actions.
- [ ] No secrets in source code.
- [ ] No passwords/tokens in logs.
- [ ] Sensitive PII not unnecessarily returned from APIs.

---

# 35. RATE LIMITING

Use Redis for distributed rate limiting.

Recommended initial limits:

```text
POST /auth/login             10 requests / 5 minutes / IP
POST /auth/register          5 requests / hour / IP
POST /emergency/trigger-sos  carefully controlled; do not block legitimate emergencies
POST /payments/checkout      20 requests / hour / user
POST /complaints             20 requests / hour / user
```

Exact limits should be configurable.

---

# 36. CACHING

Cache only data that is safe to cache.

Good candidates:

```text
public property search
property details
public property metadata
```

Do NOT blindly cache:

```text
payment status
private KYC
private tenancy information
financial ledger
SOS state
```

Use cache invalidation when property/room availability changes.

Example:

```text
property:{id}
search:{hash_of_query}
```

---

# 37. CELERY TASKS

Required tasks:

```python
generate_monthly_invoices()
send_invoice_reminders()
mark_overdue_invoices()
send_notification()
process_kyc_document()
cleanup_expired_tokens()
```

Schedule:

```text
monthly invoice generation
daily overdue check
periodic reminder
```

All scheduled tasks must be idempotent.

---

# 38. BACKGROUND JOB IDEMPOTENCY

For every scheduled job ask:

> "What happens if this task runs twice?"

Example invoice generation:

```text
Check:
tenancy_id + billing_month_year exists?
    YES → skip
    NO  → create
```

Example notification:

```text
event_id + recipient_id + channel
```

can be used as an idempotency key.

---

# 39. MONEY AND DATE RULES

## Money

Always:

```python
from decimal import Decimal
```

Never:

```python
float
```

for financial calculations.

## Dates

Use:
- `date` for billing/lease dates,
- timezone-aware `datetime` for events and timestamps.

Store timestamps in UTC.

Display in Bangladesh local time at the frontend.

---

# 40. TRANSACTION RULES

Use database transactions for:

### Booking approval

```text
lock booking
validate
reserve room/seat
update booking
create tenancy
audit
commit
```

### Payment

```text
lock invoice
verify gateway
check idempotency
create payment
update invoice paid amount/status
audit
commit
```

### Invoice generation

```text
lock/check tenancy
check duplicate invoice
calculate
create invoice
create notification
commit
```

---

# 41. LOGGING AND OBSERVABILITY

Every request should have a request ID.

Example:

```text
X-Request-ID: uuid
```

Structured logs should include:

```text
timestamp
request_id
user_id
route
method
status_code
duration_ms
```

Never log:
- passwords,
- JWTs,
- raw NID,
- private KYC document content,
- payment secrets.

---

# 42. HEALTH ENDPOINTS

Implement:

```http
GET /api/v1/health
GET /api/v1/health/db
GET /api/v1/health/redis
```

Response:

```json
{
  "status": "ok"
}
```

For `/health/db` and `/health/redis`, return dependency status.

These endpoints are needed for Docker and deployment health checks.

---

# 43. DOCKER DEVELOPMENT SETUP

Development `docker-compose.yml` should contain:

```text
postgres
redis
api
celery_worker
celery_beat
```

Frontend may be run separately during backend development.

Recommended local ports:

```text
FastAPI     8000
PostgreSQL  5432
Redis       6379
```

---

# 44. DEVELOPMENT ORDER

Claude should implement the backend in this exact sequence.

## Step 1 — Foundation

- [ ] Initialize Python project.
- [ ] Add FastAPI.
- [ ] Add SQLAlchemy async.
- [ ] Add asyncpg.
- [ ] Add Alembic.
- [ ] Add Pydantic Settings.
- [ ] Add PostgreSQL/PostGIS.
- [ ] Add Redis.
- [ ] Add structured logging.
- [ ] Create `/health`.

## Step 2 — Database

- [ ] Create base model.
- [ ] Create User.
- [ ] Create KYC.
- [ ] Create RoommatePreference.
- [ ] Create Property.
- [ ] Create Room.
- [ ] Create RoomSeat.
- [ ] Create PropertyMedia.
- [ ] Create Booking.
- [ ] Create Tenancy.
- [ ] Create Invoice.
- [ ] Create Payment.
- [ ] Create Complaint.
- [ ] Create Notice.
- [ ] Create EmergencyAlert.
- [ ] Create EmergencyContact.
- [ ] Create Review.
- [ ] Create Notification.
- [ ] Create AuditLog.
- [ ] Generate/review migrations.

## Step 3 — Auth

- [ ] Register.
- [ ] Login.
- [ ] Access JWT.
- [ ] Refresh JWT.
- [ ] Logout/revocation strategy.
- [ ] Current user.
- [ ] RBAC.
- [ ] Object-level authorization.

## Step 4 — KYC

- [ ] Submission.
- [ ] Status.
- [ ] Admin approval/rejection.
- [ ] Mock provider.
- [ ] Private file handling.

## Step 5 — Property Inventory

- [ ] Property CRUD.
- [ ] Room CRUD.
- [ ] Seat CRUD.
- [ ] Media upload abstraction.
- [ ] Publish/unpublish.
- [ ] Admin verification.

## Step 6 — Search

- [ ] Text search.
- [ ] Filters.
- [ ] PostGIS radius.
- [ ] Bounding box.
- [ ] Distance sorting.
- [ ] Pagination.
- [ ] Redis caching.

## Step 7 — Booking and Tenancy

- [ ] Booking request.
- [ ] Owner decision.
- [ ] Cancellation.
- [ ] Inventory locking.
- [ ] Tenancy creation.
- [ ] Notice/termination.

## Step 8 — Billing

- [ ] Invoice model.
- [ ] Invoice calculation.
- [ ] Utility splitting.
- [ ] Monthly Celery task.
- [ ] Overdue state.
- [ ] Late fee.

## Step 9 — Payments

- [ ] Payment abstraction.
- [ ] Mock gateway.
- [ ] Checkout.
- [ ] Webhook.
- [ ] Idempotency.
- [ ] Invoice update.

## Step 10 — Complaints and Notices

- [ ] Complaint creation.
- [ ] SLA.
- [ ] Status transitions.
- [ ] Owner resolution.
- [ ] Notice creation/read tracking.

## Step 11 — Reviews and Trust

- [ ] Review rules.
- [ ] Blind review.
- [ ] Trust score.
- [ ] Review aggregation.

## Step 12 — SOS

- [ ] Emergency contacts.
- [ ] SOS endpoint.
- [ ] WebSocket.
- [ ] Redis Pub/Sub.
- [ ] Mock notification dispatch.
- [ ] Resolution workflow.

## Step 13 — Admin

- [ ] KYC queue.
- [ ] Property moderation.
- [ ] User management.
- [ ] Complaint dashboard.
- [ ] Emergency console.
- [ ] Audit log viewer.

## Step 14 — Quality

- [ ] Unit tests.
- [ ] Integration tests.
- [ ] Concurrency tests.
- [ ] API documentation.
- [ ] Docker.
- [ ] Seed script.
- [ ] README.

---

# 45. CLAUDE CODE EXECUTION PROTOCOL

When using this document with Claude Code, do NOT ask Claude to generate the entire backend in one giant response.

Use incremental implementation.

### Prompt pattern

```text
Read BachNest_Backend_Implementation_Spec_for_Claude.md.

You are implementing the BachNest FastAPI backend.

First inspect the existing repository.
Do not rewrite working code unnecessarily.
Follow the architecture and business rules in the specification.

For this task implement only:
[ONE MODULE]

Requirements:
1. Create/update models.
2. Create/update Pydantic schemas.
3. Create service layer.
4. Create API router.
5. Add migrations if database changes are needed.
6. Add tests.
7. Update README/API documentation if needed.
8. Run tests and fix failures.

Do not implement unrelated modules.
Do not invent business rules.
At the end, report:
- files changed
- endpoints added
- database changes
- tests added
- remaining TODOs
```

---

# 46. FIRST CLAUDE TASK

Use this as the first implementation prompt:

```text
Read the complete BachNest_Backend_Implementation_Spec_for_Claude.md.

We are starting the BachNest backend from scratch.

Implement ONLY the backend foundation.

Tasks:
1. Create FastAPI application.
2. Configure Pydantic Settings.
3. Configure async SQLAlchemy 2.x.
4. Configure PostgreSQL/PostGIS connection.
5. Configure Redis connection.
6. Configure Alembic.
7. Create project directory structure.
8. Create custom exception system.
9. Create structured logging.
10. Create GET /api/v1/health.
11. Create GET /api/v1/health/db.
12. Create GET /api/v1/health/redis.
13. Create .env.example.
14. Create Dockerfile.
15. Create development docker-compose.yml.
16. Add requirements/pyproject configuration.
17. Add a basic pytest setup.

Do NOT implement authentication, properties, booking, payment, KYC, or other business modules yet.

After implementation:
- run the test suite,
- verify database connection,
- verify Redis connection,
- verify FastAPI starts,
- show the final file tree,
- explain exactly how to run the backend locally.
```

---

# 47. SECOND CLAUDE TASK — AUTH

After foundation is stable:

```text
Read the BachNest backend specification.

Implement ONLY authentication and authorization.

Implement:
1. User model.
2. UserRole enum.
3. Gender enum.
4. Registration.
5. Login.
6. Access JWT.
7. Refresh token.
8. Password hashing using Argon2id.
9. Current-user dependency.
10. Role-based dependencies.
11. Object-level authorization helpers.
12. Logout/revocation strategy appropriate for the current architecture.
13. Auth tests.
14. Migration.
15. OpenAPI documentation.

Endpoints:
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET /api/v1/users/me
PATCH /api/v1/users/me

Do not implement KYC or property modules yet.
```

---

# 48. THIRD CLAUDE TASK — PROPERTY + ROOMS

```text
Implement the BachNest property inventory module only.

Implement:
- Property model
- Room model
- RoomSeat model
- PropertyMedia model
- SQLAlchemy relationships
- Pydantic schemas
- Owner-only CRUD
- Object-level authorization
- Publish/unpublish
- Admin verification
- Inventory validation
- Tests
- Alembic migration

Endpoints must follow the master specification.

Do not implement booking or payments yet.
```

---

# 49. FOURTH CLAUDE TASK — SEARCH

```text
Implement the BachNest search module.

Requirements:
- PostgreSQL/PostGIS
- radius search
- bounding box search
- city/area filtering
- budget filtering
- room type filtering
- amenity filters
- distance calculation
- pagination
- safe query construction
- appropriate spatial/text indexes
- Redis caching
- cache invalidation when property availability changes
- tests

Do not implement booking, payments, or roommate matching in this task.
```

---

# 50. FIFTH CLAUDE TASK — BOOKING + TENANCY

```text
Implement booking and tenancy lifecycle.

Implement:
- booking creation
- booking validation
- owner approve/reject
- cancellation
- booking state machine
- inventory race-condition protection
- tenancy creation
- tenancy status
- notice
- termination
- audit logs
- tests including two users trying to book the same seat

Use database transactions.
Do not implement real payment gateway yet.
Use a mock token-deposit mechanism if needed.
```

---

# 51. SIXTH CLAUDE TASK — BILLING

```text
Implement billing and monthly invoicing.

Implement:
- invoice model/service
- invoice number
- monthly billing period
- base rent
- service charge
- utilities
- utility split
- total calculation using Decimal
- due date
- overdue state
- configurable late fee
- Celery monthly invoice task
- idempotent invoice generation
- tests

Do not integrate a real payment gateway yet.
```

---

# 52. SEVENTH CLAUDE TASK — PAYMENT

```text
Implement the payment abstraction and mock gateway.

Requirements:
- PaymentGateway interface
- MockPaymentGateway
- checkout endpoint
- webhook endpoint
- transaction verification
- amount verification
- invoice locking
- webhook idempotency
- payment record
- invoice status update
- audit log
- tests

Do not add real bKash or SSLCommerz credentials.
```

---

# 53. EIGHTH CLAUDE TASK — COMPLAINTS

```text
Implement the maintenance/complaint module.

Implement:
- complaint creation
- categories
- priority
- SLA deadline
- status machine
- owner access
- tenant access
- admin access
- evidence metadata
- cost bearer
- repair cost
- resolution
- reopen
- audit logs
- tests
```

---

# 54. NINTH CLAUDE TASK — SOS

```text
Implement the BachNest emergency SOS module.

Implement:
- emergency contacts
- SOS database model
- SOS REST endpoint
- WebSocket endpoint
- authenticated WebSocket connections
- Redis Pub/Sub
- broadcast to relevant recipients
- incident resolution
- audit logging
- tests

Use mock SMS/push providers.
Do not integrate real emergency-service APIs.
```

---

# 55. DEFINITION OF DONE

A module is NOT complete just because the endpoint works.

A module is complete only when:

```text
[ ] Model exists
[ ] Migration exists
[ ] Request schema exists
[ ] Response schema exists
[ ] Service exists
[ ] Router exists
[ ] Authentication is correct
[ ] Authorization is correct
[ ] Validation is correct
[ ] Transactions are correct
[ ] Errors are standardized
[ ] Audit logging exists where needed
[ ] Tests exist
[ ] Tests pass
[ ] OpenAPI docs are correct
[ ] README is updated
```

---

# 56. IMPORTANT IMPLEMENTATION DECISIONS

## 56.1 Do not over-engineer the FYDP

The original architecture mentions:
- Nginx,
- WAF,
- AWS,
- Kubernetes,
- replicas,
- 1,500 RPS,
- 99.95% availability,
- production-grade external integrations.

Those are useful production targets, but they are not prerequisites for the first working backend.

For the FYDP implementation, prioritize:

```text
Correctness
>
Security
>
Testability
>
Maintainability
>
Performance optimization
>
Cloud scaling
```

## 56.2 Start with a modular monolith

Do not split Auth, Billing, Search, Booking, etc. into separate microservices.

Use:

```text
One FastAPI application
+
PostgreSQL
+
Redis
+
Celery
```

This is easier to develop, debug, test, and demonstrate.

## 56.3 External services should be replaceable

Always use adapters for:

```text
Payment
SMS
Email
Storage
KYC
```

This allows:

```text
Mock provider → Development
Real provider → Production
```

without rewriting business logic.

---

# 57. SOURCE-ALIGNMENT NOTES

The original BachNest PRD defines:
- FastAPI/Python backend,
- PostgreSQL + PostGIS,
- Redis,
- Celery,
- JWT/RBAC,
- KYC,
- property/room/seat inventory,
- geospatial search,
- booking,
- tenancy,
- rent ledger,
- payment gateways,
- complaint ticketing,
- notice board,
- reviews,
- SOS,
- admin tools,
- backend directory structure,
- Docker/deployment concepts,
- and a four-phase implementation roadmap.

This document keeps those core concepts but turns them into a more practical backend-first execution plan.

Where this document says **"implementation refinement"**, it means a development-oriented clarification added to make the original requirements safer or easier to implement; it does not mean the original product requirement has been removed.

---

# 58. FINAL BACKEND BUILD TARGET

At the end of the MVP, the backend should support this complete demo:

```text
1. Bachelor registers
        ↓
2. Bachelor logs in
        ↓
3. Bachelor submits KYC
        ↓
4. Admin approves KYC
        ↓
5. Owner registers
        ↓
6. Owner creates property
        ↓
7. Owner creates rooms/seats
        ↓
8. Admin verifies property
        ↓
9. Bachelor searches nearby properties
        ↓
10. Bachelor filters by budget/room/amenities
        ↓
11. Bachelor opens property details
        ↓
12. Bachelor submits booking
        ↓
13. Owner approves booking
        ↓
14. Tenancy becomes active
        ↓
15. Monthly invoice is generated
        ↓
16. Bachelor pays using mock gateway
        ↓
17. Invoice becomes PAID
        ↓
18. Bachelor submits maintenance complaint
        ↓
19. Owner changes complaint status
        ↓
20. Owner publishes building notice
        ↓
21. Bachelor can trigger SOS
        ↓
22. Relevant recipients receive real-time alert
        ↓
23. Tenancy ends
        ↓
24. Both sides submit reviews
        ↓
25. Trust score is updated
```

If all of the above works with automated tests, the BachNest backend has a strong FYDP/MVP foundation.

---

# 59. CLAUDE'S GOLDEN RULE

**Implement one module at a time, keep business logic in services, keep persistence in PostgreSQL, use Redis only where it adds value, make external integrations replaceable, validate every state transition, secure every private resource, and write tests before declaring a module complete.**