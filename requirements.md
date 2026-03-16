# AntiqueTunes — Full Requirements Specification

## 1. Project Overview

An e-commerce website for selling digitised sheet music PDFs of rare early 20th century popular music.
- **Brand**: AntiqueTunes
- **Currency**: USD
- **Backend**: Django 5.x
- **Database**: PostgreSQL (production) / SQLite (development)
- **Hosting**: Ionos Ubuntu VPS

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x |
| Database (prod) | PostgreSQL 16+ |
| Database (dev) | SQLite 3 |
| Payments | Stripe Checkout + Webhooks |
| Frontend | Django templates + Tailwind CSS |
| PDF preview | PDF.js (in-browser, first page) |
| PDF thumbnail gen | pdf2image + Pillow |
| Audio samples | HTML5 `<audio>` (optional, phase 2) |
| Server | Gunicorn + Nginx on Ionos Ubuntu VPS |
| SSL | Let's Encrypt / Certbot |
| Email | SMTP via Ionos |
| Settings | django-environ, split base/local/production |

---

## 3. Data Model

### 3.1 SheetMusic
| Field | Type | Notes |
|---|---|---|
| title | CharField | Song title — used in page title, h1, meta |
| slug | SlugField | SEO-friendly URL |
| composer | CharField | |
| lyricist | CharField | optional |
| arranger | CharField | optional |
| publisher | CharField | original publisher name |
| year_published | IntegerField | c. 1900–1940 |
| decade | CharField | derived on save (e.g. "1920s") |
| genres | ManyToMany → Genre | e.g. Ragtime, Jazz, Blues, March |
| categories | ManyToMany → Category | broader groupings |
| instruments | ManyToMany → Instrument | e.g. Violin, Piano, Saxophone |
| ensemble_type | CharField (choices) | Solo / Duo / Voice & Piano / Orchestra etc. |
| description | TextField | rich text; used for meta description |
| condition_notes | TextField | scan quality / provenance notes |
| price | DecimalField | USD |
| cover_image | ImageField | full cover scan |
| preview_image | ImageField | auto-generated cover thumbnail |
| preview_pdf | FileField | auto-generated watermarked first page |
| audio_sample | FileField | optional MP3/OGG (phase 2) |
| pdf_file | FileField | protected — never publicly accessible |
| page_count | IntegerField | |
| is_active | BooleanField | published / draft |
| featured | BooleanField | homepage spotlight |
| meta_title | CharField | overrides default SEO title if set |
| meta_description | CharField(160) | overrides auto-generated if set |
| created_at / updated_at | DateTimeField | |

### 3.2 Genre
- name, slug, description, display_order
- Used in faceted browse, breadcrumbs, sitemaps

### 3.3 Category
- name, slug, description, parent (self-FK for hierarchy)
- e.g. "Vocal" > "Solo Voice", "Instrumental" > "Piano"

### 3.3a Instrument
- name, slug, family, display_order
- **family** groups instruments for browse UI:
  - Keyboard (Piano, Organ, Accordion, Harmonium)
  - Strings (Violin, Viola, Cello, Double Bass, Banjo, Guitar, Ukulele, Mandolin)
  - Woodwind (Flute, Clarinet, Oboe, Bassoon, Saxophone, Piccolo)
  - Brass (Trumpet, Cornet, Trombone, French Horn, Tuba)
  - Percussion (Drums, Xylophone, Timpani)
  - Voice (Soprano, Mezzo-Soprano, Alto, Tenor, Baritone, Bass, Unspecified Voice)
  - Full Orchestra, Band, Ensemble (for orchestral / ensemble arrangements)
- Pre-populated seed list; admin can add more

### 3.3b EnsembleType
- Predefined choices (not a separate model — stored as CharField on SheetMusic):
  - Solo, Duo, Trio, Quartet, Quintet, Chamber Group, Orchestra, Band, Choir, Voice & Piano, Unspecified

