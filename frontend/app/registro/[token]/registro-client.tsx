"use client";

import { useEffect, useMemo, useState } from "react";

import { ConsentMarkdown } from "@/components/registro/consent-markdown";
import { SignaturePad } from "@/components/registro/signature-pad";
import { Logo } from "@/components/logo";
import {
  BLOOD_TYPES,
  DOCUMENT_TYPES,
  MEDICAL_CONDITION_LABELS,
  fetchConsent,
  submitFirma,
  submitRegistro,
  type BloodType,
  type DocumentType,
  type MedicalConditions,
  type PublicConsent,
  type RegistroTuristaIn,
} from "@/lib/public-registro";

type Step = "form" | "consent" | "done";

const EMPTY_CONDITIONS: MedicalConditions = {
  cardiaca: false,
  respiratoria: false,
  diabetes: false,
  epilepsia: false,
  embarazo: false,
  cirugia_reciente: false,
  otras: "",
};

function ageFrom(birthISO: string): number | null {
  if (!birthISO) return null;
  const b = new Date(birthISO);
  if (Number.isNaN(b.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - b.getFullYear();
  const m = now.getMonth() - b.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < b.getDate())) age--;
  return age;
}

export function RegistroClient({ token }: { token: string }) {
  const [consent, setConsent] = useState<PublicConsent | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("form");

  // Identidad
  const [documentType, setDocumentType] = useState<DocumentType>("CC");
  const [documentNumber, setDocumentNumber] = useState("");
  const [fullName, setFullName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [nationality, setNationality] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");

  // Acudiente (solo si es menor)
  const [gName, setGName] = useState("");
  const [gDoc, setGDoc] = useState("");
  const [gRel, setGRel] = useState("");
  const [gPhone, setGPhone] = useState("");

  // Contacto de emergencia
  const [ecName, setEcName] = useState("");
  const [ecRel, setEcRel] = useState("");
  const [ecPhone, setEcPhone] = useState("");

  // Salud
  const [eps, setEps] = useState("");
  const [arl, setArl] = useState("");
  const [bloodType, setBloodType] = useState<BloodType>("O+");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState<MedicalConditions>(EMPTY_CONDITIONS);
  const [medications, setMedications] = useState("");

  // Declaraciones
  const [dTruthful, setDTruthful] = useState(false);
  const [dData, setDData] = useState(false);
  const [dRisk, setDRisk] = useState(false);
  const [dSober, setDSober] = useState(false);

  // Firma
  const [participanteId, setParticipanteId] = useState<string | null>(null);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [acceptRisk, setAcceptRisk] = useState(false);
  const [signature, setSignature] = useState<string | null>(null);
  const [signedByGuardian, setSignedByGuardian] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConsent(token)
      .then(setConsent)
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Error"));
  }, [token]);

  const age = useMemo(() => ageFrom(birthDate), [birthDate]);
  const isMinor = age !== null && age < 18;

  async function handleRegistro(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!(dTruthful && dData && dRisk && dSober)) {
      setError("Debes aceptar las cuatro declaraciones para continuar.");
      return;
    }
    if (isMinor && !(gName && gDoc && gRel && gPhone)) {
      setError("Como el participante es menor de edad, completa los datos del acudiente.");
      return;
    }

    const payload: RegistroTuristaIn = {
      document_type: documentType,
      document_number: documentNumber.trim(),
      full_name: fullName.trim(),
      birth_date: birthDate,
      nationality: nationality.trim() || null,
      phone: phone.trim(),
      email: email.trim(),
      guardian: isMinor
        ? {
            nombre: gName.trim(),
            documento: gDoc.trim(),
            parentesco: gRel.trim(),
            telefono: gPhone.trim(),
          }
        : null,
      emergency_contacts: [
        { nombre: ecName.trim(), parentesco: ecRel.trim(), telefono: ecPhone.trim() },
      ],
      eps: eps.trim(),
      arl: arl.trim() || null,
      blood_type: bloodType,
      allergies: allergies.trim() || "Ninguna",
      medical_conditions: {
        ...conditions,
        otras: conditions.otras?.trim() || null,
      },
      current_medications: medications.trim() || null,
      activity_specific: {},
      declares_truthful: dTruthful,
      accepts_data_processing: dData,
      received_risk_info: dRisk,
      declares_sober: dSober,
    };

    setSubmitting(true);
    try {
      const out = await submitRegistro(token, payload);
      setParticipanteId(out.participante_id);
      setSignedByGuardian(isMinor);
      setStep("consent");
      window.scrollTo({ top: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFirma() {
    setError(null);
    if (!participanteId) return;
    if (!(acceptPrivacy && acceptRisk)) {
      setError("Debes aceptar ambas casillas para firmar.");
      return;
    }
    if (!signature) {
      setError("Dibuja tu firma en el recuadro antes de continuar.");
      return;
    }
    setSubmitting(true);
    try {
      await submitFirma(token, {
        participante_id: participanteId,
        accepted_privacy: acceptPrivacy,
        accepted_risk_info: acceptRisk,
        signature_png_base64: signature,
      });
      setStep("done");
      window.scrollTo({ top: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <Shell activity={null}>
        <div className="card p-6 text-center">
          <p className="text-4xl">🚫</p>
          <h1 className="mt-3 font-display text-lg font-bold text-marca-950">
            Enlace no disponible
          </h1>
          <p className="mt-2 text-sm text-slate-600">{loadError}</p>
          <p className="mt-4 text-sm text-slate-500">
            Pídele a la empresa un nuevo enlace de registro.
          </p>
        </div>
      </Shell>
    );
  }

  if (!consent) {
    return (
      <Shell activity={null}>
        <p className="text-center text-sm text-slate-500">Cargando…</p>
      </Shell>
    );
  }

  return (
    <Shell activity={consent.activity_name}>
      <Steps current={step} />

      {error && (
        <p className="mb-4 rounded-lg bg-flag-100 px-3 py-2 text-sm text-flag-600">
          {error}
        </p>
      )}

      {step === "form" && (
        <form onSubmit={handleRegistro} className="space-y-6">
          <Section title="Tus datos">
            <Field label="Nombre completo">
              <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={3} />
            </Field>
            <div className="grid grid-cols-3 gap-2">
              <Field label="Tipo doc." className="col-span-1">
                <select className="input" value={documentType} onChange={(e) => setDocumentType(e.target.value as DocumentType)}>
                  {DOCUMENT_TYPES.map((d) => (
                    <option key={d.id} value={d.id}>{d.id}</option>
                  ))}
                </select>
              </Field>
              <Field label="Número de documento" className="col-span-2">
                <input className="input" value={documentNumber} onChange={(e) => setDocumentNumber(e.target.value)} required inputMode="numeric" />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Fecha de nacimiento">
                <input className="input" type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required />
              </Field>
              <Field label="Nacionalidad (opcional)">
                <input className="input" value={nationality} onChange={(e) => setNationality(e.target.value)} placeholder="Colombiana" />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Teléfono">
                <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} required inputMode="tel" />
              </Field>
              <Field label="Correo">
                <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </Field>
            </div>
          </Section>

          {isMinor && (
            <Section title="Acudiente" hint="El participante es menor de edad; el acudiente firmará el consentimiento.">
              <Field label="Nombre del acudiente">
                <input className="input" value={gName} onChange={(e) => setGName(e.target.value)} required />
              </Field>
              <div className="grid grid-cols-2 gap-2">
                <Field label="Documento">
                  <input className="input" value={gDoc} onChange={(e) => setGDoc(e.target.value)} required />
                </Field>
                <Field label="Parentesco">
                  <input className="input" value={gRel} onChange={(e) => setGRel(e.target.value)} placeholder="Madre, padre…" required />
                </Field>
              </div>
              <Field label="Teléfono del acudiente">
                <input className="input" value={gPhone} onChange={(e) => setGPhone(e.target.value)} required inputMode="tel" />
              </Field>
            </Section>
          )}

          <Section title="Contacto de emergencia">
            <Field label="Nombre">
              <input className="input" value={ecName} onChange={(e) => setEcName(e.target.value)} required />
            </Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Parentesco">
                <input className="input" value={ecRel} onChange={(e) => setEcRel(e.target.value)} placeholder="Madre, pareja…" required />
              </Field>
              <Field label="Teléfono">
                <input className="input" value={ecPhone} onChange={(e) => setEcPhone(e.target.value)} required inputMode="tel" />
              </Field>
            </div>
          </Section>

          <Section title="Información de salud" hint="Se guarda cifrada y solo la ve el equipo que te atiende.">
            <div className="grid grid-cols-2 gap-2">
              <Field label="EPS">
                <input className="input" value={eps} onChange={(e) => setEps(e.target.value)} required />
              </Field>
              <Field label="ARL (opcional)">
                <input className="input" value={arl} onChange={(e) => setArl(e.target.value)} />
              </Field>
            </div>
            <Field label="Tipo de sangre">
              <select className="input" value={bloodType} onChange={(e) => setBloodType(e.target.value as BloodType)}>
                {BLOOD_TYPES.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </Field>
            <Field label="Alergias" hint='Escribe "Ninguna" si no tienes.'>
              <input className="input" value={allergies} onChange={(e) => setAllergies(e.target.value)} placeholder="Ninguna" />
            </Field>
            <div>
              <p className="label">¿Tienes alguna de estas condiciones?</p>
              <div className="grid grid-cols-1 gap-1.5">
                {MEDICAL_CONDITION_LABELS.map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-marca-600"
                      checked={conditions[key]}
                      onChange={(e) => setConditions((c) => ({ ...c, [key]: e.target.checked }))}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            <Field label="Otras condiciones (opcional)">
              <input className="input" value={conditions.otras ?? ""} onChange={(e) => setConditions((c) => ({ ...c, otras: e.target.value }))} />
            </Field>
            <Field label="Medicamentos que tomas (opcional)">
              <input className="input" value={medications} onChange={(e) => setMedications(e.target.value)} />
            </Field>
          </Section>

          <Section title="Declaraciones">
            <Check checked={dTruthful} onChange={setDTruthful}>
              Declaro que la información que entregué es verdadera.
            </Check>
            <Check checked={dData} onChange={setDData}>
              Autorizo el tratamiento de mis datos personales (Ley 1581 de 2012).
            </Check>
            <Check checked={dRisk} onChange={setDRisk}>
              Recibí información sobre los riesgos de la actividad.
            </Check>
            <Check checked={dSober} onChange={setDSober}>
              Me presentaré sin haber consumido alcohol ni sustancias psicoactivas.
            </Check>
          </Section>

          <button type="submit" disabled={submitting} className="btn-marca w-full">
            {submitting ? "Guardando…" : "Continuar al consentimiento"}
          </button>
        </form>
      )}

      {step === "consent" && (
        <div className="space-y-5">
          <Section title={`Consentimiento informado (v${consent.template_version})`}>
            <div className="max-h-72 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4">
              <ConsentMarkdown body={consent.body_md} />
            </div>
          </Section>

          <Section title={signedByGuardian ? "Firma del acudiente" : "Tu firma"}>
            <Check checked={acceptPrivacy} onChange={setAcceptPrivacy}>
              He leído y acepto el tratamiento de datos personales.
            </Check>
            <Check checked={acceptRisk} onChange={setAcceptRisk}>
              Entiendo y asumo los riesgos descritos en el consentimiento.
            </Check>
            <SignaturePad onChange={setSignature} />
            <p className="text-xs text-slate-500">
              Tu firma queda registrada con fecha, hora y dispositivo como
              evidencia legal (Ley 527 de 1999).
            </p>
          </Section>

          <button onClick={handleFirma} disabled={submitting} className="btn-marca w-full">
            {submitting ? "Registrando firma…" : "Firmar y finalizar"}
          </button>
        </div>
      )}

      {step === "done" && (
        <div className="card p-6 text-center">
          <p className="text-4xl">✅</p>
          <h1 className="mt-3 font-display text-lg font-extrabold text-marca-950">
            ¡Registro completo!
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Quedaste registrado{consent.activity_name ? ` para ${consent.activity_name}` : ""}.
            Preséntate el día de la actividad con tu documento.
          </p>
          <p className="mt-4 text-xs text-slate-400">Ya puedes cerrar esta página.</p>
        </div>
      )}
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Piezas de layout
// ---------------------------------------------------------------------------

function Shell({ activity, children }: { activity: string | null; children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="bg-marca-gradient px-5 py-6 text-white">
        <div className="mx-auto w-full max-w-md">
          <Logo variant="marcaOnDark" />
          <p className="mt-4 font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-marca-300">
            Registro de participante
          </p>
          {activity && (
            <h1 className="mt-1 font-display text-2xl font-extrabold leading-tight">
              {activity}
            </h1>
          )}
        </div>
      </header>
      <div className="mx-auto w-full max-w-md px-5 py-6">{children}</div>
    </main>
  );
}

function Steps({ current }: { current: Step }) {
  const order: Step[] = ["form", "consent", "done"];
  const labels: Record<Step, string> = {
    form: "Datos",
    consent: "Consentimiento",
    done: "Listo",
  };
  const idx = order.indexOf(current);
  return (
    <ol className="mb-6 flex items-center gap-2 text-xs font-medium">
      {order.map((s, i) => (
        <li key={s} className="flex flex-1 items-center gap-2">
          <span
            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] ${
              i <= idx ? "bg-marca-600 text-white" : "bg-slate-200 text-slate-500"
            }`}
          >
            {i < idx ? "✓" : i + 1}
          </span>
          <span className={i <= idx ? "text-marca-700" : "text-slate-400"}>{labels[s]}</span>
          {i < order.length - 1 && <span className="h-px flex-1 bg-slate-200" />}
        </li>
      ))}
    </ol>
  );
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-5">
      <h2 className="font-display text-base font-bold text-marca-950">{title}</h2>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
      <div className="mt-4 space-y-4">{children}</div>
    </section>
  );
}

function Field({
  label,
  hint,
  className,
  children,
}: {
  label: string;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={className}>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="mt-1 text-[11px] text-slate-400">{hint}</p>}
    </div>
  );
}

function Check({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="flex items-start gap-2.5 text-sm text-slate-700">
      <input
        type="checkbox"
        className="mt-0.5 h-4 w-4 shrink-0 accent-marca-600"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span>{children}</span>
    </label>
  );
}
