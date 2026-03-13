# Enhanced Ticket Purchase System - Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PARTICIPANT FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. Browse Events → 2. Select Event → 3. Click "Purchase Tickets"
                                              ↓
                        ┌─────────────────────────────────┐
                        │   Enhanced Purchase Flow        │
                        │   (4-Step Process)              │
                        └─────────────────────────────────┘
                                      ↓
        ┌─────────────────────────────────────────────────────┐
        │                                                       │
   ┌────▼────┐    ┌──────────┐    ┌──────────┐    ┌─────────▼────┐
   │ STEP 1  │───▶│  STEP 2  │───▶│  STEP 3  │───▶│    STEP 4    │
   │ Select  │    │ Attendee │    │  Custom  │    │   Review &   │
   │ Tickets │    │   Info   │    │Questions │    │   Payment    │
   └─────────┘    └──────────┘    └──────────┘    └──────────────┘
                         │                                  │
                         │ Auto-fill from                   │
                         │ User Profile                     │
                         ↓                                  ↓
                  ┌──────────────┐              ┌──────────────────┐
                  │  User Model  │              │ Promo Code Check │
                  └──────────────┘              └──────────────────┘
                                                          ↓
                                              ┌──────────────────────┐
                                              │  Create Purchase     │
                                              │  + Tickets           │
                                              │  + Answers           │
                                              └──────────────────────┘
                                                          ↓
                                              ┌──────────────────────┐
                                              │  Success Page        │
                                              │  (QR Codes)          │
                                              └──────────────────────┘
```

## Data Model Relationships

```
┌──────────────────────────────────────────────────────────────────┐
│                      DATABASE SCHEMA                              │
└──────────────────────────────────────────────────────────────────┘

┌─────────────┐
│    User     │ (Django Auth)
│─────────────│
│ id          │
│ email       │
│ first_name  │
│ last_name   │
│ phone       │
└──────┬──────┘
       │
       │ buyer (FK)
       │
       ↓
┌──────────────────┐
│ TicketPurchase   │ ◄─────────┐
│──────────────────│            │
│ id               │            │
│ buyer_id         │            │
│ event_id         │            │
│ purchase_number  │            │ One Purchase
│ total_amount     │            │ Many Tickets
│ discount_amount  │            │
│ promo_code_id    │            │
│ payment_status   │            │
│ payment_method   │            │
│ created_at       │            │
└────────┬─────────┘            │
         │                      │
         │ purchase (FK)        │
         │                      │
         ↓                      │
┌──────────────────┐            │
│     Ticket       │────────────┘
│──────────────────│
│ id               │
│ purchase_id      │
│ event_id         │
│ ticket_type_id   │
│ ticket_number    │
│ attendee_name    │ ◄── Can differ from buyer
│ attendee_email   │ ◄── Can differ from buyer
│ attendee_phone   │ ◄── Can differ from buyer
│ status           │
│ qr_code          │
│ checked_in_at    │
│ checked_in_by_id │
└────────┬─────────┘
         │
         │ ticket (FK)
         │
         ↓
┌──────────────────┐
│  TicketAnswer    │
│──────────────────│
│ id               │
│ ticket_id        │
│ question_id      │ ◄── Links to RegistrationField
│ answer           │
└──────────────────┘


