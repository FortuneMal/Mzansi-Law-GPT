import { memo } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/cn";

/** react-markdown passes its AST node as a prop; drop it so it never reaches the DOM. */
function dom<P extends { node?: unknown }>(props: P): Omit<P, "node"> {
  const rest = { ...props };
  delete rest.node;
  return rest;
}

/**
 * Renders model output as formatted text. react-markdown does not render raw HTML and sanitises
 * link URLs by default, so model output cannot inject markup or script.
 */
const components: Components = {
  // Answers rarely need page-level headings; map them down so they sit inside the message.
  h1: (props) => <h3 {...dom(props)} className="mt-6 mb-2 font-serif text-lg font-semibold text-ink first:mt-0" />,
  h2: (props) => <h3 {...dom(props)} className="mt-6 mb-2 font-serif text-lg font-semibold text-ink first:mt-0" />,
  h3: (props) => <h4 {...dom(props)} className="mt-5 mb-1.5 text-[15px] font-semibold text-ink first:mt-0" />,
  h4: (props) => <h5 {...dom(props)} className="mt-4 mb-1 text-sm font-semibold text-ink first:mt-0" />,
  p: (props) => <p {...dom(props)} className="my-3 first:mt-0 last:mb-0" />,
  ul: (props) => <ul {...dom(props)} className="my-3 list-disc space-y-1.5 pl-5 marker:text-ink-subtle" />,
  ol: (props) => <ol {...dom(props)} className="my-3 list-decimal space-y-1.5 pl-5 marker:text-ink-subtle" />,
  li: (props) => <li {...dom(props)} className="pl-1 [&>ol]:my-1.5 [&>ul]:my-1.5" />,
  strong: (props) => <strong {...dom(props)} className="font-semibold text-ink" />,
  a: (props) => (
    <a
      {...dom(props)}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-brand underline decoration-brand/30 underline-offset-2 hover:decoration-brand"
    />
  ),
  blockquote: (props) => <blockquote {...dom(props)} className="my-3 border-l-2 border-line-strong pl-4 text-ink-muted" />,
  hr: () => <hr className="my-5 border-line" />,
  code: (props) => (
    <code
      {...dom(props)}
      className={cn("rounded bg-surface-muted px-1.5 py-0.5 font-mono text-[0.9em]", props.className)}
    />
  ),
  pre: (props) => (
    <pre
      {...dom(props)}
      className="my-3 overflow-x-auto rounded-lg bg-surface-muted p-3 text-[13px] [&>code]:bg-transparent [&>code]:p-0"
    />
  ),
  table: (props) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-line">
      <table {...dom(props)} className="w-full border-collapse text-left text-sm" />
    </div>
  ),
  th: (props) => <th {...dom(props)} className="border-b border-line bg-surface-muted px-3 py-2 font-semibold text-ink" />,
  td: (props) => <td {...dom(props)} className="border-b border-line px-3 py-2 align-top last:border-b-0" />,
};

export const Markdown = memo(function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cn("text-[15px] leading-7 text-ink-muted [overflow-wrap:anywhere]", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
});