### 3.4 Bundle
| Field | Notes |
|---|---|
| name, slug | |
| description | |
| items | ManyToMany → SheetMusic |
| price | Fixed bundle price (discount vs. sum of items) |
| cover_image | |
| is_active | |
| meta_title / meta_description | SEO fields |

### 3.5 Customer (extends AbstractUser)
- Login by email (no visible username)
- Fields: email, display_name, date_joined, is_active
- Billing address (optional, for future tax support)

### 3.6 Order & OrderItem
| Field | Notes |
|---|---|
| order_reference | Human-readable, unique (e.g. AT-2025-00042) |
| customer | FK → Customer (nullable for guests) |
| guest_email | stored if no account |
| status | pending / paid / refunded / failed |
| stripe_session_id | |
| stripe_payment_intent_id | |
| subtotal / total | |
| created_at | |
| OrderItem | FK → SheetMusic or Bundle, unit_price |

### 3.7 DownloadToken
| Field | Notes |
|---|---|
| uuid | unique token |
| order_item | FK → OrderItem |
| customer | FK → Customer (nullable for guests) |
| created_at, expires_at | guests: 30 days; account holders: null (no expiry) |
| download_count | tracked |
| max_downloads | guests: 5; account holders: null (unlimited) |

### 3.8 SiteSettings (singleton)
- homepage_headline, homepage_subtext, about_text
- Contact email, social links
- SEO: default meta title suffix, default meta description

---

## 4. URL Structure (SEO-friendly)

```
/                               Home
/catalogue/                          Browse all
/catalogue/<genre-slug>/             Browse by genre
/catalogue/<genre-slug>/<slug>/      Item detail
/instruments/                        Browse by instrument family
/instruments/<instrument-slug>/      Browse by instrument
/bundles/                       Browse bundles
/bundles/<slug>/                Bundle detail
/search/                        Search results
/cart/                          Cart
/checkout/                      Stripe redirect
/checkout/success/              Post-payment success
/checkout/cancel/               Cancelled checkout
/account/register/              Registration
/account/login/                 Login
/account/orders/                Order history
/account/downloads/             Download library
/about/                         About page
/contact/                       Contact form
/manage/                        Management dashboard (staff only)
```

---

## 5. Public-Facing Pages

### 5.1 Home Page
- Hero section: brand story headline, subheadline, CTA button ("Browse the Collection")
- Featured items grid (4–6 items, marked `featured=True`)
- Browse by decade strip (1900s, 1910s, 1920s, 1930s, 1940s)
- Browse by genre tiles with cover art
- Browse by instrument family strip (Keyboard, Strings, Woodwind, Brass, Voice etc.)
- Recently added items row
- Search bar (prominent, above fold)

### 5.2 Catalogue / Browse
- Filterable, paginated grid (12 or 24 per page)
- Sidebar or top filters: genre, category, decade, instrument, ensemble type, price range
- Sort: title A–Z, year (old–new, new–old), price, newest added
- Item card: cover thumbnail, title, composer, year, price, "Add to Cart" / "View" buttons
- Active filters shown as removable chips
- Filter state preserved in URL querystring (shareable, indexable)
- Canonical URL on paginated pages (rel=canonical, rel=prev/next)

### 5.3 Item Detail Page
- `<h1>`: item title
- Large cover image with alt text
- Full metadata: composer, lyricist, year, publisher, genre tags, instruments, ensemble type, page count
- Instrument tags are clickable links → catalogue filtered to that instrument
- Condition / provenance notes
- Embedded watermarked first-page PDF preview (PDF.js)
- Audio sample player if file present (HTML5 `<audio>`)
- Price + "Add to Cart" CTA
- Bundle membership notice (if item is in a bundle, link to bundle)
- Related items (same genre / same instrument / same decade, 4 items)
- Breadcrumb: Home > Genre > Title
- Structured data: `schema.org/Product` + `schema.org/BreadcrumbList`

