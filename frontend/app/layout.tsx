import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Assisted Journal System",
  description: "Capture and analyze journal entries with AI-powered insights.",
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
