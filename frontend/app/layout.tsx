import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TailorResume — AI Resume Maker & Resume Updater to JD",
  description:
    "TailorResume is the ultimate AI resume maker and updater. Upload your resume and job description (JD) to rewrite, optimize, and tailor your resume for ATS systems in seconds.",
  keywords: [
    "resume maker",
    "resume updater",
    "resume updater to a jd",
    "tailor resume to jd",
    "AI resume builder",
    "ATS resume optimizer",
    "AI resume tailoring",
    "resume rewriter",
    "job description resume aligner"
  ],
  authors: [{ name: "TailorResume Team" }],
  creator: "TailorResume",
  metadataBase: new URL("https://tailor-resume-xi.vercel.app"),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "TailorResume — AI Resume Maker & Resume Updater to JD",
    description:
      "Align your resume with any job description in seconds using our advanced AI-powered pipeline. Stop getting filtered out by ATS.",
    url: "https://tailor-resume-xi.vercel.app",
    siteName: "TailorResume",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "TailorResume — AI Resume Maker & Resume Updater to JD",
    description:
      "Transform your resume to match job descriptions using advanced AI tailoring.",
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || "google_verification_placeholder_code",
    other: {
      "msvalidate.01": process.env.NEXT_PUBLIC_BING_SITE_VERIFICATION || "bing_verification_placeholder_code",
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": "https://tailor-resume-xi.vercel.app/#website",
        "url": "https://tailor-resume-xi.vercel.app",
        "name": "TailorResume",
        "description": "AI Resume Maker & Resume Updater to JD",
        "publisher": {
          "@type": "Organization",
          "name": "TailorResume",
          "logo": {
            "@type": "ImageObject",
            "url": "https://tailor-resume-xi.vercel.app/favicon.ico"
          }
        }
      },
      {
        "@type": "SoftwareApplication",
        "@id": "https://tailor-resume-xi.vercel.app/#software",
        "name": "TailorResume",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "All",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        },
        "description": "An AI-powered resume maker and updater that tailors resumes to specific job descriptions (JDs) using dynamic gap analysis and ATS optimization pipelines.",
        "browserRequirements": "Requires HTML5 compatible browser",
        "featureList": [
          "AI Resume Rewriting",
          "Job Description Scraper",
          "ATS Compliance Check",
          "Resume-to-JD Gap Analysis",
          "LaTeX Resume Compiling"
        ]
      }
    ]
  };

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
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="film-grain">{children}</body>
    </html>
  );
}
