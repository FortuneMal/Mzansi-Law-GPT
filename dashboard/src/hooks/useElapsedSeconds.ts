"use client";

import { useEffect, useState } from "react";

/** Seconds elapsed since `startedAt` (epoch ms), updated once per second. Returns 0 when not started. */
export function useElapsedSeconds(startedAt: number | null): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (startedAt == null) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  return startedAt == null ? 0 : Math.max(0, Math.floor((now - startedAt) / 1000));
}
