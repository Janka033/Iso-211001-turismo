import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Operación en terreno · ColAdventure",
  robots: { index: false, follow: false },
};

// Área móvil de operación (guía, mecánico, recepción). Sin sidebar: se usa
// desde el teléfono en campo. Sistema visual azul (DESIGN.md).
export default function CampoLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-slate-50">{children}</div>;
}
