import { SalidaDetailClient } from "./salida-detail-client";

export default function SalidaDetailPage({ params }: { params: { id: string } }) {
  return <SalidaDetailClient salidaId={params.id} />;
}
