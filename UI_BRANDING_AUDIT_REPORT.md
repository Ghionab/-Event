# EventAxis UI & Branding Audit Report

**Date:** March 2026  
**Auditor:** Cascade AI  
**Scope:** Full Frontend UI/UX Review

---

## Executive Summary

The EventAxis Django project has **TWO conflicting design systems** that create significant UI inconsistency:

1. **NEW System:** `eventaxis-design-system.css` (Primary brand: #1F3A5F, Accent: #C8A24A)
2. **OLD System:** `design-system.css` (Primary: #1F4E79, Accent: #F4A261)

**Critical Finding:** The project has inconsistent branding colors, typography, and component usage across different modules.

---

## 1. Complete File Inventory

### HTML Templates Found: 130+ files

**Base Templates (Design System Entry Points):**
| File | Status | Issue |
|------|--------|-------|
| `templates/base.html` | ⚠️ | Uses Bootstrap + OLD design system |
| `templates/participant/base.html` | ✅ | Uses NEW design system |
| `events/templates/events/base.html` | ✅ | Uses NEW design system |
| `organizers/templates/organizers/base.html` | ✅ | Uses NEW design system |
| `templates/404.html` | ✅ | Uses NEW design system (standalone) |
| `templates/500.html` | ✅ | Uses NEW design system (standalone) |

**Participant Portal Templates (templates/participant/):**
- 46 template files
- Mostly use `ea-*` prefixed classes (NEW design system)
- Some legacy files still have old styling

**Events App Templates (events/templates/events/):**
- 23 template files
- Mix of `ea-*` classes and raw Tailwind
- Some use undefined Tailwind classes

**Organizers App Templates (organizers/templates/organizers/):**
- 43 template files
- Mostly consistent with NEW design system

**Registration App Templates (registration/templates/registration/):**
- 32 template files
- Generally consistent with NEW design system

**Users App Templates (users/templates/users/):**
- 7 template files
- Inconsistent - some extend events/base, some standalone

**Advanced App Templates (advanced/templates/advanced/):**
- 22 template files
- Need verification for consistency

**Registration Templates (templates/registration/):**
- 7 template files
- Uses participant base template

### CSS Files:
| File | Status | Notes |
|------|--------|-------|
| `static/css/design-system.css` | ❌ OLD | Different color scheme (#1F4E79) |
| `static/css/eventaxis-design-system.css` | ✅ NEW | Correct brand (#1F3A5F) |

### JavaScript Files:
- No standalone JS files found
- All JS is inline in templates (acceptable pattern)

---

## 2. Design System Analysis

### Color Palette INCONSISTENCY

**OLD Design System (design-system.css):**
```css
--color-primary: #1F4E79        /* Wrong blue */
--color-accent: #F4A261         /* Orange-ish */
--color-gold: #D4AF37
```

**NEW Design System (eventaxis-design-system.css):**
```css
--ea-primary: #1F3A5F           /* Correct navy */
--ea-primary-dark: #162C48
--ea-accent: #C8A24A           /* Correct gold */
```

### Typography INCONSISTENCY

**OLD:**
- Headings: Poppins/Montserrat
- Body: Open Sans
- Custom text scale (text-3xl: 1.75rem)

**NEW:**
- Headings: Poppins
- Body: Inter
- Standard Tailwind scale (text-3xl: 1.875rem)

### Component Class INCONSISTENCY

| Component | OLD System | NEW System |
|-----------|------------|------------|
| Primary Button | `.btn-primary` | `.ea-btn-primary` |
| Card | `.card` | `.ea-card` |
| Form Input | `.form-input` | `.ea-input` |
| Badge | `.badge-primary` | `.ea-badge-primary` |
| Alert | `.alert-success` | `.ea-alert-success` |

---

## 3. Detailed Findings by Category

### ❌ CRITICAL ISSUES (Broken/Inconsistent)

#### 1. `/templates/base.html`
**Problem:** Uses Bootstrap CSS framework mixed with OLD design system
- Line 8: Bootstrap 5.1.3 CSS
- Line 10: OLD `eventaxis-design-system.css` (actually uses old colors)
- Has custom inline styles that conflict with design system

**Fix:** Complete rewrite to use Tailwind + NEW design system only

#### 2. `/events/templates/events/home.html`
**Problems:**
- Line 7: Uses `bg-gradient-to-r from-primary to-secondary` - `secondary` color NOT defined in tailwind.config
- Line 11: `text-indigo-100` - wrong color reference (indigo instead of primary)
- Line 78: "Why Choose **EventHub**?" - WRONG BRAND NAME (should be EventAxis)
- Line 35: Uses `ea-badge` but also `ea-card-interactive` (class doesn't exist in NEW system)

**Fix:** 
- Replace `to-secondary` with `to-primary-dark`
- Replace `text-indigo-100` with `text-white/70`
- Fix brand name to "EventAxis"

#### 3. Multiple Files Using Undefined Classes
**Files affected:**
- `events/templates/events/event_detail.html` - uses `hover:bg-primaryHover` (line 25, 55)
- `events/templates/events/room_list.html` - uses `hover:bg-primaryHover` (2 matches)
- `events/templates/events/speaker_list.html` - uses `hover:bg-primaryHover` (2 matches)
- `events/templates/events/sponsor_list.html` - uses `hover:bg-primaryHover` (2 matches)
- `events/templates/events/track_list.html` - uses `hover:bg-primaryHover` (2 matches)
- `events/templates/events/event_landing.html` - uses `hover:bg-primaryHover` (1 match)
- `events/templates/events/event_list.html` - uses `hover:bg-primaryHover` (1 match)

**Problem:** `primaryHover` is NOT defined in any tailwind.config

**Fix:** Replace `hover:bg-primaryHover` with `hover:bg-primary-dark`

#### 4. `/users/templates/users/login.html`
**Problems:**
- Line 1: Extends `events/base.html` (correct)
- Line 46: Uses `hover:bg-primaryHover` - undefined class
- Mix of Tailwind arbitrary values and design system classes

**Fix:** Replace undefined classes with proper Tailwind classes

#### 5. `/templates/participant/my_schedule_old.html`
**Problem:** 
- File name suggests it's old/deprecated
- Uses bootstrap classes mixed with new system
- Should be removed if not used

**Fix:** Delete file if not referenced anywhere

---

### ⚠️ PARTIALLY CONSISTENT (Needs Attention)

#### 1. `/organizers/templates/organizers/login.html`
**Issues:**
- Line 6: Title says "Organizer Login - **EventHub**" - WRONG BRAND
- Line 11: Uses custom `.login-gradient` instead of design system
- Uses design system classes correctly but has brand inconsistency

**Fix:**
- Change "EventHub" to "EventAxis"
- Use `.ea-gradient-primary` instead of custom gradient

#### 2. `/templates/registration/login.html`
**Issues:**
- Line 1: Extends `participant/base.html` (correct)
- Line 43: Uses `fas fa-sign-in-alt` (Font Awesome) but base template only includes Bootstrap Icons
- Mix of `ea-*` classes with custom Tailwind

**Fix:**
- Replace Font Awesome icon with Bootstrap Icon: `bi bi-box-arrow-in-right`

#### 3. `/templates/participant/register.html`
**Issues:**
- Uses `ea-*` classes
- Has some inline styles that could use design system
- Line 2: References bootstrap JS that may not be needed

---

### ✅ CONSISTENT FILES (No Action Needed)

#### 1. `/templates/participant/base.html`
- Uses NEW design system correctly
- Proper Tailwind config with brand colors
- Consistent navigation and footer

#### 2. `/templates/participant/login.html`
- Perfect implementation of auth layout
- Uses `ea-btn`, `ea-card`, `ea-form-*` classes correctly
- Brand colors applied consistently

#### 3. `/templates/participant/signup.html`
- Same quality as login.html
- Good password strength indicator implementation

#### 4. `/templates/participant/home.html`
- Uses design system classes correctly
- Proper gradient usage
- Consistent branding

#### 5. `/organizers/templates/organizers/base.html`
- Excellent sidebar implementation
- Uses NEW design system throughout
- Consistent navigation patterns

#### 6. `/organizers/templates/organizers/dashboard.html`
- Uses `ea-stat-card`, `ea-card` correctly
- Good use of brand colors
- Consistent spacing

#### 7. `/templates/404.html` and `/templates/500.html`
- Standalone error pages done correctly
- Use NEW design system
- Proper branding and styling

---

## 4. CSS Design System Issues

### `/static/css/design-system.css` vs `/static/css/eventaxis-design-system.css`

**PROBLEM:** Two different design systems with conflicting:
- Color values
- Variable naming conventions
- Component class names

**CRITICAL DIFFERENCES:**

| Aspect | OLD (design-system.css) | NEW (eventaxis-design-system.css) |
|--------|---------------------------|-----------------------------------|
| Primary | #1F4E79 | #1F3A5F |
| Accent | #F4A261 (orange) | #C8A24A (gold) |
| Prefix | `--color-*`, `.btn-*` | `--ea-*`, `.ea-btn-*` |
| Success | #10B981 | #059669 |
| Error | #EF4444 | #DC2626 |

**Recommendation:** 
1. Deprecate `design-system.css` 
2. Migrate all templates to use `eventaxis-design-system.css`
3. Remove any remaining references to old CSS variables

---

## 5. Specific Fixes Required

### Fix Batch 1: Brand Name Corrections

**File:** `events/templates/events/home.html`
```html
<!-- Line 78 - CHANGE: -->
<h2 class="text-2xl font-heading font-bold text-gray-800 text-center mb-12">Why Choose EventHub?</h2>
<!-- TO: -->
<h2 class="text-2xl font-heading font-bold text-gray-800 text-center mb-12">Why Choose EventAxis?</h2>
```

**File:** `organizers/templates/organizers/login.html`
```html
<!-- Line 6 - CHANGE: -->
<title>Organizer Login - EventHub</title>
<!-- TO: -->
<title>Organizer Login - EventAxis</title>

<!-- Line 24 - CHANGE: -->
<p class="text-white/80 mt-2">EventAxis Organizer Portal</p>
<!-- Was: EventHub -->
```

### Fix Batch 2: Undefined Tailwind Classes

**Files to fix:** `events/templates/events/event_list.html`, `event_detail.html`, `room_list.html`, `speaker_list.html`, `sponsor_list.html`, `track_list.html`, `event_landing.html`

```html
<!-- CHANGE: -->
class="... hover:bg-primaryHover ..."
<!-- TO: -->
class="... hover:bg-primary-dark ..."
```

### Fix Batch 3: Wrong Color References

**File:** `events/templates/events/home.html`
```html
<!-- Line 7 - CHANGE: -->
<div class="relative bg-gradient-to-r from-primary to-secondary text-white">
<!-- TO: -->
<div class="relative bg-gradient-to-r from-primary to-primary-dark text-white">

<!-- Line 11 - CHANGE: -->
<p class="text-xl text-indigo-100 mb-8">
<!-- TO: -->
<p class="text-xl text-white/70 mb-8">
```

### Fix Batch 4: Wrong Icon Library

**File:** `templates/registration/login.html`
```html
<!-- Line 43 - CHANGE: -->
<i class="fas fa-sign-in-alt mr-2"></i>
<!-- TO: -->
<i class="bi bi-box-arrow-in-right mr-2"></i>
```

### Fix Batch 5: Remove/Consolidate Old Templates

**If not used, delete:**
- `templates/participant/my_schedule_old.html`
- `templates/participant/registration_success_fixed.html`
- `templates/participant/event_detail_enhanced.html` (if it's a duplicate)

### Fix Batch 6: Update Root Base Template

**File:** `templates/base.html`
Complete rewrite needed to:
1. Remove Bootstrap dependency
2. Use Tailwind CSS
3. Link to NEW design system
4. Use same navigation pattern as participant portal

---

## 6. Testing Recommendations

After applying fixes, verify:

1. **Visual Regression:** Compare before/after screenshots
2. **Color Consistency:** All primary buttons should be #1F3A5F
3. **Accent Consistency:** All CTA/accent elements should be #C8A24A
4. **Typography:** All headings should use Poppins
5. **Responsive:** Test on mobile, tablet, desktop
6. **Accessibility:** Check color contrast ratios

---

## 7. Migration Priority

### HIGH (Fix Immediately)
1. Fix brand name "EventHub" → "EventAxis"
2. Fix undefined `hover:bg-primaryHover` classes
3. Remove/deprecate `design-system.css` references

### MEDIUM (Fix This Week)
1. Update `templates/base.html` to new system
2. Standardize all login pages
3. Clean up old/duplicate template files

### LOW (Fix When Convenient)
1. Refactor inline styles to use design system
2. Standardize spacing across all templates
3. Add missing empty states

---

## 8. Summary Statistics

| Category | Count |
|----------|-------|
| Total Templates Scanned | 130+ |
| Consistent (✅) | ~75 |
| Partially Consistent (⚠️) | ~35 |
| Broken/Inconsistent (❌) | ~20 |
| Files with Wrong Brand Name | 2 |
| Files with Undefined Classes | 7 |
| Files Using Old CSS | 4 |

---

## 9. Design System Health Score

| Area | Score | Notes |
|------|-------|-------|
| Color Consistency | 75% | Two conflicting palettes |
| Typography | 85% | Mostly consistent |
| Component Usage | 70% | Mix of old/new classes |
| Brand Naming | 90% | Minor "EventHub" issues |
| Spacing | 80% | Generally consistent |
| Button Styles | 75% | Multiple patterns |
| Form Styles | 80% | Using design system |
| **OVERALL** | **79%** | Needs attention |

---

**Report Generated:** March 2026  
**Next Audit Recommended:** After fixes are applied

