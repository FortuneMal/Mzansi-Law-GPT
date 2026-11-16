"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, FileSearch, MessageSquareText, Scale } from "lucide-react";
import { cn } from "@/lib/cn";
import { ThemeSwitcher } from "./ThemeSwitcher";

const NAV_ITEMS = [
  { href: "/", label: "Ask", Icon: MessageSquareText },
  { href: "/review", label: "Contract review", Icon: FileSearch },
  { href: "/sources", label: "Sources", Icon: BookOpen },
] as const;

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5 rounded-lg">
      <span aria-hidden className="flex size-8 items-center justify-center rounded-lg bg-brand text-on-brand">
        <Scale className="size-4.5" />
      </span>
      <span className="leading-tight">
        <span className="block text-[15px] font-semibold tracking-tight text-ink">Mzansi Law GPT</span>
        <span className="block text-xs text-ink-subtle">South African legal research</span>
      </span>
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-dvh overflow-hidden">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2 focus:text-sm focus:shadow-raised"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-surface lg:flex">
        <div className="px-5 pt-5 pb-6">
          <Logo />
        </div>
        <nav aria-label="Main" className="flex-1 px-3">
          <ul className="space-y-0.5">
            {NAV_ITEMS.map(({ href, label, Icon }) => {
              const active = isActive(pathname, href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex h-9 items-center gap-3 rounded-lg px-3 text-sm transition-colors",
                      active
                        ? "bg-brand-soft font-medium text-brand-ink"
                        : "text-ink-muted hover:bg-surface-muted hover:text-ink",
                    )}
                  >
                    <Icon aria-hidden className="size-4" />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="space-y-3 border-t border-line px-5 py-4">
          <ThemeSwitcher />
          <p className="text-xs leading-5 text-ink-subtle">
            AI-generated guidance, not legal advice. Consult a qualified attorney for your situation.
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile header */}
        <header className="shrink-0 border-b border-line bg-surface lg:hidden">
          <div className="flex h-14 items-center justify-between px-4">
            <Logo />
            <ThemeSwitcher />
          </div>
          <nav aria-label="Main" className="px-2">
            <ul className="flex">
              {NAV_ITEMS.map(({ href, label }) => {
                const active = isActive(pathname, href);
                return (
                  <li key={href} className="flex-1">
                    <Link
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex h-10 items-center justify-center border-b-2 text-[13px] transition-colors",
                        active
                          ? "border-brand font-medium text-ink"
                          : "border-transparent text-ink-muted hover:text-ink",
                      )}
                    >
                      {label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </header>

        <main id="main" tabIndex={-1} className="min-h-0 flex-1 overflow-y-auto scrollbar-thin focus:outline-none">
          {children}
        </main>
      </div>
    </div>
  );
}
