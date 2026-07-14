/** Logotipo de ColAdventure: marca de montaña + wordmark.
 *
 * Variantes:
 * - default / onDark: sistema verde actual (dashboard, onboarding, login).
 * - marca / marcaOnDark: sistema azul DESIGN.md (hoy solo la landing).
 */
export function Logo({
  className = "",
  variant = "default",
}: {
  className?: string;
  variant?: "default" | "onDark" | "marca" | "marcaOnDark";
}) {
  const dark = variant === "onDark" || variant === "marcaOnDark";
  const azul = variant === "marca" || variant === "marcaOnDark";

  const tile = dark
    ? "bg-white/15"
    : azul
      ? "bg-marca-gradient"
      : "bg-brand-gradient";
  const word = dark
    ? azul
      ? "text-naranja-400"
      : "text-accent-400"
    : azul
      ? "text-marca-600"
      : "text-brand-600";
  const sol = azul ? "#FB923C" : "#FBBF24";

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-lg text-white shadow-card ${tile}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
          <path d="M3 19h18L14.5 7.5l-3 5-2-3L3 19z" fill="currentColor" opacity="0.95" />
          <circle cx="17.5" cy="6.5" r="2" fill={sol} />
        </svg>
      </span>
      <span
        className={`font-display text-lg font-bold tracking-tight ${
          dark ? "text-white" : "text-tinta"
        }`}
      >
        Col
        <span className={word}>Adventure</span>
      </span>
    </span>
  );
}
