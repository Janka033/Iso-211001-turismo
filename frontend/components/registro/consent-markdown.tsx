import { Fragment, type ReactNode } from "react";

/**
 * Render mínimo del texto del consentimiento (markdown de nuestra propia DB).
 * Cubre lo que usan las plantillas: encabezados, listas, negritas y párrafos.
 * Se construye con elementos React (no dangerouslySetInnerHTML) para evitar
 * cualquier inyección aunque el origen sea de confianza.
 */
function renderInline(text: string): ReactNode {
  // Negritas **así**; el resto queda como texto plano.
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-marca-950">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function ConsentMarkdown({ body }: { body: string }) {
  const lines = body.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let list: string[] = [];

  const flushList = (key: string) => {
    if (list.length === 0) return;
    blocks.push(
      <ul key={key} className="my-2 list-disc space-y-1 pl-5 text-slate-700">
        {list.map((item, i) => (
          <li key={i}>{renderInline(item)}</li>
        ))}
      </ul>,
    );
    list = [];
  };

  lines.forEach((raw, idx) => {
    const line = raw.trim();
    if (line.startsWith("- ") || line.startsWith("* ")) {
      list.push(line.slice(2));
      return;
    }
    flushList(`ul-${idx}`);
    if (!line) return;
    if (line.startsWith("### ")) {
      blocks.push(
        <h3 key={idx} className="mt-4 font-display text-base font-bold text-marca-950">
          {renderInline(line.slice(4))}
        </h3>,
      );
    } else if (line.startsWith("## ")) {
      blocks.push(
        <h2 key={idx} className="mt-5 font-display text-lg font-extrabold text-marca-950">
          {renderInline(line.slice(3))}
        </h2>,
      );
    } else if (line.startsWith("# ")) {
      blocks.push(
        <h1 key={idx} className="font-display text-xl font-extrabold text-marca-950">
          {renderInline(line.slice(2))}
        </h1>,
      );
    } else {
      blocks.push(
        <p key={idx} className="my-2 leading-relaxed text-slate-700">
          {renderInline(line)}
        </p>,
      );
    }
  });
  flushList("ul-final");

  return <div className="text-sm">{blocks}</div>;
}
