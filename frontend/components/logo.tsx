/** Logotipo de ColAdventure: marca de montaña + wordmark.
 *
 * Sistema azul DESIGN.md en TODA la app (dashboard, onboarding, login y
 * landing). `marca`/`marcaOnDark` se conservan como alias de compatibilidad
 * de `default`/`onDark`.
 */
export function Logo({
  className = "",
  variant = "default",
}: {
  className?: string;
  variant?: "default" | "onDark" | "marca" | "marcaOnDark";
}) {
  const dark = variant === "onDark" || variant === "marcaOnDark";

  const tile = dark ? "bg-white/15" : "bg-marca-gradient";
  const word = dark ? "text-naranja-400" : "text-marca-600";
  const sol = "#FB923C";

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
