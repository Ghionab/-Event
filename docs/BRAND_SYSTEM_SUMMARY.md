# EventAxis Brand System Summary
## Extracted from Official Branding Guide & Logo

---

## 1. COLOR PALETTE

### Primary Colors
| Name | HEX | Usage |
|------|-----|-------|
| **Primary Blue** | `#1F4E79` | Headers, primary buttons, navbar, key UI elements |
| **Accent Orange** | `#F4A261` | CTAs, highlights, badges, hover states |
| **Gold/Yellow** | `#D4AF37` | Logo accent, premium elements, success states |

### Secondary Colors
| Name | HEX | Usage |
|------|-----|-------|
| **Dark Text** | `#333333` | Primary text, headings |
| **Secondary Text** | `#666666` | Body text, descriptions |
| **Muted Text** | `#999999` | Placeholders, disabled states |
| **Light Background** | `#F8FAFC` | Page backgrounds, cards |
| **White** | `#FFFFFF` | Card backgrounds, inputs |
| **Border** | `#E5E7EB` | Dividers, card borders |

### Semantic Colors
| Name | HEX | Usage |
|------|-----|-------|
| **Success** | `#10B981` | Success messages, confirmations |
| **Warning** | `#F59E0B` | Alerts, warnings |
| **Error** | `#EF4444` | Errors, validation failures |
| **Info** | `#3B82F6` | Informational messages |

---

## 2. TYPOGRAPHY SYSTEM

### Font Families
- **Headings**: `Poppins`, `Montserrat` (sans-serif)
- **Body Text**: `Open Sans` (sans-serif)
- **Fallback**: `system-ui, -apple-system, sans-serif`

### Type Scale (8px Grid)
| Element | Size | Weight | Line Height | Letter Spacing |
|---------|------|--------|-------------|----------------|
| **H1** | 48px (3rem) | 700 | 1.2 | -0.02em |
| **H2** | 36px (2.25rem) | 600 | 1.3 | -0.01em |
| **H3** | 28px (1.75rem) | 600 | 1.4 | 0 |
| **H4** | 24px (1.5rem) | 600 | 1.4 | 0 |
| **H5** | 20px (1.25rem) | 600 | 1.5 | 0 |
| **H6** | 18px (1.125rem) | 600 | 1.5 | 0.01em |
| **Body Large** | 18px (1.125rem) | 400 | 1.6 | 0 |
| **Body** | 16px (1rem) | 400 | 1.6 | 0 |
| **Body Small** | 14px (0.875rem) | 400 | 1.5 | 0 |
| **Caption** | 12px (0.75rem) | 500 | 1.4 | 0.01em |
| **Button** | 14px (0.875rem) | 600 | 1 | 0.02em |

---

## 3. SPACING SYSTEM (8px Grid)

### Base Unit: 8px
| Token | Value | Usage |
|-------|-------|-------|
| **space-1** | 4px | Tight spacing |
| **space-2** | 8px | Component internal padding |
| **space-3** | 12px | Small gaps |
| **space-4** | 16px | Default padding |
| **space-5** | 20px | Medium gaps |
| **space-6** | 24px | Card padding |
| **space-8** | 32px | Large gaps |
| **space-10** | 40px | Section spacing |
| **space-12** | 48px | Major section breaks |

### Border Radius
| Token | Value | Usage |
|-------|-------|-------|
| **radius-sm** | 4px | Inputs, small elements |
| **radius-md** | 8px | Cards, buttons |
| **radius-lg** | 12px | Large cards, modals |
| **radius-xl** | 16px | Feature cards, hero |
| **radius-full** | 9999px | Pills, avatars |

---

## 4. SHADOWS & ELEVATION

| Token | Value | Usage |
|-------|-------|-------|
| **shadow-sm** | `0 1px 2px 0 rgba(0,0,0,0.05)` | Subtle elevation |
| **shadow-md** | `0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)` | Cards, buttons |
| **shadow-lg** | `0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)` | Dropdowns, modals |
| **shadow-xl** | `0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)` | Overlays, dialogs |
| **shadow-glow** | `0 0 20px rgba(244,162,97,0.3)` | Accent glow on hover |

---

## 5. UI STYLE DIRECTION

### Brand Personality
- **Modern**: Clean lines, contemporary aesthetic
- **Professional**: Trustworthy, business-ready
- **Trustworthy**: Consistent, reliable design language
- **User-Friendly**: Intuitive, accessible interfaces

### Design Principles
1. **Clean Minimalism**: Ample whitespace, focused content
2. **Strong Hierarchy**: Clear visual distinction between elements
3. **Soft Interactions**: Subtle shadows, gentle transitions
4. **Rounded Geometry**: 8-16px border radius throughout
5. **Consistent Spacing**: 8px grid system
6. **Responsive First**: Mobile-optimized, desktop-enhanced

### SaaS Patterns (Stripe, Notion, Linear inspired)
- Card-based layouts with subtle shadows
- Pill-shaped buttons with clear CTAs
- Consistent icon usage (Font Awesome / Lucide)
- Empty states with helpful illustrations
- Loading skeletons instead of spinners
- Clear form validation with inline errors

---

## 6. LOGO USAGE

### Primary Logo
- EventAxis wordmark with city skyline icon
- Blue (#1F4E79) for "Event", Gold (#D4AF37) for "Axis"
- Compass/star element in gradient blue-gold
- Clear space: minimum 20px around logo

### Tagline
- "YOUR ETHIOPIAN LIVE EVENT HUB" (when space permits)
- All caps, smaller font (12-14px)
- Color: Secondary text (#666666)

---

## 7. COMPONENT PRINCIPLES

### Buttons
- **Primary**: `bg-[#1F4E79]`, white text, `hover:bg-[#163d5f]`, `shadow-md`
- **Secondary**: White bg, `border-[#1F4E79]`, `text-[#1F4E79]`
- **Accent/CTA**: `bg-[#F4A261]`, white text, `hover:bg-[#e08c4a]`
- **Ghost**: Transparent, text only with hover underline
- Border radius: 8px (rounded-lg)
- Padding: 12px 24px (py-3 px-6)
- Font: 14px, weight 600

### Cards
- White background (#FFFFFF)
- Border radius: 12px (rounded-xl)
- Shadow: `shadow-md` default, `shadow-lg` on hover
- Border: 1px solid `#E5E7EB` (optional)
- Padding: 24px (p-6)
- Hover: Lift effect with `transform: translateY(-2px)`

### Forms
- Input border: 1px solid `#E5E7EB`, radius 8px
- Focus: Ring 2px `#1F4E79` with 20% opacity
- Labels: 14px, weight 500, color `#333333`
- Error states: Border `#EF4444`, error text below
- Success states: Check icon, green tint

### Navigation
- Navbar: White bg, `shadow-sm`, sticky top
- Links: 14px, weight 500, `#666666` default
- Active/Hover: `#1F4E79` with underline
- CTA button in navbar: Accent orange or primary blue

---

*Document generated from EventAxis Branding Guide*
*Date: March 24, 2026*
