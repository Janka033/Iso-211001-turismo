"use client";

import { useEffect, useRef, useState } from "react";

import { NumeralChip } from "./ui";

/**
 * La firma de la landing: un documento del expediente que se escribe solo.
 * Lo que el operador dice con sus palabras (arriba) se convierte en cláusulas
 * formales con numeral (abajo). Lo que no dijo NO se inventa: queda como
 * [PENDIENTE: …] visible. Cierra con el sello de trazabilidad.
 *
 * Respeta prefers-reduced-motion: sin animación, se muestra el estado final.
 */

interface DocLine {
  text: string;
  pending?: string; // chip [PENDIENTE: …] al final de la línea
}

interface Script {
  numeral: string;
  title: string;
  spoken: string;
  lines: DocLine[];
}

const SCRIPTS: Script[] = [
  {
    numeral: "5.2",
    title: "POLÍTICA DE SEGURIDAD",
    spoken:
      "“Hacemos rafting en el río Fonce, nivel III y IV, con cinco guías certificados…”",
    lines: [
      {
        text: "La alta dirección establece la presente política para la operación de rafting en el río Fonce (nivel III–IV).",
      },
      {
        text: "La actividad se conduce con cinco (5) guías certificados y briefing de seguridad obligatorio.",
      },
      {
        text: "Contacto de emergencia ARL:",
        pending: "[PENDIENTE: teléfono de la ARL]",
      },
    ],
  },
  {
    numeral: "8.2",
    title: "PLAN DE EMERGENCIAS",
    spoken:
      "“Si el río crece evacuamos por el sendero del puente y llamamos a los bomberos de San Gil…”",
    lines: [
      {
        text: "Ante crecida súbita del río, la evacuación se realiza por el sendero del puente hacia el punto de encuentro.",
      },
      {
        text: "Cadena de llamado: Bomberos San Gil (119) y coordinador de operaciones.",
      },
      {
        text: "Punto de encuentro georreferenciado:",
        pending: "[PENDIENTE: coordenadas del punto]",
      },
    ],
  },
];

const TYPE_MS = 34; // por carácter
const LINE_MS = 900; // entre cláusulas
const HOLD_MS = 5200; // documento completo en pantalla

export function LiveDocument() {
  const [scriptIdx, setScriptIdx] = useState(0);
  const [typed, setTyped] = useState(0); // chars de la frase hablada
  const [linesShown, setLinesShown] = useState(0);
  const [stamped, setStamped] = useState(false);
  const [reduced, setReduced] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const script = SCRIPTS[scriptIdx];

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (reduced) return; // estado final estático

    const push = (fn: () => void, ms: number) => {
      timers.current.push(setTimeout(fn, ms));
    };

    setTyped(0);
    setLinesShown(0);
    setStamped(false);

    // 1. Tipear la frase del operador.
    const chars = script.spoken.length;
    for (let c = 1; c <= chars; c++) push(() => setTyped(c), 350 + c * TYPE_MS);
    const typedDone = 350 + chars * TYPE_MS;

    // 2. Las cláusulas aparecen una a una.
    script.lines.forEach((_, i) => {
      push(() => setLinesShown(i + 1), typedDone + 500 + i * LINE_MS);
    });
    const linesDone = typedDone + 500 + script.lines.length * LINE_MS;

    // 3. Sello y pausa; luego el siguiente guion.
    push(() => setStamped(true), linesDone + 300);
    push(() => setScriptIdx((s) => (s + 1) % SCRIPTS.length), linesDone + HOLD_MS);

    return () => {
      timers.current.forEach(clearTimeout);
      timers.current = [];
    };
  }, [script, reduced]);

  const showAll = reduced;
  const typedText = showAll ? script.spoken : script.spoken.slice(0, typed);
  const visibleLines = showAll ? script.lines.length : linesShown;
  const showStamp = showAll || stamped;

  return (
    <div
      className="relative w-full max-w-md rounded-2xl bg-white shadow-card-marca-hover ring-1 ring-marca-950/10"
      aria-label={`Ejemplo: ${script.title} generándose desde las palabras del operador`}
    >
      {/* Pestaña del expediente */}
      <div className="flex items-center justify-between rounded-t-2xl border-b border-slate-100 bg-papel px-5 py-3">
        <span className="font-mono text-[11px] font-semibold tracking-[0.18em] text-slate-500">
          {script.title}
        </span>
        <NumeralChip>NTC-ISO 21101 · {script.numeral}</NumeralChip>
      </div>

      <div className="space-y-4 px-5 py-5">
        {/* Lo que dijo el operador */}
        <div className="rounded-xl bg-marca-50 px-4 py-3">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-marca-600">
            Tú lo cuentas
          </p>
          <p className="mt-1 min-h-[3.5rem] text-[15px] leading-snug text-marca-900">
            {typedText}
            {!showAll && typed < script.spoken.length && (
              <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-marca-600 animate-caret" />
            )}
          </p>
        </div>

        {/* El documento se redacta */}
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            El expediente lo formaliza
          </p>
          <div className="mt-2 min-h-[10.5rem] space-y-2.5">
            {script.lines.slice(0, visibleLines).map((line, i) => (
              <p
                key={`${scriptIdx}-${i}`}
                className={`border-l-2 border-marca-200 pl-3 text-[13.5px] leading-snug text-slate-700 ${
                  showAll ? "" : "animate-doc-line"
                }`}
              >
                {line.text}
                {line.pending && (
                  <span className="ml-1.5 inline-block rounded bg-flag-100 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-flag-600">
                    {line.pending}
                  </span>
                )}
              </p>
            ))}
          </div>
        </div>
      </div>

      {/* Sello de trazabilidad */}
      <div className="flex items-center justify-between gap-3 rounded-b-2xl border-t border-dashed border-slate-200 px-5 py-3">
        <span className="truncate font-mono text-[10px] text-slate-400">
          plantilla v1 · snapshot ✓
        </span>
        {showStamp && (
          <span
            className={`rounded border-2 border-cielo-600 px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-widest text-cielo-600 ${
              showAll ? "-rotate-3" : "animate-stamp-in"
            }`}
          >
            Generado · v1
          </span>
        )}
      </div>
    </div>
  );
}
