import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  if (
    process.env.NEXT_PUBLIC_APP_ENV !== "production" ||
    process.env.NEXT_PUBLIC_DATA_MODE !== "nationwide-public"
  )
    return [];
  const base = process.env.PUBLIC_BASE_URL!;
  return [
    "",
    "/resources",
    "/coverage",
    "/data-sources",
    "/verification",
    "/about",
    "/privacy",
    "/accessibility",
    "/security",
  ].map((path) => ({ url: `${base}${path}`, changeFrequency: "weekly" }));
}