### 5.4 Bundle Detail Page
- Bundle name, description, price, savings vs. individual
- Grid of included items with covers
- "Add Bundle to Cart" CTA
- Structured data: `schema.org/Product`

### 5.5 Search
- Full-text search: title, composer, lyricist, publisher, description, instrument names
- Results page uses same filtered grid component as catalogue
- Query preserved in URL (`?q=`)
- "No results" suggests browsing genres or featured items

### 5.6 Cart
- Session-based (works for guests and logged-in users)
- Lists items and bundles, quantities, unit prices, subtotal
- Digital goods: quantity fixed at 1 per item
- "Proceed to Checkout" CTA
- Persistent across page loads (session cookie)
- Cart count in header nav

### 5.7 Checkout
- Stripe Checkout (hosted page — minimal PCI scope)
- On return to success page: order confirmed, download links shown
- Email receipt sent automatically
- Post-purchase: prompt guest to create account (email pre-filled)

### 5.8 Customer Account
- Register / Login / Logout (email + password)
- Password reset by email
- Order history: date, reference, items, total, status
- Downloads library: all purchased items with permanent download buttons
  - Account holders: unlimited downloads, no expiry
  - Guests (post-account-creation with merged order): inherits account rules
- Profile: update display name, email, password

### 5.9 About & Contact
- About: brand story, collection provenance, scanned originals context
- Contact: simple form → email to admin

---

## 6. Management Dashboard (`/manage/`)

Protected: `@staff_member_required`. Styled consistently with site but functional-first.

### 6.1 Sheet Music Upload / Edit / Delete
- Single-page form with all metadata fields including instruments (multi-select with family grouping) and ensemble type (dropdown)
- File uploads: full PDF, cover image, optional audio sample
- On save:
  - Auto-generate watermarked first-page preview PDF (pdf2image + Pillow: add "PREVIEW" watermark)
  - Auto-generate cover thumbnail from page 1 if no cover image provided
  - Auto-populate `decade` from `year_published`
  - Auto-generate `slug` from `title` (editable)
  - Auto-populate `meta_description` from first 155 chars of description (editable)
- Drag-and-drop file upload
- Preview of cover image and PDF preview inline
- List view: sortable, filterable, shows active/draft status
- Bulk actions: activate, deactivate, delete

### 6.2 Bundle Management
- Create / edit / delete bundles
- Item picker (search + multi-select)
- Price set manually; show auto-calculated saving vs. sum

### 6.3 Order Management
- Paginated list: date, reference, customer/email, items, total, status
- Order detail: full line items, Stripe session link, re-send download email
- Manual status override (e.g. mark refunded after Stripe refund)
- Filter by status, date range

### 6.4 Customer Management
- List customers: name, email, join date, order count, lifetime spend
- Customer detail: order history, download activity
- Disable / re-enable account

### 6.5 Finance Reporting
- **Revenue dashboard**: total to date, MTD, YTD
- **Revenue over time**: line/bar chart by day / week / month (Chart.js), date range picker
- **Top-selling items**: table, units sold + revenue per title
- **Sales by genre / category**: aggregate breakdown
- **Order volume chart**: orders per period
- **Refunds tracker**: refunded orders, amounts
- **Export to CSV**: all reports, filtered by date range
- All charts responsive (Chart.js)

---

## 7. Stripe Integration

- Stripe Checkout (hosted page)
- Line items passed dynamically per order (no pre-created Products in Stripe dashboard required)
- **Webhooks handled**:
  - `checkout.session.completed` → mark order paid, generate download tokens, send receipt email
  - `payment_intent.payment_failed` → mark order failed
  - `charge.refunded` → mark order refunded, invalidate download tokens
- Webhook signature verification (Stripe-Signature header)
- Idempotent processing (check order status before acting on duplicate webhooks)
- Keys via environment variables; test keys in dev, live keys in prod
- Future: support tax via Stripe Tax (hooks already structured for it)

