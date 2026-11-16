import type { Metadata } from "next";
import { AuditView } from "@/components/audit/AuditView";

export const metadata: Metadata = { title: "Contract review" };

export default function ReviewPage() {
  return <AuditView />;
}
