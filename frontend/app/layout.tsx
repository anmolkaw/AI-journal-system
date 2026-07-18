import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ArvyaX Reflections | AI-Assisted Journal",
  description: "Private nature-session journaling with structured AI emotion analysis and insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
