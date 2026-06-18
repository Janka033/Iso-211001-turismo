import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ColAdventure",
  description: "Cumplimiento NTC-ISO 21101 para turismo de aventura",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
