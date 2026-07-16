import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/logo";
import { OnboardingChat } from "@/components/onboarding/onboarding-chat";

export const metadata: Metadata = {
  title: "Onboarding · ColAdventure",
};

export default function OnboardingPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-100 bg-white">
        <div className="section flex h-16 items-center justify-between">
          <Logo />
          <Link href="/dashboard" className="text-sm font-medium text-slate-500 hover:text-marca-700">
            Salir
          </Link>
        </div>
      </header>

      <main className="section py-10">
        <div className="max-w-2xl">
          <p className="eyebrow">Onboarding</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
            Cuéntanos cómo opera tu empresa
          </h1>
          <p className="mt-2 text-slate-600">
            Responde unas preguntas y la IA preparará tus documentos de seguridad.
            Toma pocos minutos; puedes pausar y retomar.
          </p>
        </div>

        <div className="mt-8">
          <OnboardingChat />
        </div>
      </main>
    </div>
  );
}