---

## 8. Secure PDF Delivery

- Full PDFs stored in `PROTECTED_MEDIA_ROOT` — outside web-accessible path
- Download endpoint (`/account/downloads/<token>/`):
  - Validates token exists, not expired, under download limit
  - Validates token belongs to requesting user/session
  - Serves file via Nginx `X-Accel-Redirect` (efficient, no Python buffering)
  - Increments `download_count`
- Token generated only after successful `checkout.session.completed` webhook
- Watermarked preview PDF is publicly accessible (no token needed)

---

## 9. SEO Requirements

### 9.1 Technical SEO
- Clean, semantic HTML5 throughout
- All URLs are lowercase, hyphenated slugs (no IDs in URLs)
- `<title>` tag: `{item title} — Sheet Music | AntiqueTunes` (configurable suffix)
- `<meta name="description">`: per-page, 150–160 chars, auto-generated with manual override
- Canonical tags on all pages; `rel=prev/next` on paginated catalogues
- `robots.txt`: disallow `/manage/`, `/checkout/`, `/cart/`, `/account/`
- `sitemap.xml` (django.contrib.sitemaps): items, bundles, genres, categories, instruments, static pages; auto-updated
- `hreflang` not needed (English/USD only for now)
- No duplicate content: paginated pages use canonical to page 1
- 301 redirects if slugs change (keep old slug as redirect source)

### 9.2 On-Page SEO
- Every SheetMusic and Bundle has unique title + meta description
- `<h1>` contains item title; `<h2>` for section headings
- Images: descriptive `alt` text auto-generated from title + composer; overridable
- Internal linking: breadcrumbs, genre pages link to items, related items on detail pages
- Genre and Category pages have editable descriptions (content for Google to index)

### 9.3 Structured Data (JSON-LD)
- `schema.org/Product` on item and bundle detail pages:
  - name, description, image, offers (price, currency, availability)
- `schema.org/BreadcrumbList` on all catalogue and detail pages
- `schema.org/WebSite` with `SearchAction` on home page (sitelinks searchbox)
- `schema.org/Organization` on home/about pages

### 9.4 Performance (Core Web Vitals)
- Lazy-load images below the fold (`loading="lazy"`)
- Serve images in WebP format (Pillow conversion on upload)
- Minify CSS/JS (Tailwind purge in production)
- Static files served by Nginx (not Django)
- Pagination to keep page sizes manageable

### 9.5 Social / Open Graph
- `og:title`, `og:description`, `og:image` (cover image), `og:type=product` on item pages
- `og:type=website` on home/about
- `twitter:card=summary_large_image`

---

## 10. Accessibility Requirements (WCAG 2.1 AA)

### 10.1 Semantic Structure
- Proper heading hierarchy (`h1` → `h2` → `h3`) on every page — never skip levels
- Landmark regions: `<header>`, `<nav>`, `<main>`, `<footer>`, `<aside>`
- `<nav aria-label="Main navigation">`, `<nav aria-label="Breadcrumb">` etc.

### 10.2 Keyboard Navigation
- All interactive elements reachable and operable by keyboard alone
- Logical tab order throughout
- Visible focus styles (high-contrast outline — not browser default removed without replacement)
- Skip-to-main-content link as first focusable element on every page
- Modal/dialog traps focus while open; returns focus on close
- Dropdown menus operable with arrow keys

### 10.3 Images & Media
- All `<img>` elements have descriptive `alt` text (auto-generated; overridable)
- Decorative images use `alt=""`
- Cover images: alt = "{title} — sheet music cover"
- Audio player has visible play/pause controls with `aria-label`
- PDF preview iframe has title attribute

### 10.4 Colour & Contrast
- Text contrast ratio ≥ 4.5:1 (normal text), ≥ 3:1 (large text / UI components)
- Never convey meaning by colour alone (use icons or text alongside)
- Form error states use both colour and icon + text message

