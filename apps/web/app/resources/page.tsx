import type { Metadata } from "next";
import { ResourceSearch } from "@/components/resources/resource-search";
import { SafetyNotice } from "@/components/safety-notice";
export const metadata: Metadata = { title: "Resource directory | CivicSignal" };
export default function ResourcesPage() {
  return (
    <main
      id="main-content"
      className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14"
    >
      <SafetyNotice />
      <div className="mt-8">
        <ResourceSearch />
      </div>
    </main>
  );
}
