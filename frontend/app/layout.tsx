import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TailorResume — AI-Powered Resume Tailoring",
  description:
    "Upload your resume and a job description. Our LangGraph AI pipeline rewrites your resume to pass ATS filters and impress hiring managers.",
  keywords: ["resume", "AI", "ATS", "job application", "tailor resume"],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* JetBrains Mono for code labels + Geist for headlines/body */}
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Geist:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
        {/* Material Symbols */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="film-grain">{children}</body>
    </html>
  );
}
