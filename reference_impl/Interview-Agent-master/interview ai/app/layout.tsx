import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Interview Agent — ABTalks AI Cohort",
  description:
    "Personalized multi-turn technical interviews powered by Groq, based on each candidate's real 31-day AI Engineering cohort journey.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg-primary text-ink-primary antialiased">
        {children}
      </body>
    </html>
  );
}
