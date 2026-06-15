"use client";

import React, { useRef, useState, useCallback } from "react";

interface UploadStepProps {
  resumeFile: File | null;
  jobUrl: string;
  jobText: string;
  jobTab: "url" | "text";
  onResumeChange: (file: File | null) => void;
  onUrlChange: (url: string) => void;
  onTextChange: (text: string) => void;
  onTabChange: (tab: "url" | "text") => void;
  onNext: () => void;
}

export function UploadStep({
  resumeFile,
  jobUrl,
  jobText,
  jobTab,
  onResumeChange,
  onUrlChange,
  onTextChange,
  onTabChange,
  onNext,
}: UploadStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const hasJobInput =
    jobTab === "url" ? jobUrl.trim().length > 0 : jobText.trim().length >= 50;
  const canProceed = resumeFile !== null && hasJobInput;

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) return;
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (ext === "pdf" || ext === "docx") {
        onResumeChange(file);
      }
    },
    [onResumeChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0] ?? null;
      handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  return (
    <div className="w-full max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col border border-[#444748] bg-[#0e0e0e] overflow-hidden animate-fade-in">
      {/* Split Panel */}
      <div className="flex-grow flex overflow-hidden">
        {/* LEFT — Resume Upload */}
        <div className="w-1/2 flex flex-col border-r border-[#444748] p-8">
          <div className="flex items-center gap-2 mb-6">
            <span className="material-symbols-outlined text-white">description</span>
            <h2 className="font-['Geist'] text-[20px] font-semibold text-white uppercase tracking-widest">
              Resume
            </h2>
            {resumeFile && (
              <span className="ml-auto font-['JetBrains_Mono'] text-[11px] border border-white text-white px-2 py-0.5 uppercase tracking-widest">
                Ready ✓
              </span>
            )}
          </div>

          {/* Drop zone */}
          <div
            className={`flex-grow border border-dashed flex flex-col items-center justify-center text-center p-8 cursor-pointer transition-all
              ${isDragging
                ? "border-white bg-[#1c1b1b]"
                : resumeFile
                ? "border-white bg-[#141313]"
                : "border-[#444748] bg-[#050505] hover:border-white"
              }`}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div
              className={`w-16 h-16 border flex items-center justify-center mb-6 transition-colors
                ${resumeFile ? "border-white bg-white" : "border-[#444748] hover:border-white"}`}
            >
              <span
                className={`material-symbols-outlined text-[32px] ${
                  resumeFile ? "text-[#141313]" : "text-white"
                }`}
              >
                {resumeFile ? "check" : "upload_file"}
              </span>
            </div>

            {resumeFile ? (
              <>
                <p className="font-['JetBrains_Mono'] text-[12px] text-white mb-1 break-all">
                  {resumeFile.name}
                </p>
                <p className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase tracking-widest">
                  {(resumeFile.size / 1024).toFixed(0)} KB · Click to replace
                </p>
              </>
            ) : (
              <>
                <p className="font-['JetBrains_Mono'] text-[12px] text-white mb-2">
                  Drag &amp; drop your resume PDF/DOCX here
                </p>
                <p className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase tracking-widest">
                  Max 10MB
                </p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
        </div>

        {/* RIGHT — Job Description */}
        <div className="w-1/2 flex flex-col p-8">
          <div className="flex items-center gap-2 mb-6">
            <span className="material-symbols-outlined text-white">work</span>
            <h2 className="font-['Geist'] text-[20px] font-semibold text-white uppercase tracking-widest">
              Job Description
            </h2>
            {hasJobInput && (
              <span className="ml-auto font-['JetBrains_Mono'] text-[11px] border border-white text-white px-2 py-0.5 uppercase tracking-widest">
                Ready ✓
              </span>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-[1px] mb-[1px] bg-[#444748]">
            {(["text", "url"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => onTabChange(tab)}
                className={`px-6 py-2 font-['JetBrains_Mono'] text-[12px] uppercase tracking-widest transition-colors flex-1
                  ${jobTab === tab
                    ? "bg-[#353434] text-white border-b-2 border-white"
                    : "bg-[#141313] text-[#c4c7c8] hover:text-white"
                  }`}
              >
                {tab === "text" ? "Paste Text" : "Paste URL"}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-grow border border-[#444748] bg-[#0a0a0a] relative">
            {jobTab === "text" ? (
              <textarea
                value={jobText}
                onChange={(e) => onTextChange(e.target.value)}
                placeholder="Paste the full job description here... (min 50 chars)"
                className="w-full h-full bg-transparent border-none focus:outline-none focus:ring-0 p-4 font-['JetBrains_Mono'] text-[12px] text-white resize-none placeholder:text-[#8e9192] leading-relaxed"
              />
            ) : (
              <div className="p-4 flex flex-col gap-3 h-full">
                <input
                  type="url"
                  value={jobUrl}
                  onChange={(e) => onUrlChange(e.target.value)}
                  placeholder="https://www.linkedin.com/jobs/view/..."
                  className="w-full bg-transparent border border-[#444748] px-3 py-2 font-['JetBrains_Mono'] text-[12px] text-white placeholder:text-[#8e9192] focus:outline-none focus:border-white transition-colors"
                />
                <p className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase">
                  Note: Some job portals block scraping. If it fails, switch to Paste Text.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="h-20 border-t border-[#444748] bg-[#141313] flex items-center justify-between px-8 shrink-0">
        <div className="flex items-center gap-2 text-[#c4c7c8]">
          <span className="material-symbols-outlined text-[18px]">info</span>
          <p className="font-['JetBrains_Mono'] text-[12px]">
            {!resumeFile && "Upload your resume to get started."}
            {resumeFile && !hasJobInput && "Add a job description to continue."}
            {canProceed && "All set — choose your template next."}
          </p>
        </div>
        <button
          id="analyze-resume-btn"
          onClick={onNext}
          disabled={!canProceed}
          className={`h-12 px-8 font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center gap-2 transition-all
            ${canProceed
              ? "bg-white text-[#141313] hover:bg-transparent hover:text-white hover:border hover:border-white cursor-pointer"
              : "bg-[#353434] text-[#8e9192] cursor-not-allowed"
            }`}
        >
          Analyze My Resume
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