┌──────────────────────┐
│  RegistrationField   │ (Custom Questions)
│──────────────────────│
│ id                   │
│ event_id             │
│ field_name           │
│ field_type           │
│ label                │
│ required             │
│ options              │
│ order                │
└──────────────────────┘
```

## Purchase Flow Sequence

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Participant│    │  View    │    │   API    │    │ Database │
└─────┬────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
      │              │               │               │
      │ Load Page    │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │              │ Get User Info │               │
      │              ├──────────────▶│               │
      │              │               │               │
      │              │◀──────────────┤               │
      │              │ {name, email} │               │
      │              │               │               │
      │ Select       │               │               │
      │ Tickets      │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │ Fill         │               │               │
      │ Attendee     │               │               │
      │ Info         │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │ Answer       │               │               │
      │ Questions    │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │ Apply Promo  │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │              │ Validate      │               │
      │              │ Promo         │               │
      │              ├──────────────▶│               │
      │              │               │ Check Code    │
      │              │               ├──────────────▶│
      │              │               │               │
      │              │               │◀──────────────┤
      │              │               │ Valid/Invalid │
      │              │◀──────────────┤               │
      │              │               │               │
      │ Submit       │               │               │
      │ Purchase     │               │               │
      ├─────────────▶│               │               │
      │              │               │               │
      │              │ Create        │               │
      │              │ Purchase      │               │
      │              ├──────────────▶│               │
      │              │               │               │
      │              │               │ BEGIN TRANSACTION
      │              │               ├──────────────▶│
      │              │               │ Create Purchase
      │              │               ├──────────────▶│
      │              │               │ Create Tickets
      │              │               ├──────────────▶│
      │              │               │ Create Answers
      │              │               ├──────────────▶│
      │              │               │ Update Inventory
      │              │               ├──────────────▶│
      │              │               │ COMMIT
      │              │               ├──────────────▶│
      │              │               │               │
      │              │◀──────────────┤               │
      │              │ Success       │               │
      │◀─────────────┤               │               │
      │ Redirect     │               │               │
      │              │               │               │
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Templates)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ enhanced_        │  │ purchase_        │  │ my_          │ │
│  │ purchase.html    │  │ success.html     │  │ purchases.   │ │
│  │                  │  │                  │  │ html         │ │
│  │ - 4 Steps        │  │ - Confirmation   │  │ - History    │ │
│  │ - Auto-fill      │  │ - QR Codes       │  │ - List       │ │
│  │ - Validation     │  │ - Details        │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Django Views)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  views_enhanced.py                                       │  │
│  │                                                          │  │
│  │  - enhanced_ticket_purchase()                           │  │
│  │  - handle_ticket_purchase_submission()                  │  │
│  │  - purchase_success()                                   │  │
│  │  - my_purchases()                                       │  │
│  │  - purchase_detail()                                    │  │
│  │  - get_user_info_api()                                  │  │
│  │  - validate_promo_code_api()                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FORMS (Validation)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  forms_enhanced.py                                       │  │
│  │                                                          │  │
│  │  - TicketPurchaseForm                                   │  │
│  │  - AttendeeInfoForm (with auto-fill)                    │  │
│  │  - CustomQuestionForm (dynamic)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MODELS (Data Layer)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ TicketPurchase   │  │   Ticket     │  │  TicketAnswer   │  │
│  │                  │  │              │  │                 │  │
│  │ - buyer          │  │ - purchase   │  │ - ticket        │  │
│  │ - event          │  │ - attendee_* │  │ - question      │  │
│  │ - total_amount   │  │ - qr_code    │  │ - answer        │  │
│  │ - promo_code     │  │ - status     │  │                 │  │
│  └──────────────────┘  └──────────────┘  └─────────────────┘  │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE (PostgreSQL)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Buyer vs Attendee Separation
```
Purchase (Buyer: john@example.com)
  ├── Ticket 1 (Attendee: jane@example.com)
  ├── Ticket 2 (Attendee: bob@example.com)
  └── Ticket 3 (Attendee: alice@example.com)
```
**Why:** Allows one person to buy tickets for multiple people

### 2. One Ticket = One Attendee
```
Ticket
  ├── attendee_name
  ├── attendee_email
  ├── attendee_phone
  └── answers (custom questions)
```
**Why:** Each ticket has its own attendee info and QR code

### 3. Custom Questions Per Ticket
```
Ticket 1 Answers:
  ├── Company: ABC Corp
  ├── Dietary: Vegetarian
  └── T-Shirt: M

Ticket 2 Answers:
  ├── Company: XYZ Inc
  ├── Dietary: None
  └── T-Shirt: L
```
**Why:** Different attendees may have different answers

### 4. Transaction-Based Purchase
```
BEGIN TRANSACTION
  1. Create TicketPurchase
  2. Create Tickets (loop)
  3. Create TicketAnswers (loop)
  4. Update ticket inventory
  5. Apply promo code
COMMIT
```
**Why:** Ensures data consistency, all-or-nothing approach

## Security Considerations

1. **Authentication Required:** Users must be logged in
2. **CSRF Protection:** All forms include CSRF tokens
3. **Input Validation:** Server-side validation on all inputs
4. **SQL Injection Prevention:** Django ORM prevents SQL injection
5. **XSS Protection:** Django templates auto-escape output
6. **Transaction Safety:** Database transactions ensure consistency

## Performance Optimizations

1. **Prefetch Related:** Use `prefetch_related('tickets')` for purchases
2. **Select Related:** Use `select_related('ticket_type')` for tickets
3. **Database Indexing:** Indexes on foreign keys and unique fields
4. **Caching:** Can add caching for event and ticket type data
5. **Lazy Loading:** QR codes generated on-demand

## Scalability

The system is designed to scale:
- **Horizontal Scaling:** Stateless views can run on multiple servers
- **Database Scaling:** Can use read replicas for purchase history
- **Caching Layer:** Redis can cache event and ticket data
- **Queue System:** Can add Celery for email notifications
- **CDN:** Static assets (CSS, JS) can be served via CDN

---

This architecture provides a solid foundation for a professional ticket purchase system that can grow with your platform.
