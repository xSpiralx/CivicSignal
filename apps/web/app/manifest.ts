import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "CivicSignal",
    short_name: "CivicSignal",
    description: "Source-aware community resource directory",
    start_url: "/resources",
    display: "standalone",
    background_color: "#f5f8f5",
    theme_color: "#0d4c4a",
    icons: [{ src: "/icons/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
