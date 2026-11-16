import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "icon";

const VARIANTS: Record<Variant, string> = {
  // Disabled primary buttons turn neutral rather than fading, which looks muddy on dark surfaces.
  primary:
    "bg-brand text-on-brand hover:bg-brand-hover shadow-card disabled:bg-surface-muted disabled:text-ink-subtle disabled:shadow-none disabled:opacity-100",
  secondary: "bg-surface text-ink border border-line hover:border-line-strong hover:bg-surface-muted shadow-card",
  ghost: "text-ink-muted hover:text-ink hover:bg-surface-muted",
  danger: "bg-surface text-danger border border-line hover:bg-danger-soft hover:border-danger/40",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px] gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  icon: "h-9 w-9 justify-center",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = "md", className, type = "button", ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex shrink-0 items-center rounded-lg font-medium transition-colors",
        "disabled:pointer-events-none disabled:opacity-50",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    />
  );
});
