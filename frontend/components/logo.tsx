/** Logotipo de ColAdventure: marca de montaña + wordmark. */
export function Logo({
  className = "",
  variant = "default",
}: {
  className?: string;
  variant?: "default" | "onDark";
}) {
  const onDark = variant === "onDark";
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-lg text-white shadow-card ${
          onDark ? "bg-white/15" : "bg-brand-gradient"
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
          <path d="M3 19h18L14.5 7.5l-3 5-2-3L3 19z" fill="currentColor" opacity="0.95" />
          <circle cx="17.5" cy="6.5" r="2" fill="#FBBF24" />
        </svg>
      </span>
      <span
        className={`text-lg font-semibold tracking-tight ${
          onDark ? "text-white" : "text-slate-900"
        }`}
      >
        Col
        <span className={onDark ? "text-accent-400" : "text-brand-600"}>Adventure</span>
      </span>
    </span>
  );
}
