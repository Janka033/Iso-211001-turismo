import type { SceneKey } from "@/lib/departments";

/**
 * Escenas SVG simbólicas del turismo de aventura por región.
 * Estilo: ilustración plana, siluetas en azul marino sobre cielo degradado,
 * con un sol/acento regional. Liviano (sin imágenes) y escalable.
 */

const FAR = "#23508C";
const MID = "#142F5C";
const NEAR = "#0A1E3D";

interface SceneProps {
  scene: SceneKey;
  sky: [string, string, string];
  accent: string;
  uid: string;
  className?: string;
}

export function Scene({ scene, sky, accent, uid, className }: SceneProps) {
  return (
    <svg
      viewBox="0 0 800 520"
      className={className}
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`sky-${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={sky[0]} />
          <stop offset="55%" stopColor={sky[1]} />
          <stop offset="100%" stopColor={sky[2]} />
        </linearGradient>
        <radialGradient id={`sun-${uid}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="1" />
          <stop offset="70%" stopColor={accent} stopOpacity="0.85" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect width="800" height="520" fill={`url(#sky-${uid})`} />

      {scene === "canyon" && <Canyon uid={uid} accent={accent} />}
      {scene === "mountains" && <Mountains uid={uid} accent={accent} />}
      {scene === "paramo" && <Paramo uid={uid} accent={accent} />}
      {scene === "desert" && <Desert uid={uid} accent={accent} />}
      {scene === "sea" && <Sea uid={uid} accent={accent} />}
      {scene === "coffee" && <Coffee uid={uid} accent={accent} />}
      {scene === "llanos" && <Llanos uid={uid} accent={accent} />}
    </svg>
  );
}

function Sun({ uid, cx, cy, r = 150, core = 46 }: { uid: string; cx: number; cy: number; r?: number; core?: number; }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill={`url(#sun-${uid})`} />
      <circle cx={cx} cy={cy} r={core} fill="#FFF4E0" opacity="0.95" />
    </g>
  );
}

function Birds({ x, y, color = "#0A1E3D" }: { x: number; y: number; color?: string }) {
  const b = (dx: number, dy: number, s: number) => (
    <path
      d={`M${x + dx} ${y + dy} q${6 * s} ${-5 * s} ${12 * s} 0 q${6 * s} ${-5 * s} ${12 * s} 0`}
      stroke={color}
      strokeWidth="2.2"
      fill="none"
      strokeLinecap="round"
    />
  );
  return (
    <g opacity="0.7">
      {b(0, 0, 1)}
      {b(34, 14, 0.8)}
      {b(-26, 20, 0.7)}
    </g>
  );
}

function Canyon({ uid, accent }: { uid: string; accent: string }) {
  return (
    <g>
      <Sun uid={uid} cx={400} cy={150} r={140} core={42} />
      <Birds x={250} y={110} />
      {/* pared lejana */}
      <path d="M0 200 L120 150 L200 210 L300 170 L300 520 L0 520 Z" fill={FAR} opacity="0.5" />
      <path d="M800 190 L690 150 L600 220 L500 175 L500 520 L800 520 Z" fill={FAR} opacity="0.5" />
      {/* paredes del cañón */}
      <path d="M0 240 L150 180 L250 260 L330 230 L330 520 L0 520 Z" fill={MID} />
      <path d="M800 230 L660 180 L560 270 L470 235 L470 520 L800 520 Z" fill={MID} />
      <path d="M0 320 L130 280 L240 360 L330 330 L330 520 L0 520 Z" fill={NEAR} />
      <path d="M800 330 L690 285 L580 370 L470 335 L470 520 L800 520 Z" fill={NEAR} />
      {/* río al fondo */}
      <path d="M340 520 L370 360 Q400 330 430 360 L460 520 Z" fill={accent} opacity="0.55" />
      <path d="M362 520 L382 380 Q400 362 418 380 L438 520 Z" fill="#CFE8FF" opacity="0.5" />
    </g>
  );
}

