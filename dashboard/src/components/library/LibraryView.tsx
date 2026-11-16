"use client";

import { useEffect, useMemo, useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import { PageHeader } from "@/components/shell/PageHeader";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ApiError, fetchActs, isAbortError, type ActInfo } from "@/lib/api";
import { CATEGORY_LABELS, instrumentByKey, type Instrument, type InstrumentCategory } from "@/lib/catalog";
import { titleCase } from "@/lib/format";

interface Entry {
  key: string;
  title: string;
  url: string;
  short: string;
  category: InstrumentCategory;
  summary: string;
  coverage: string;
}

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; acts: ActInfo[] };

const CATEGORY_ORDER: InstrumentCategory[] = ["act", "subordinate", "case_law"];

function toEntry(act: ActInfo): Entry {
  const meta: Partial<Instrument> = instrumentByKey(act.key) ?? {};
  return {
    key: act.key,
    title: meta.title ?? titleCase(act.title),
    url: act.url,
    short: meta.short ?? act.key.toUpperCase(),
    category: meta.category ?? "act",
    summary: meta.summary ?? "",
    coverage: meta.coverage ?? "",
  };
}

function SourceCard({ entry }: { entry: Entry }) {
  return (
    <li className="flex flex-col rounded-xl border border-line bg-surface p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <Badge tone="brand">{entry.short}</Badge>
        <a
          href={entry.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs font-medium text-ink-subtle hover:text-brand"
        >
          SAFLII
          <ExternalLink aria-hidden className="size-3.5" />
          <span className="sr-only">: open {entry.title} on SAFLII (new tab)</span>
        </a>
      </div>
      <h3 className="mt-3 text-[15px] leading-6 font-medium text-ink">{entry.title}</h3>
      {entry.summary && <p className="mt-1 text-sm leading-6 text-ink-muted">{entry.summary}</p>}
      {entry.coverage && (
        <p className="mt-auto pt-4 text-xs leading-5 text-ink-subtle">
          <span className="font-medium text-ink-muted">Indexed: </span>
          {entry.coverage}
        </p>
      )}
    </li>
  );
}

export function LibraryView() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetchActs(controller.signal)
      .then((acts) => setState({ status: "ready", acts }))
      .catch((error: unknown) => {
        if (isAbortError(error)) return;
        setState({
          status: "error",
          message: error instanceof ApiError ? error.message : "The list of sources could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  const retry = () => {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  };

  const groups = useMemo(() => {
    if (state.status !== "ready") return [];
    const needle = query.trim().toLowerCase();
    const entries = state.acts
      .map(toEntry)
      .filter((e) => !needle || [e.title, e.short, e.summary].some((field) => field.toLowerCase().includes(needle)));
    return CATEGORY_ORDER.map((category) => ({
      category,
      entries: entries.filter((e) => e.category === category),
    })).filter((group) => group.entries.length > 0);
  }, [state, query]);

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
      <PageHeader
        title="Sources"
        description="The assistant searches selected excerpts from these instruments, not their full text. If a question goes beyond what is indexed, confirm the law on SAFLII."
      >
        <div className="relative w-full sm:w-64">
          <Search aria-hidden className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-subtle" />
          <label htmlFor="source-search" className="sr-only">
            Search sources
          </label>
          <input
            id="source-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search sources"
            disabled={state.status !== "ready"}
            className="h-10 w-full rounded-lg border border-line bg-surface pr-3 pl-9 text-sm text-ink placeholder:text-ink-subtle hover:border-line-strong focus:border-line-strong focus:outline-none disabled:opacity-60"
          />
        </div>
      </PageHeader>

      {state.status === "loading" && (
        <ul aria-label="Loading sources" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <li key={i} className="h-44 animate-pulse rounded-xl border border-line bg-surface-muted" />
          ))}
        </ul>
      )}

      {state.status === "error" && (
        <Alert
          tone="danger"
          title="Sources could not be loaded"
          action={
            <Button variant="secondary" size="sm" onClick={retry}>
              Try again
            </Button>
          }
        >
          {state.message}
        </Alert>
      )}

      {state.status === "ready" && (
        <div className="space-y-10">
          {groups.length === 0 && <p className="text-sm text-ink-muted">No sources match “{query.trim()}”.</p>}
          {groups.map((group) => (
            <section key={group.category} aria-labelledby={`group-${group.category}`}>
              <h2 id={`group-${group.category}`} className="mb-3 text-sm font-semibold text-ink">
                {CATEGORY_LABELS[group.category]}{" "}
                <span className="font-normal text-ink-subtle">({group.entries.length})</span>
              </h2>
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {group.entries.map((entry) => (
                  <SourceCard key={entry.key} entry={entry} />
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
