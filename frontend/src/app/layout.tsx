import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KW Studio",
  description: "AI workspace shell for knowledge work",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
