import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const publicDirectory =
    process.env.NEXT_PUBLIC_APP_ENV === "production" &&
    process.env.NEXT_PUBLIC_DATA_MODE === "nationwide-public";
  if (!publicDirectory) {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin/", "/api/", "/offline"],
    },
    sitemap: `${process.env.PUBLIC_BASE_URL}/sitemap.xml`,
  };
}
