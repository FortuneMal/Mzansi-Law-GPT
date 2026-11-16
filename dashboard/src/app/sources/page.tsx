import type { Metadata } from "next";
import { LibraryView } from "@/components/library/LibraryView";

export const metadata: Metadata = { title: "Sources" };

export default function SourcesPage() {
  return <LibraryView />;
}
