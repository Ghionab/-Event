# Enhanced Ticket Purchase Flow - Visual Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ENHANCED TICKET PURCHASE SYSTEM              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   MODELS     │         │    VIEWS     │         │  TEMPLATES   │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ Registration │◄────────│ enhanced_    │────────►│ step1.html   │
│ Question     │         │ register_    │         │ step2.html   │
│ TicketAnswer │         │ for_event()  │         │ step3.html   │
│ TicketType   │         │              │         │              │
│ Event        │         │ handle_      │         │ question_    │
│ User         │         │ step_1/2/3() │         │ form.html    │
└──────────────┘         └──────────────┘         └──────────────┘
```

## Purchase Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                             │
└─────────────────────────────────────────────────────────────────┘

START: User clicks "Register" on Event Page
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: SELECT TICKETS                                          │
├─────────────────────────────────────────────────────────────────┤
│ • Choose ticket type (VIP, Regular, Early Bird, etc.)          │
│ • Select quantity (1-10 tickets)                               │
│ • Apply promo code (optional)                                  │
│ • View real-time price calculation                             │
│                                                                 │
│ [Ticket Type: VIP ▼]  [Quantity: 2 ▼]                         │
│ [Promo Code: ________] [Apply]                                 │
│                                                                 │
│ Order Summary:                                                  │
│   Ticket Price: $100.00                                        │
│   Quantity: 2                                                  │
│   Subtotal: $200.00                                            │
│   Discount: -$20.00                                            │
│   Total: $180.00                                               │
│                                                                 │
│ [Back to Event] ────────────────────────── [Continue →]        │
└─────────────────────────────────────────────────────────────────┘
  │
  │ POST: Store in session
  │ - ticket_type_id
  │ - quantity
  │ - promo_code
  │ - pricing details
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: ATTENDEE INFORMATION                                    │
├─────────────────────────────────────────────────────────────────┤
│ Order Summary: VIP × 2 = $180.00                               │
│                                                                 │
│ ☑ Use same information for all tickets                         │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 🎫 Ticket 1 - Attendee Information                      │   │
│ │ ✓ Your information has been pre-filled (editable)      │   │
│ │                                                         │   │
│ │ Full Name: [John Doe____________] *                    │   │
│ │ Email:     [john@example.com____] *                    │   │
│ │ Phone:     [+1234567890_________]                      │   │
│ │                                                         │   │
│ │ Additional Information:                                 │   │
│ │ Company Name: [Acme Corp________] *                    │   │
│ │ T-Shirt Size: [L ▼] *                                  │   │
│ │ Dietary Pref: ○ None ● Vegetarian ○ Vegan            │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 🎫 Ticket 2 - Attendee Information                      │   │
│ │                 