function Mountains({ uid, accent }: { uid: string; accent: string }) {
  return (
    <g>
      <Sun uid={uid} cx={580} cy={140} r={130} core={40} />
      <Birds x={180} y={120} />
      <path d="M0 360 L180 200 L330 360 Z" fill={FAR} opacity="0.6" />
      <path d="M250 360 L470 170 L690 360 Z" fill={FAR} opacity="0.7" />
      {/* picos con nieve */}
      <path d="M-40 420 L160 230 L360 420 Z" fill={MID} />
      <path d="M120 250 L160 230 L210 268 L188 280 L165 268 L140 282 Z" fill="#EAF3FF" opacity="0.9" />
      <path d="M300 420 L520 200 L760 420 Z" fill={NEAR} />
      <path d="M470 232 L520 200 L580 244 L548 258 L520 240 L498 256 Z" fill="#EAF3FF" opacity="0.9" />
      {/* lago / reflejo */}
      <rect x="0" y="420" width="800" height="100" fill={NEAR} />
      <rect x="0" y="420" width="800" height="100" fill={accent} opacity="0.16" />
      <path d="M300 430 L520 430 L505 470 L315 470 Z" fill="#CFE8FF" opacity="0.18" />
    </g>
  );
}

function Paramo({ uid, accent }: { uid: string; accent: string }) {
  const frailejon = (x: number, y: number, s: number) => (
    <g opacity="0.92">
      <rect x={x - 3 * s} y={y - 40 * s} width={6 * s} height={42 * s} rx={3 * s} fill={NEAR} />
      <path d={`M${x} ${y - 40 * s} q${-16 * s} ${-6 * s} ${-12 * s} ${-22 * s} q${12 * s} ${10 * s} ${12 * s} ${4 * s} q0 ${-6 * s} ${12 * s} ${-4 * s} q${4 * s} ${16 * s} ${-12 * s} ${22 * s} Z`} fill={NEAR} />
    </g>
  );
  return (
    <g>
      <Sun uid={uid} cx={250} cy={150} r={120} core={38} />
      <Birds x={520} y={120} color={MID} />
      {/* colinas redondeadas */}
      <path d="M0 330 Q200 260 420 320 T800 300 L800 520 L0 520 Z" fill={FAR} opacity="0.6" />
      <path d="M0 380 Q240 320 480 372 T800 360 L800 520 L0 520 Z" fill={MID} />
      {/* laguna */}
      <ellipse cx="430" cy="430" rx="190" ry="34" fill={accent} opacity="0.35" />
      <ellipse cx="430" cy="430" rx="190" ry="34" fill="#0A1E3D" opacity="0.35" />
      <path d="M0 440 Q260 392 540 446 T800 440 L800 520 L0 520 Z" fill={NEAR} />
      {frailejon(120, 452, 1.5)}
      {frailejon(190, 470, 1.1)}
      {frailejon(660, 448, 1.6)}
      {frailejon(720, 466, 1.2)}
    </g>
  );
}

function Desert({ uid, accent }: { uid: string; accent: string }) {
  const cactus = (x: number, y: number, s: number) => (
    <g fill={NEAR}>
      <rect x={x - 5 * s} y={y - 54 * s} width={10 * s} height={56 * s} rx={5 * s} />
      <rect x={x - 22 * s} y={y - 40 * s} width={9 * s} height={26 * s} rx={4.5 * s} />
      <rect x={x - 22 * s} y={y - 44 * s} width={9 * s} height={9 * s} rx={4 * s} />
      <rect x={x + 13 * s} y={y - 46 * s} width={9 * s} height={30 * s} rx={4.5 * s} />
      <rect x={x + 13 * s} y={y - 50 * s} width={9 * s} height={9 * s} rx={4 * s} />
    </g>
  );
  return (
    <g>
      {/* estrellas en la parte alta */}
      <g fill="#FFFFFF" opacity="0.85">
        <circle cx="90" cy="70" r="1.6" /><circle cx="160" cy="120" r="1.2" />
        <circle cx="240" cy="60" r="1.8" /><circle cx="320" cy="110" r="1.3" />
        <circle cx="120" cy="150" r="1.1" /><circle cx="60" cy="110" r="1.4" />
        <circle cx="700" cy="80" r="1.6" /><circle cx="640" cy="130" r="1.2" />
      </g>
      <Sun uid={uid} cx={560} cy={210} r={150} core={48} />
      {/* dunas */}
      <path d="M0 360 Q220 300 460 350 T800 330 L800 520 L0 520 Z" fill={FAR} opacity="0.7" />
      <path d="M0 410 Q260 350 520 404 T800 386 L800 520 L0 520 Z" fill={MID} />
      <path d="M0 456 Q240 410 520 456 T800 450 L800 520 L0 520 Z" fill={NEAR} />
      {cactus(150, 452, 1.5)}
      {cactus(250, 470, 1.1)}
      {cactus(680, 452, 1.3)}
    </g>
  );
}

