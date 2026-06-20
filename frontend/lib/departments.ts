/**
 * Departamentos de Colombia con identidad de turismo de aventura.
 * Alimenta el hero regional de la landing: al cambiar de departamento cambian
 * el paisaje (escena SVG), el titular, las actividades insignia y el acento.
 *
 * Incluye centroide (lat/lng) para detectar la región más cercana a la
 * ubicación del navegador. Es contenido de presentación; no toca el motor.
 */

export type SceneKey =
  | "canyon"
  | "mountains"
  | "paramo"
  | "desert"
  | "sea"
  | "coffee"
  | "llanos";

export interface Department {
  id: string;
  name: string;
  zone: string;
  tagline: string;
  description: string;
  activities: string[];
  scene: SceneKey;
  sky: [string, string, string];
  accent: string;
  stat: { value: string; label: string };
  /** Centroide aproximado para detección por geolocalización. */
  lat: number;
  lng: number;
}

export const DEPARTMENTS: Department[] = [
  {
    id: "santander",
    name: "Santander",
    zone: "San Gil · Cañón del Chicamocha",
    tagline: "Donde nació el turismo de aventura en Colombia.",
    description:
      "Rafting en el río Suárez, parapente sobre el Chicamocha, espeleología y torrentismo. La cuna de la aventura merece documentos a su altura.",
    activities: ["Rafting", "Parapente", "Espeleología", "Torrentismo"],
    scene: "canyon",
    sky: ["#0E2A52", "#1B5BC0", "#F9A03F"],
    accent: "#F97316",
    stat: { value: "Río Suárez", label: "Rafting nivel IV-V" },
    lat: 6.64,
    lng: -73.13,
  },
  {
    id: "antioquia",
    name: "Antioquia",
    zone: "Guatapé · San Félix",
    tagline: "Montañas, embalses y vuelo libre.",
    description:
      "Parapente en San Félix, kayak en los embalses y senderismo entre montañas. Una operación de talla mundial con respaldo normativo.",
    activities: ["Parapente", "Kayak", "Senderismo", "Ciclomontañismo"],
    scene: "mountains",
    sky: ["#0E2A52", "#1466C8", "#4FC3E8"],
    accent: "#22B8CF",
    stat: { value: "San Félix", label: "Despegue de parapente" },
    lat: 6.55,
    lng: -75.6,
  },
  {
    id: "boyaca",
    name: "Boyacá",
    zone: "Sierra Nevada del Cocuy · Páramo",
    tagline: "Cumbres, lagunas y páramo infinito.",
    description:
      "Montañismo en el Cocuy, senderismo de altura y travesías de páramo. Terreno exigente que pide protocolos serios de seguridad.",
    activities: ["Montañismo", "Senderismo de altura", "Espeleología", "Ciclismo"],
    scene: "paramo",
    sky: ["#16235C", "#3A4FB5", "#8FA3E8"],
    accent: "#A78BFA",
    stat: { value: "El Cocuy", label: "Glaciar a 5.330 m" },
    lat: 5.54,
    lng: -73.36,
  },
  {
    id: "cundinamarca",
    name: "Cundinamarca",
    zone: "Suesca · Tobia",
    tagline: "Roca, río y adrenalina cerca de Bogotá.",
    description:
      "Escalada en las rocas de Suesca, rafting y torrentismo en Tobia. El destino de aventura favorito de la capital.",
    activities: ["Escalada en roca", "Rafting", "Torrentismo", "Parapente"],
    scene: "mountains",
    sky: ["#0E2A52", "#1F5DBC", "#7FB2EE"],
    accent: "#3B82F6",
    stat: { value: "Suesca", label: "Escalada en roca" },
    lat: 5.0,
    lng: -74.03,
  },
  {
    id: "huila",
    name: "Huila",
    zone: "Desierto de la Tatacoa",
    tagline: "Desierto, estrellas y río Magdalena.",
    description:
      "Rafting en el alto Magdalena, astroturismo en la Tatacoa y senderismo entre cárcavas. Paisajes únicos, riesgos bien gestionados.",
    activities: ["Rafting", "Astroturismo", "Senderismo", "Espeleología"],
    scene: "desert",
    sky: ["#1A1740", "#7A3DA8", "#F08A3C"],
    accent: "#F59E0B",
    stat: { value: "La Tatacoa", label: "Cielo de astroturismo" },
    lat: 2.55,
    lng: -75.52,
  },
  {
    id: "magdalena",
    name: "Magdalena",
    zone: "Tayrona · Sierra Nevada",
    tagline: "Del mar Caribe a la Sierra Nevada.",
    description:
      "Buceo en el Tayrona, travesía a Ciudad Perdida y kitesurf en el Caribe. Del nivel del mar a la montaña, todo con trazabilidad.",
    activities: ["Buceo", "Trekking Ciudad Perdida", "Snorkel", "Kitesurf"],
    scene: "sea",
    sky: ["#0B3A6B", "#1E88C7", "#F7C26B"],
    accent: "#FB923C",
    stat: { value: "Tayrona", label: "Buceo en arrecife" },
    lat: 10.4,
    lng: -74.0,
  },
  {
    id: "quindio",
    name: "Quindío",
    zone: "Valle del Cocora · Eje Cafetero",
    tagline: "Palmas de cera y montañas de niebla.",
    description:
      "Senderismo entre palmas de cera, canopy y aviturismo en el Eje Cafetero. El paisaje cultural cafetero, listo para auditoría.",
    activities: ["Senderismo", "Canopy", "Cabalgata", "Aviturismo"],
    scene: "coffee",
    sky: ["#15315E", "#2E78B8", "#9FD6E6"],
    accent: "#38BDF8",
    stat: { value: "Cocora", label: "Palma de cera, 60 m" },
    lat: 4.46,
    lng: -75.67,
  },
  {
    id: "meta",
    name: "Meta",
    zone: "Caño Cristales · Los Llanos",
    tagline: "El río de los cinco colores y la llanura infinita.",
    description:
      "Senderismo a Caño Cristales, safari llanero y kayak en la Orinoquía. Naturaleza extraordinaria con operación responsable.",
    activities: ["Senderismo", "Safari llanero", "Kayak", "Rafting"],
    scene: "llanos",
    sky: ["#0E2A52", "#2563C9", "#F2935C"],
    accent: "#EC4899",
    stat: { value: "Caño Cristales", label: "El río de 5 colores" },
    lat: 3.5,
    lng: -73.2,
  },
  {
    id: "valle",
    name: "Valle del Cauca",
    zone: "Pacífico · Cali",
    tagline: "Ballenas en el Pacífico y vuelo sobre Cali.",
    description:
      "Avistamiento de ballenas, buceo en el Pacífico y parapente sobre el valle. Aventura entre el mar y la cordillera.",
    activities: ["Avistamiento de ballenas", "Buceo", "Parapente", "Senderismo"],
    scene: "sea",
    sky: ["#0B3A6B", "#1466B0", "#7FCBE0"],
    accent: "#2DD4BF",
    stat: { value: "Pacífico", label: "Ballenas jorobadas" },
    lat: 3.8,
    lng: -76.6,
  },
  {
    id: "risaralda",
    name: "Risaralda",
    zone: "Santuario del Otún · Eje Cafetero",
    tagline: "Niebla, café y aves entre montañas.",
    description:
      "Senderismo en el Otún Quimbaya, parapente y aviturismo. El corazón del Eje Cafetero, con cumplimiento al día.",
    activities: ["Senderismo", "Parapente", "Aviturismo", "Ciclomontañismo"],
    scene: "coffee",
    sky: ["#163763", "#2E78B8", "#A8DCE8"],
    accent: "#34D399",
    stat: { value: "Otún", label: "Bosque de niebla" },
    lat: 5.0,
    lng: -75.9,
  },
  {
    id: "caldas",
    name: "Caldas",
    zone: "Nevado del Ruiz · Manizales",
    tagline: "Nevados, termales y alta montaña.",
    description:
      "Montañismo en el Nevado del Ruiz, termales y senderismo de páramo. Riesgo de altura que exige protocolos rigurosos.",
    activities: ["Montañismo", "Termalismo", "Senderismo", "Ciclismo"],
    scene: "mountains",
    sky: ["#0E2A52", "#2D6BC0", "#BFE3F2"],
    accent: "#60A5FA",
    stat: { value: "Nevado del Ruiz", label: "Volcán a 5.321 m" },
    lat: 5.07,
    lng: -75.52,
  },
  {
    id: "tolima",
    name: "Tolima",
    zone: "Cañón del Combeima · Nevado del Tolima",
    tagline: "Cañones, nevados y ríos bravos.",
    description:
      "Rafting, montañismo en el Nevado del Tolima y senderismo en el Combeima. Aventura de cordillera con respaldo normativo.",
    activities: ["Rafting", "Montañismo", "Senderismo", "Torrentismo"],
    scene: "mountains",
    sky: ["#0E2A52", "#1F5DBC", "#79B6EE"],
    accent: "#38BDF8",
    stat: { value: "Combeima", label: "Cañón de montaña" },
    lat: 4.43,
    lng: -75.23,
  },
  {
    id: "narino",
    name: "Nariño",
    zone: "Laguna de la Cocha · Galeras",
    tagline: "Volcanes, lagunas y páramo del sur.",
    description:
      "Senderismo en La Cocha, ascenso al Galeras y travesías de páramo. Frontera andina con operación responsable.",
    activities: ["Senderismo", "Montañismo", "Kayak", "Aviturismo"],
    scene: "paramo",
    sky: ["#16235C", "#3A4FB5", "#9FB1EC"],
    accent: "#818CF8",
    stat: { value: "La Cocha", label: "Laguna andina" },
    lat: 1.3,
    lng: -77.4,
  },
  {
    id: "norte-santander",
    name: "Norte de Santander",
    zone: "Pamplona · Páramo de Santurbán",
    tagline: "Páramo, cañones y senderos de frontera.",
    description:
      "Senderismo en Santurbán, ciclomontañismo y espeleología. Naturaleza de altura con seguridad documentada.",
    activities: ["Senderismo", "Ciclomontañismo", "Espeleología", "Parapente"],
    scene: "paramo",
    sky: ["#16235C", "#37509E", "#8FA3E8"],
    accent: "#A78BFA",
    stat: { value: "Santurbán", label: "Páramo protegido" },
    lat: 7.9,
    lng: -72.9,
  },
  {
    id: "choco",
    name: "Chocó",
    zone: "Nuquí · Bahía Solano",
    tagline: "Selva y ballenas en el Pacífico salvaje.",
    description:
      "Avistamiento de ballenas, surf, buceo y senderismo de selva. Aventura en uno de los lugares más biodiversos del planeta.",
    activities: ["Avistamiento de ballenas", "Surf", "Buceo", "Senderismo"],
    scene: "sea",
    sky: ["#0B3A6B", "#1670B0", "#86D2DE"],
    accent: "#2DD4BF",
    stat: { value: "Nuquí", label: "Ballenas y selva" },
    lat: 5.7,
    lng: -77.0,
  },
  {
    id: "san-andres",
    name: "San Andrés y Providencia",
    zone: "Mar de los siete colores",
    tagline: "El Caribe insular para bucear.",
    description:
      "Buceo, snorkel y kayak en la tercera barrera de coral más grande del mundo. Aventura marina con protocolos al día.",
    activities: ["Buceo", "Snorkel", "Kayak", "Kitesurf"],
    scene: "sea",
    sky: ["#0B3A6B", "#1E9AD0", "#7FE3DE"],
    accent: "#22D3EE",
    stat: { value: "Barrera de coral", label: "Buceo de clase mundial" },
    lat: 12.55,
    lng: -81.72,
  },
  {
    id: "casanare",
    name: "Casanare",
    zone: "Hato llanero · Orinoquía",
    tagline: "Safari, ríos y atardeceres de llano.",
    description:
      "Safari de fauna, cabalgata llanera y kayak en los ríos de la Orinoquía. Turismo de naturaleza con operación segura.",
    activities: ["Safari de fauna", "Cabalgata", "Kayak", "Aviturismo"],
    scene: "llanos",
    sky: ["#0E2A52", "#2563C9", "#F2935C"],
    accent: "#FB923C",
    stat: { value: "Orinoquía", label: "Safari de llano" },
    lat: 5.34,
    lng: -71.4,
  },
  {
    id: "amazonas",
    name: "Amazonas",
    zone: "Leticia · Río Amazonas",
    tagline: "La selva más grande del mundo, a tu cuidado.",
    description:
      "Senderismo de selva, canopy, kayak y avistamiento de fauna. La aventura amazónica exige el máximo estándar de seguridad.",
    activities: ["Senderismo de selva", "Canopy", "Kayak", "Avistamiento de fauna"],
    scene: "coffee",
    sky: ["#15315E", "#2E78B8", "#9FD6E6"],
    accent: "#34D399",
    stat: { value: "Río Amazonas", label: "Selva tropical" },
    lat: -2.5,
    lng: -70.0,
  },
];

export const DEFAULT_DEPARTMENT_ID = "santander";

export function getDepartment(id: string): Department {
  return DEPARTMENTS.find((d) => d.id === id) ?? DEPARTMENTS[0];
}

/** Departamento con el centroide más cercano a unas coordenadas. */
export function findNearestDepartment(lat: number, lng: number): Department {
  let best = DEPARTMENTS[0];
  let bestDist = Number.POSITIVE_INFINITY;
  for (const d of DEPARTMENTS) {
    const dist = (d.lat - lat) ** 2 + (d.lng - lng) ** 2;
    if (dist < bestDist) {
      bestDist = dist;
      best = d;
    }
  }
  return best;
}
