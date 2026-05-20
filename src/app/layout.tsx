import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hledání synonym — Národní autority ČR",
  description:
    "Vektorové vyhledávání synonym v autoritním souboru Národní knihovny ČR",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="cs">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
