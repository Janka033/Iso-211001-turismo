import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono, Public_Sans } from "next/font/google";
import "./globals.css";

/**
 * Tipografía del sistema:
 * - Archivo (display): fundición latinoamericana; "archivo" = expediente.
 * - Public Sans (cuerpo): nacida de un design system de gobierno — voz documental.
 * - IBM Plex Mono (datos): numerales, [PENDIENTE], sellos de trazabilidad.
 */
const publicSans = Public_Sans({ subsets: ["latin"], variable: "--font-sans" });
const archivo = Archivo({
  subsets: ["latin"],
  weight: ["600", "700", "800", "900"],
  variable: "--font-display",
});
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "ColAdventure — Certifícate en la NTC-ISO 21101 sin ahogarte en papeleo",
  description:
    "El expediente de seguridad de tu empresa de turismo de aventura, generado desde tu operación real. Auditable ante ONAC, sin inventar un solo dato.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="es"
      className={`${publicSans.variable} ${archivo.variable} ${plexMono.variable}`}
    >
      <body className="font-sans">{children}</body>
    </html>
  );
}
