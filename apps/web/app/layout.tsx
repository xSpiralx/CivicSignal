import type { Metadata } from "next";
import { ServiceWorkerRegistration } from "@/components/service-worker-registration";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.PUBLIC_BASE_URL ?? "http://localhost:3000"),
  title: "CivicSignal",
  description:
    "A trustworthy foundation for verified community resource information.",
  manifest: "/manifest.webmanifest",
  openGraph: {
    title: "CivicSignal",
    description: "Trusted community resources, clearly sourced.",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "CivicSignal — Trusted community resources, clearly sourced.",
      },
    ],
  },
  twitter: { card: "summary_large_image", images: ["/og.png"] },
  robots:
    process.env.NEXT_PUBLIC_APP_ENV === "staging"
      ? { index: false, follow: false, nocache: true }
      : undefined,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {process.env.NEXT_PUBLIC_APP_ENV === "staging" && (
          <div className="no-print bg-[#6d3fc0] px-4 py-2 text-center text-sm font-bold text-white">
            STAGING · Fictional or approved test data only · Not a public
            service
          </div>
        )}
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <SiteHeader />
        {children}
        <SiteFooter />
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
