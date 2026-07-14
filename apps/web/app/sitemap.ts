import type { MetadataRoute } from "next";
import { SITEMAP_ROUTES } from "@/lib/routes";
import { siteConfig } from "@/lib/site-config";

export default function sitemap(): MetadataRoute.Sitemap {
  return SITEMAP_ROUTES.map((path) => ({
    url: new URL(path, siteConfig.siteUrl).toString(),
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : path === "/apply" ? 0.9 : 0.7,
  }));
}
