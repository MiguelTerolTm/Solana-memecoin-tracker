import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Solana Memecoin Intelligence Tracker",
  description: "Herramienta de investigación de memecoins de Solana. Solo lectura, sin wallets, sin trading automático.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
