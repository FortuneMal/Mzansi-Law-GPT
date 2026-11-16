"use client";

import { useEffect, type ReactNode } from "react";
import { AuditProvider } from "@/components/audit/AuditProvider";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { wakeBackend } from "@/lib/api";

/** App-wide client state. Lives in the root layout so conversations and reviews survive navigation. */
export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => {
    wakeBackend();
  }, []);

  return (
    <ChatProvider>
      <AuditProvider>{children}</AuditProvider>
    </ChatProvider>
  );
}
