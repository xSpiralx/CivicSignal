import Link from "next/link";

const repository =
  process.env.NEXT_PUBLIC_REPOSITORY_URL ??
  "https://github.com/xSpiralx/CivicSignal";

export function DemoBanner() {
  const publicDirectory =
    process.env.NEXT_PUBLIC_DATA_MODE === "nationwide-public";
  return (
    <aside
      aria-label={
        publicDirectory
          ? "Nationwide directory coverage notice"
          : "Portfolio demonstration notice"
      }
      className="no-print border-b border-[#b9d7e7] bg-[#e9f7ff] px-4 py-2.5 text-sm text-[#173b57]"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center">
        <strong>
          {publicDirectory
            ? "CivicSignal nationwide directory"
            : "CivicSignal portfolio demo"}
        </strong>
        <span>
          {publicDirectory
            ? "Search any U.S. state or territory. Verified coverage varies by place; confirm details with the provider."
            : "Fictional organizations and test data demonstrate governed resource publishing—not real emergency assistance."}
        </span>
        <Link className="font-bold underline" href="/coverage">
          Coverage and limits
        </Link>
        <a className="font-bold underline" href={repository} rel="noreferrer">
          Source code
        </a>
      </div>
    </aside>
  );
}