function Sea({ uid, accent }: { uid: string; accent: string }) {
  return (
    <g>
      <Sun uid={uid} cx={420} cy={170} r={150} core={50} />
      <Birds x={170} y={120} color="#0A1E3D" />
      {/* horizonte / mar */}
      <rect x="0" y="320" width="800" height="200" fill={MID} />
      <rect x="0" y="320" width="800" height="200" fill={accent} opacity="0.18" />
      {/* reflejo del sol */}
      <path d="M386 322 L454 322 L470 520 L370 520 Z" fill="#FFE9C2" opacity="0.35" />
      {/* olas */}
      <g stroke="#CFE8FF" strokeWidth="3" fill="none" opacity="0.55" strokeLinecap="round">
        <path d="M40 380 q30 -12 60 0 t60 0 t60 0" />
        <path d="M520 420 q30 -12 60 0 t60 0 t60 0" />
        <path d="M120 460 q30 -12 60 0 t60 0 t60 0" />
      </g>
      {/* palmera */}
      <g fill={NEAR}>
        <path d="M120 520 q-10 -150 6 -240 q4 80 -2 240 Z" />
        <g transform="translate(126 280)">
          <path d="M0 0 q-70 -30 -120 -8 q60 -34 120 -8 Z" />
          <path d="M0 0 q-50 -60 -96 -76 q66 -16 96 64 Z" />
          <path d="M0 0 q70 -30 120 -8 q-60 -34 -120 -8 Z" />
          <path d="M0 0 q50 -60 96 -76 q-66 -16 -96 64 Z" />
        </g>
      </g>
    </g>
  );
}

function Coffee({ uid, accent }: { uid: string; accent: string }) {
  const palm = (x: number, base: number, h: number) => (
    <g fill={NEAR}>
      <path d={`M${x - 3} ${base} q-2 ${-h} 3 ${-h - 8} q5 8 3 ${h + 8} Z`} />
      <g transform={`translate(${x} ${base - h - 6})`}>
        <ellipse cx="0" cy="-6" rx="26" ry="10" />
        <ellipse cx="-16" cy="2" rx="22" ry="9" transform="rotate(-28)" />
        <ellipse cx="16" cy="2" rx="22" ry="9" transform="rotate(28)" />
      </g>
    </g>
  );
  return (
    <g>
      <Sun uid={uid} cx={600} cy={150} r={120} core={40} />
      {/* bandas de niebla */}
      <rect x="0" y="250" width="800" height="40" fill="#FFFFFF" opacity="0.12" />
      <rect x="0" y="320" width="800" height="34" fill="#FFFFFF" opacity="0.10" />
      {/* colinas con surcos (terrazas de café) */}
      <path d="M0 360 Q220 300 460 352 T800 336 L800 520 L0 520 Z" fill={FAR} opacity="0.7" />
      <path d="M0 410 Q240 356 520 408 T800 396 L800 520 L0 520 Z" fill={MID} />
      <g stroke="#0A1E3D" strokeWidth="2" opacity="0.25" fill="none">
        <path d="M40 430 Q260 392 520 432" />
        <path d="M40 452 Q260 416 520 454" />
      </g>
      <path d="M0 452 Q260 410 560 456 T800 452 L800 520 L0 520 Z" fill={NEAR} />
      {/* palmas de cera */}
      {palm(150, 456, 150)}
      {palm(210, 470, 120)}
      {palm(660, 452, 160)}
    </g>
  );
}

function Llanos({ uid, accent }: { uid: string; accent: string }) {
  return (
    <g>
      <Sun uid={uid} cx={400} cy={210} r={170} core={56} />
      <Birds x={180} y={120} color="#0A1E3D" />
      {/* llanura */}
      <path d="M0 380 Q400 350 800 380 L800 520 L0 520 Z" fill={MID} />
      <path d="M0 430 Q400 408 800 430 L800 520 L0 520 Z" fill={NEAR} />
      {/* río serpenteante hacia el horizonte */}
      <path d="M380 380 Q410 430 350 470 Q300 505 420 520 L470 520 Q420 480 470 446 Q520 410 420 380 Z" fill={accent} opacity="0.5" />
      <path d="M398 384 Q420 430 372 466 Q336 494 410 510" stroke="#CFE8FF" strokeWidth="3" fill="none" opacity="0.5" />
      {/* árbol solitario */}
      <g fill={NEAR}>
        <rect x="648" y="372" width="6" height="40" rx="3" />
        <ellipse cx="651" cy="366" rx="34" ry="20" />
      </g>
    </g>
  );
}
