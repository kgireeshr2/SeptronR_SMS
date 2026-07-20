# 10 — Public Launch Strategy (India, Private K-12)

> Complements `01_GTM_Strategy.md`. Fills the two open decisions — **pricing** and **budget** — and sharpens targeting for English-medium private K-12 schools in India.

## Positioning — lead with 2 differentiators
1. **WhatsApp-first parent engagement** — parents check fees, attendance, marks *inside WhatsApp*, no app download (`chat_flow_engine.py` 7-flow bot = demo centerpiece).
2. **All-in-one** — admissions → fees → attendance → exams → transport → accounting → parent comms, plus a white-label public website + enquiry form per school.

**Tagline to test:** *"Run your whole school — and talk to every parent on WhatsApp — from one platform."*

**ICP:** English-medium private K-12, 300–2,000 students, Tier-1/Tier-2 cities. Buyer = Trustee/Owner; champion = Principal/Admin.
Competitors to differentiate against: Teachmint, MyClassboard, Entab, Fedena, Edunext.

## Pricing — per-student/year, billed annually, tiered
| Tier | ₹/student/year | Who | Includes |
|------|----------------|-----|----------|
| Starter | ₹150–200 | <500 | Admissions, attendance, fees, SMS/email, parent portal |
| **Pro** (lead) | ₹250–350 | 500–1,500 | + WhatsApp bot, exams/report cards, accounting, white-label site, PTM |
| Enterprise | Custom | groups / >1,500 | + multi-campus superadmin, custom domain, payroll, transport GPS, priority support |

- Market it as ₹/student/month (₹20–30 "sounds" small); **bill annually**.
- One-time onboarding fee ₹15k–40k (migration + training; funds sales, filters tyre-kickers).
- **60-day free pilot** = the conversion engine.
- Referral credit: refer a school → 1–2 months free.
- Account for Meta per-conversation WhatsApp cost: bundle a monthly message cap per tier.

## Budget — lean, sales-led start
**Phase 1 (Mo 1–3, ~₹25–40k/mo)** → goal: 3–5 pilots
- Google Search Ads, high-intent only (₹15–20k/mo).
- Founder outreach to 100 owners/principals (LinkedIn + WhatsApp + brochure) — ₹0.
- Education-consultant / local-IT-vendor referral partners (15–20% of year-1) — ₹0 upfront.

**Phase 2 (Mo 4–6, ~₹60–100k/mo)** → goal: convert pilots + 10 new pilots
- Meta ads + lookalikes from pilot signups.
- 1–2 regional CBSE/ICSE principal expos (best offline ROI).
- 3–4 pilot-school case-study videos.

Don't scale paid before **one referenceable happy school**. CAC here is sales effort, not ad spend.

## Channel priority
1. Founder/direct demo (show the WhatsApp bot live on the buyer's phone)
2. Referrals & partners
3. Google Search Ads
4. Offline expos / principal roundtables
5. Meta ads + WhatsApp nurture
6. Content/SEO (fee collection, CBSE result automation, parent communication)

## First 90 days
- **Wk 1–2:** product marketing landing page + pricing page; demo school with realistic seed data.
- **Wk 2–4:** 50-school target list; send brochure, book demos; launch Search Ads.
- **Wk 4–8:** run demos, pitch 60-day pilot, sign 3–5; recruit 2–3 referral partners.
- **Wk 8–12:** onboard pilots, capture testimonials, first case study, convert earliest pilot to annual.

Reuse: `02_90_Day_Campaign_Plan.md`, `04_Content_Calendar_8_Weeks.md`, the trifold brochure, `05_Budget_KPI_Tracker_Template.csv`.

## Metrics (from day 1, in the CSV tracker)
Demos booked → demo→pilot (>30%) → pilot→annual (>50%) → CAC → ₹ ARR added.

## Enablement gaps to build (optional but recommended)
1. One public product marketing landing page (you only have per-school `/site/{slug}` sites today).
2. Demo tenant with realistic seed data (extend `backend/app/scripts/seed_data.py`).
3. Lead-capture wiring to a monitored inbox/CRM/WhatsApp (reuse existing enquiry-form infra).
4. Pricing page reflecting the table above.
