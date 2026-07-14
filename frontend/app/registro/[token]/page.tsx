import type { Metadata } from "next";

import { RegistroClient } from "./registro-client";

export const metadata: Metadata = {
  title: "Registro de participante · ColAdventure",
  robots: { index: false, follow: false },
};

export default function RegistroPage({ params }: { params: { token: string } }) {
  return <RegistroClient token={params.token} />;
}
