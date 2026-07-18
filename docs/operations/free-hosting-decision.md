# Free hosting decision

Reviewed 2026-07-18 against official provider documentation. Limits and terms can change; re-check them before creating services.

## Selected release-candidate architecture

- **Vercel Hobby** for the Next.js application. It has native Next.js support, automatic TLS, preview deployments, and hard usage limits that pause a Hobby project instead of creating an unapproved bill. Hobby is restricted to personal, non-commercial use; CivicSignal must move plans or providers before any commercial use. The Vercel project root is `apps/web`.
- **Render Free web service** for FastAPI. It supports the existing API Dockerfile and health check without a payment commitment. The service spins down after 15 idle minutes, can take about a minute to wake, has an ephemeral filesystem, and is explicitly unsuitable for production-grade availability. The API therefore remains an honest release-candidate deployment.
- **Neon Free** for PostgreSQL. The free plan has no stated time limit or card requirement, scales idle compute to zero, and currently includes 0.5 GB storage and 100 compute-unit hours per project per month. CivicSignal uses manual logical exports because free-tier recovery history is limited.
- **GitHub Actions** for CI and authenticated daily stale detection. Scheduled workflows can be delayed or disabled after repository inactivity, so the operator must check runs and retain a manual CLI fallback.

The browser uses the Vercel origin only. Server-side Next.js routes proxy browser requests to Render and attach a separate shared secret. FastAPI rejects direct `/api/v1/` access without it. Sessions remain same-origin, secure, HTTP-only, and strict SameSite. Health endpoints remain public; production API documentation is disabled.

## Alternatives evaluated

| Provider | Result | Reason |
| --- | --- | --- |
| Cloudflare Workers | Rejected for v1 | Strong static hosting and generous request allowance, but OpenNext currently does not support Node.js middleware. CivicSignal's protected staging middleware would require a platform-specific redesign. |
| Koyeb Free | Rejected for v1 | Technically suitable for FastAPI, but the free instance is presented for hobby/testing, sleeps after one hour, is limited to Washington or Frankfurt, and account validation may require a payment method. |
| Render Free PostgreSQL | Rejected | Free databases expire after 30 days, which fails the persistence gate. |
| Supabase Free | Not selected | A viable PostgreSQL alternative, but Neon is simpler for this SQLAlchemy-only application and has a clear no-card, no-expiration free path. |
| Vercel for API | Rejected | FastAPI state, migrations, and operational commands are clearer in the existing container service. |

## Official references

- Vercel Hobby and fair use: <https://vercel.com/docs/plans/hobby> and <https://vercel.com/docs/limits/fair-use-guidelines>
- Render Free limitations: <https://render.com/docs/free>
- Neon pricing and scale to zero: <https://neon.com/pricing> and <https://neon.com/docs/introduction/scale-to-zero>
- Koyeb free instances and pricing FAQ: <https://www.koyeb.com/docs/reference/instances> and <https://www.koyeb.com/docs/faqs/pricing>
- Cloudflare Workers pricing, limits, and Next.js: <https://developers.cloudflare.com/workers/platform/pricing/>, <https://developers.cloudflare.com/workers/platform/limits/>, and <https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/>

## No-surprise billing rule

Do not add a payment method, paid plan, usage-based billing, paid database, paid monitoring, or custom domain as part of this release without explicit authorization. Provider dashboards must be checked monthly for changed limits.
