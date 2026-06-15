"use client";

import React, { useState } from "react";

interface ResultStepProps {
  jobId: string | null;
  onReIterate: () => void;
}

export function ResultStep({ jobId, onReIterate }: ResultStepProps) {
  const [downloading, setDownloading] = useState(false);
  const downloadUrl = jobId
    ? `http://127.0.0.1:8000/api/download/${jobId}`
    : null;

  const handleDownload = () => {
    if (!downloadUrl) return;
    setDownloading(true);
    window.location.href = `${downloadUrl}?download=true`;
    setTimeout(() => setDownloading(false), 1000);
  };

  return (
    <div className="w-full max-w-7xl mx-auto animate-fade-in">
      {/* Success banner */}
      <div className="flex items-center gap-4 mb-10">
        <div className="w-14 h-14 bg-white flex items-center justify-center shrink-0">
          <span
            className="material-symbols-outlined text-[#141313] text-[32px]"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            check
          </span>
        </div>
        <div>
          <h1 className="font-['Geist'] text-[32px] font-semibold text-white leading-tight">
            Your Tailored Resume is Ready
          </h1>
          <p className="font-['JetBrains_Mono'] text-[12px] text-[#c4c7c8] mt-1 uppercase tracking-widest">
            ATS-optimised · LaTeX compiled · PDF ready to download
          </p>
        </div>
      </div>

      {/* Split: PDF preview + actions */}
      <div className="grid grid-cols-[1fr_320px] gap-6 h-[520px]">
        {/* PDF Preview */}
        <div className="border border-[#444748] bg-[#0e0e0e] flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#444748] bg-[#1c1b1b]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-white text-[18px]">picture_as_pdf</span>
              <span className="font-['JetBrains_Mono'] text-[12px] text-white">
                tailored_resume.pdf
              </span>
            </div>
            <span className="font-['JetBrains_Mono'] text-[11px] border border-[#444748] text-[#8e9192] px-2 py-0.5 uppercase">
              PDF
            </span>
          </div>

          {/* iframe or placeholder */}
          {downloadUrl ? (
            <iframe
              src={downloadUrl}
              className="flex-grow w-full border-none bg-white"
              title="Tailored Resume Preview"
            />
          ) : (
            <div className="flex-grow flex items-center justify-center text-[#8e9192]">
              <div className="text-center">
                <span className="material-symbols-outlined text-[48px] mb-3 block">picture_as_pdf</span>
                <p className="font-['JetBrains_Mono'] text-[12px] uppercase">No preview available</p>
              </div>
            </div>
          )}
        </div>

        {/* Actions sidebar */}
        <div className="flex flex-col gap-4">
          {/* Download */}
          <div className="border border-[#444748] bg-[#1c1b1b] p-6 flex flex-col gap-4">
            <h3 className="font-['Geist'] text-[20px] font-semibold text-white">
              Download
            </h3>
            <p className="font-['JetBrains_Mono'] text-[12px] text-[#c4c7c8]">
              Your resume has been rewritten and compiled to a clean, ATS-optimised PDF.
            </p>
            <button
              id="download-pdf-btn"
              onClick={handleDownload}
              disabled={!downloadUrl || downloading}
              className="w-full h-12 bg-white text-[#141313] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-transparent hover:text-white hover:border hover:border-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {downloading ? (
                <>
                  <span className="material-symbols-outlined text-[18px] animate-spin-slow">sync</span>
                  Downloading...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  Download PDF
                </>
              )}
            </button>
          </div>

          {/* Re-iterate (disabled) */}
          <div className="border border-[#444748] bg-[#1c1b1b] p-6 flex flex-col gap-4 opacity-50">
            <h3 className="font-['Geist'] text-[20px] font-semibold text-[#c4c7c8]">
              Re-iterate
            </h3>
            <p className="font-['JetBrains_Mono'] text-[12px] text-[#8e9192]">
              Provide additional feedback and run the pipeline again to further refine your resume.
            </p>
            <div className="relative group">
              <button
                disabled
                className="w-full h-12 border border-[#444748] text-[#8e9192] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-[18px]">lock</span>
                Re-iterate Resume
              </button>
              {/* Tooltip */}
              <div className="absolute -top-9 left-1/2 -translate-x-1/2 bg-[#353434] border border-[#444748] px-3 py-1.5 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                <span className="font-['JetBrains_Mono'] text-[11px] text-white uppercase tracking-widest">
                  Coming soon
                </span>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="border border-[#444748] bg-[#0e0e0e] p-4 flex flex-col gap-3">
            <span className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase tracking-widest">
              Pipeline Summary
            </span>
            {[
              ["Profile", "Analyzed ✓"],
              ["Job Requirements", "Mapped ✓"],
              ["Gap Analysis", "Complete ✓"],
              ["Interview", "Personalized ✓"],
              ["PDF", "Compiled ✓"],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between items-center">
                <span className="font-['JetBrains_Mono'] text-[11px] text-[#c4c7c8]">{label}</span>
                <span className="font-['JetBrains_Mono'] text-[11px] text-green-400">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
