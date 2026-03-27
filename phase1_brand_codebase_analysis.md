# Phase 1 — Brand System Summary & Codebase Analysis

## 1. Branding Guide Extraction

From the provided **EventAxis Branding Guide**:

| Token | Value | Usage |
|---|---|---|
| **Primary Color** | `#1F3A5F` | Dark navy blue — navbar, sidebar, primary buttons |
| **Accent Color** | `#C8A24A` | Gold — CTAs, highlights, active states, badges |
| **Background** | `#F5F6F7` | Light gray — page backgrounds |
| **Text Color** | `#2B2B2B` | Near-black — body text |

### Typography
- **Headings**: Poppins / Montserrat (bold, semi-bold)
- **Body**: Inter / Open Sans (regular, medium)

### UI Guidelines
- **Buttons**: Blue primary (`#1F3A5F`), Gold accent (`#C8A24A`)
- **Cards**: White with soft shadows
- **Navbar**: Dark blue with white text
- **Personality**: Modern, professional, tech-driven, urban Ethiopian identity

---

## 2. Logo Color Extraction

From the **EventAxis logo**:

| Color | HEX | Role |
|---|---|---|
| Dark Navy | `#1F3A5F` | Primary — outlines, compass, text "Event" |
| Gold | `#C8A24A` | Accent — "Axis" text, compass detail, "LIVE" badge |
| White | `#FFFFFF` | Card/container backgrounds |
| Light Gray | `#F5F6F7` | Background surfaces |

**Visual style**: Shield-shaped frame, Ethiopian city skyline silhouette, compass rose motif. Tone is professional, authoritative, modern.

---

## 3. Final Brand System (Confirmed)

### Color Palette

| Token | HEX | Usage |
|---|---|---|
| `--ea-primary` | `#1F3A5F` | Navbar, sidebar, primary buttons, links |
| `--ea-primary-dark` | `#162C48` | Hover states for primary |
| `--ea-primary-light` | `#2A4F7A` | Lighter variant for backgrounds |
| `--ea-accent` | `#C8A24A` | CTAs, highlights, badges, active indicators |
| `--ea-accent-dark` | `#B08E3A` | Hover states for accent |
| `--ea-accent-light` | `#D4B56A` | Lighter accent for backgrounds |
| `--ea-bg` | `#F5F6F7` | Page backgrounds |
| `--ea-bg-white` | `#FFFFFF` | Cards, modals, containers |
| `--ea-text` | `#2B2B2B` | Primary body text |
| `--ea-text-light` | `#6B7280` | Secondary/muted text |
| `--ea-text-lighter` | `#9CA3AF` | Placeholder/subtle text |
| `--ea-border` | `#E5E7EB` | Borders, dividers |
| `--ea-success` | `#059669` | Success states (kept standard) |
| `--ea-error` | `#DC2626` | Error states (kept standard) |
| `--ea-warning` | `#D97706` | Warning states (kept standard) |

### Typography Pairing
- **Headings**: `'Poppins', 'Montserrat', sans-serif` — weights 600, 700
- **Body**: `'Inter', 'Open Sans', sans-serif` — weights 400, 500

### UI Style Direction
- **Tone**: Clean, minimal, professional — inspired by Stripe/Linear
- **Corners**: 8–16px border-radius
- **Shadows**: Soft (`0 1px 3px rgba(0,0,0,0.1)`) to medium (`0 4px 12px rgba(0,0,0,0.08)`)
- **Spacing**: 8px grid system
- **Animations**: Subtle transitions (200–300ms)

---

## 4. Codebase Analysis — Current Frontend Architecture

### Portal Structure (5 Portals)

| Portal | Base Template | Framework | Templates | Layout |
|---|---|---|---|---|
| **Organizer** | [organizers/templates/organizers/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/organizers/templates/organizers/base.html) | Tailwind CDN + custom CSS | 43 | Fixed sidebar + top header |
| **Participant** | [templates/participant/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/templates/participant/base.html) | Tailwind CDN | 44 | Top navbar + footer |
| **Events (Public)** | [events/templates/events/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/events/templates/events/base.html) | Tailwind CDN | — | Top navbar + footer |
| **Coordinator** | [coordinators/templates/coordinators/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/coordinators/templates/coordinators/base.html) | Bootstrap 5.3 | 3 | Sidebar + top bar |
| **Staff** | [staff/templates/staff/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/staff/templates/staff/base.html) | Bootstrap 5.3.2 | 5 | Header bar |
| **Shared** | [templates/base.html](file:///c:/Users/zefasil/Desktop/cloning%20to%20test%20and%20work%20my%20part/Intern-project/templates/base.html) | Bootstrap 5.1 | — | Simple navbar |

### Shared App Templates

| App | Templates | Types |
|---|---|---|
| `advanced` | 28 | Vendors, contracts, tasks, team, ushers, security |
| `business` | 8 | Analytics, expenses, invoices, reports, sponsors |
| `communication` | 8 | Email templates, polls, Q&A, reminders, logs |
| `registration` | 7 | Ticket purchase, badges, QR emails |

### Current Problems

1. **No brand alignment** — Uses generic indigo `#4f46e5` and purple gradients everywhere
2. **Named "EventHub/EventPortal"** — Not "EventAxis" in any UI
3. **Inconsistent frameworks** — Mix of Tailwind CDN and Bootstrap across portals
4. **No shared CSS** — Zero `.css` files; all 419 lines of CSS are inline in base templates
5. **No design tokens** — Colors hardcoded individually in each template
6. **No Google Fonts** — Uses system fonts instead of Poppins/Inter

---

## 5. Key UI Components Identified (per portal)

### Organizer Portal (Primary Refactor Target)
- ✅ **Sidebar** — Dark gradient, collapsible, section-grouped nav items
- ✅ **Top Header** — Page title, user menu dropdown, notification bell
- ✅ **Stat Cards** — Icon + number + label
- ✅ **Cards** — White with shadows, header + body
- ✅ **Messages** — Success/error/info with colored backgrounds
- ✅ **User Dropdown** — Profile, settings, logout

### Participant Portal
- ✅ **Top Navbar** — Logo, nav links, notification/message dropdowns, user avatar
- ✅ **Mobile Menu** — Hamburger toggle, responsive links
- ✅ **Toast Notifications** — Slide-in, auto-dismiss
- ✅ **Footer** — 4-column grid (brand, links, support, social)

### Coordinator Portal
- ✅ **Sidebar** — Purple gradient, simple 3-item nav
- ✅ **Top Bar** — Page title, action buttons
- ✅ **Alert Messages** — Bootstrap alerts

### Staff Portal
- ✅ **Staff Header** — Gradient banner, user info, logout
- ✅ **Stats Cards** — Icon + number + label
- ✅ **Attendee Cards** — Left-bordered, check-in states
- ✅ **Scan Button** — Large gradient CTA
- ✅ **Audio Feedback System** — Success/error beeps for scanning

---

> [!IMPORTANT]
> **Phase 1 is complete.** No code changes have been made. This analysis provides the foundation for Phase 2 (Design System) and Phase 3+ (UI Refactor).
