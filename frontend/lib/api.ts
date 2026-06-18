/** Base del backend FastAPI. Falla claro si falta la variable de entorno. */
export function apiBase(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error(
      "Falta NEXT_PUBLIC_API_URL. Configúrala en frontend/.env.local (ver .env.local.example).",
    );
  }
  return url;
}