### 10.5 Forms
- Every input has an associated `<label>` (not just placeholder)
- Required fields marked with `aria-required="true"` and visual indicator
- Inline validation errors: `aria-describedby` links input to error message
- Error summary at top of form on failed submit, with links to each field

### 10.6 ARIA
- Use native HTML elements over ARIA where possible
- `aria-live` regions for dynamic updates (cart count, add-to-cart confirmation)
- `aria-current="page"` in navigation for current page
- `role="alert"` for flash messages / errors

### 10.7 PDF Preview
- PDF.js viewer: provide a text alternative ("Download preview page as image") for users who cannot use the embedded viewer
- Fallback: static watermarked cover image shown if PDF.js fails to load

### 10.8 Testing
- Automated: run axe-core (or similar) in CI on key templates
- Manual: keyboard-only walkthrough of purchase flow before each release
- Screen reader: test with VoiceOver (macOS) on checkout and account flows

---

## 11. Design & UX

- **Aesthetic**: warm vintage — evokes 1920s sheet music covers
- **Typography**: Playfair Display (serif) for headings; Inter or similar for body
- **Colour palette**: cream/ivory background, deep mahogany `#4a1c0d`, gold accent `#c9a84c`, dark charcoal text
- **Responsive**: mobile-first, fluid grid; breakpoints at 640px, 1024px, 1280px
- **Micro-interactions**: hover states on cards, smooth transitions, button feedback
- **Loading states**: skeleton screens on catalogue while filtering
- **Empty states**: friendly messaging when cart is empty, no search results, etc.
- **Toast notifications**: non-blocking confirmations (item added to cart, etc.) with `aria-live`

---

## 12. Environment Configuration

```
# .env (never committed)
SECRET_KEY=
DEBUG=False
DATABASE_URL=postgres://...        # prod only
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@antiquetunes.com
MEDIA_ROOT=
PROTECTED_MEDIA_ROOT=
ALLOWED_HOSTS=
SITE_URL=https://antiquetunes.com
```

Settings files:
- `settings/base.py` — shared config
- `settings/local.py` — SQLite, DEBUG=True, Stripe test keys
- `settings/production.py` — PostgreSQL, DEBUG=False, security headers

---

## 13. Deployment (Ionos Ubuntu VPS)

- Nginx: reverse proxy, serves `/static/` and `/media/`, `X-Accel-Redirect` for protected files
- Gunicorn: systemd service
- PostgreSQL: installed on server
- Let's Encrypt SSL via Certbot (auto-renew)
- `collectstatic` and `migrate` run on each deploy
- `pg_dump` cron job for nightly database backups
- Environment variables in `/etc/environment` or `.env` file, not in repo

### Security Headers (Nginx)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: (configured per-app)
```

---

## 14. Phased Delivery

| Phase | Scope |
|---|---|
| 1 | Project scaffold, settings, models, Django admin, PDF upload + auto-thumbnail, catalogue browse, item detail, SEO foundations |
| 2 | Cart, Stripe Checkout, webhooks, secure download, order confirmation email |
| 3 | Customer accounts, registration, order history, download library, guest-to-account merge |
| 4 | Bundles, bundle browse/detail, bundle checkout |
| 5 | Management dashboard: upload form, order management, finance reporting |
| 6 | Full-text search improvements (PostgreSQL SearchVector), accessibility audit, performance pass |
| 7 | Production deployment, Nginx config, SSL, backups, go-live |

---

## 15. Out of Scope (for now)

- Multi-currency
- VAT / tax calculation (architecture supports adding Stripe Tax later)
- Subscription / membership pricing
- User reviews or ratings
- Audio samples (placeholder in model, UI deferred to phase 2)
- Bulk CSV import (can add in phase 5)
- CDN for static assets
