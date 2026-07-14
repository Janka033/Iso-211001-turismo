"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Panel de firma para el turista: trazo con dedo o mouse sobre un canvas.
 * Emite el PNG en base64 (sin prefijo data-URL) que el backend valida como
 * evidencia legal (Ley 527/1999). Vacío => onChange(null).
 */
export function SignaturePad({
  onChange,
}: {
  onChange: (pngBase64: string | null) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const hasInk = useRef(false);
  const last = useRef<{ x: number; y: number } | null>(null);
  const [empty, setEmpty] = useState(true);

  // El canvas se dibuja a resolución de dispositivo (DPR) para trazo nítido en
  // móvil, pero se muestra al tamaño CSS. Reajusta al montar y al rotar.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function setup() {
      if (!canvas) return;
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.scale(ratio, ratio);
      ctx.lineWidth = 2.2;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "#172554"; // marca-950
    }
    setup();
    window.addEventListener("resize", setup);
    return () => window.removeEventListener("resize", setup);
  }, []);

  function pointFromEvent(e: React.PointerEvent<HTMLCanvasElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function start(e: React.PointerEvent<HTMLCanvasElement>) {
    e.currentTarget.setPointerCapture(e.pointerId);
    drawing.current = true;
    last.current = pointFromEvent(e);
  }

  function move(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    e.preventDefault();
    const ctx = canvasRef.current?.getContext("2d");
    const from = last.current;
    if (!ctx || !from) return;
    const to = pointFromEvent(e);
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
    last.current = to;
    if (!hasInk.current) {
      hasInk.current = true;
      setEmpty(false);
    }
  }

  function end() {
    if (!drawing.current) return;
    drawing.current = false;
    last.current = null;
    emit();
  }

  function emit() {
    const canvas = canvasRef.current;
    if (!canvas || !hasInk.current) {
      onChange(null);
      return;
    }
    // dataURL => "data:image/png;base64,XXXX": el backend acepta con o sin
    // prefijo, pero enviamos solo el payload para no inflar el request.
    const dataUrl = canvas.toDataURL("image/png");
    onChange(dataUrl.split(",")[1] ?? null);
  }

  function clear() {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (canvas && ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    hasInk.current = false;
    setEmpty(true);
    onChange(null);
  }

  return (
    <div>
      <div className="relative overflow-hidden rounded-xl border border-slate-300 bg-white">
        <canvas
          ref={canvasRef}
          onPointerDown={start}
          onPointerMove={move}
          onPointerUp={end}
          onPointerLeave={end}
          onPointerCancel={end}
          className="h-44 w-full touch-none"
          style={{ touchAction: "none" }}
        />
        {empty && (
          <span className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-slate-400">
            Firma aquí con el dedo
          </span>
        )}
        {/* Línea base de firma. */}
        <span className="pointer-events-none absolute inset-x-6 bottom-8 border-b border-dashed border-slate-300" />
      </div>
      <div className="mt-2 flex justify-end">
        <button
          type="button"
          onClick={clear}
          disabled={empty}
          className="text-sm font-medium text-slate-500 hover:text-marca-700 disabled:opacity-40"
        >
          Borrar y volver a firmar
        </button>
      </div>
    </div>
  );
}
