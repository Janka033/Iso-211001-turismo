"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/logo";
import { LogoutButton } from "@/app/dashboard/logout-button";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Panel", icon: <IconHome /> },
  { href: "/dashboard/ruta", label: "Tu ruta", icon: <IconRoute /> },
  { href: "/dashboard#documentos", label: "Documentos", icon: <IconDoc /> },
  { href: "/dashboard/inventario", label: "Inventario", icon: <IconBox /> },
  { href: "/campo", label: "Terreno", icon: <IconCompass /> },
  { href: "/dashboard/calidad", label: "Calidad", icon: <IconShield /> },
  { href: "/onboarding", label: "Onboarding", icon: <IconChat /> },
  { href: "/dashboard#asistente", label: "Asistente", icon: <IconSpark /> },
  { href: "/dashboard#config", label: "Configuración", icon: <IconGear /> },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-marca-900 px-4 py-6 text-white md:flex">
      <div className="px-2">
        <Logo variant="onDark" />
      </div>

      <nav className="mt-8 flex-1 space-y-1">
        {NAV.map((item) => {
          const base = item.href.split("#")[0];
          const isActive = !item.href.includes("#") && base === pathname;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-white/12 text-white"
                  : "text-marca-100/70 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className="text-marca-200">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 rounded-xl bg-white/5 p-4">
        <p className="text-xs text-marca-100/70">¿Dudas con la norma?</p>
        <p className="mt-0.5 text-sm font-medium">Pregúntale al asistente</p>
        <div className="mt-3">
          <LogoutButton />
        </div>
      </div>
    </aside>
  );
}

function IconHome() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M3 9l7-5.5L17 9v7a1 1 0 0 1-1 1h-3v-5H7v5H4a1 1 0 0 1-1-1V9Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
function IconRoute() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <circle cx="5" cy="4.5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="15" cy="15.5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7 4.5h6a3 3 0 0 1 0 6H7a3 3 0 0 0 0 6h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
function IconDoc() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M5 3h6l4 4v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M11 3v4h4M7 11h6M7 14h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
function IconBox() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M3 6.5 10 3l7 3.5v7L10 17l-7-3.5v-7Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M3 6.5 10 10m0 0 7-3.5M10 10v7" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
function IconCompass() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <circle cx="10" cy="10" r="7.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="m13 7-2 4-4 2 2-4 4-2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
function IconShield() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M10 2.5 16.5 5v4.5c0 4-2.8 6.9-6.5 8-3.7-1.1-6.5-4-6.5-8V5L10 2.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="m7.5 9.8 1.8 1.8 3.2-3.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function IconChat() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M4 4h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H8l-4 3v-3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
function IconSpark() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <path d="M10 3l1.8 4.2L16 9l-4.2 1.8L10 15l-1.8-4.2L4 9l4.2-1.8L10 3Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
function IconGear() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15 5l-1.4 1.4M6.4 13.6 5 15M15 15l-1.4-1.4M6.4 6.4 5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
