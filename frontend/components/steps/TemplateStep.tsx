"use client";

import React from "react";

interface TemplateStepProps {
  selectedTemplate: string;
  onSelectTemplate: (t: string) => void;
  onNext: () => void;
  onBack: () => void;
}

function DefaultPreview() {
  return (
    <div className="w-4/5 h-4/5 border border-[#444748] p-4 bg-[#141313] flex flex-col gap-2">
      <div className="w-full h-8 bg-[#353434]" />
      <div className="w-1/2 h-4 bg-[#353434]/50" />
      <div className="flex-grow flex gap-2">
        <div className="w-1/3 h-full border border-dashed border-[#444748]" />
        <div className="w-2/3 flex flex-col gap-2 pt-1">
          <div className="w-full h-2 bg-[#353434]/40" />
          <div className="w-full h-2 bg-[#353434]/40" />
          <div className="w-3/4 h-2 bg-[#353434]/40" />
          <div className="w-full h-2 bg-[#353434]/30 mt-2" />
          <div className="w-5/6 h-2 bg-[#353434]/30" />
        </div>
      </div>
    </div>
  );
}

function LockedPreview() {
  return (
    <div className="w-4/5 h-4/5 border border-[#444748] p-4 bg-[#141313] flex flex-col items-center justify-center gap-3">
      <span className="material-symbols-outlined text-[#8e9192] text-5xl">lock</span>
      <div className="w-full h-2 bg-[#353434]/20" />
      <div className="w-full h-2 bg-[#353434]/20" />
      <div className="w-3/4 h-2 bg-[#353434]/20" />
    </div>
  );
}

function ModernPreview() {
  const teal = "#0d9488";
  return (
    <div className="w-[90%] h-[88%] bg-white flex overflow-hidden shadow-lg">
      {/* Left column */}
      <div className="w-[58%] h-full p-3 border-r border-gray-200 flex flex-col gap-1.5">
        {/* Header */}
        <div className="border-b-2 pb-1.5" style={{ borderColor: teal }}>
          <div className="h-3 w-24 bg-gray-900 rounded-[1px] mb-1" />
          <div className="h-2 w-16 rounded-[1px] mb-1.5" style={{ background: teal }} />
          <div className="flex gap-2">
            <div className="h-1.5 w-12 bg-gray-300 rounded" />
            <div className="h-1.5 w-16 bg-gray-300 rounded" />
          </div>
        </div>
        {/* Summary */}
        <div>
          <div className="h-1.5 w-10 mb-1 rounded-[1px]" style={{ background: teal }} />
          <div className="h-1 w-full bg-gray-200 rounded mb-0.5" />
          <div className="h-1 w-5/6 bg-gray-200 rounded mb-0.5" />
          <div className="h-1 w-4/5 bg-gray-200 rounded" />
        </div>
        {/* Experience */}
        <div>
          <div className="h-1.5 w-14 mb-1 rounded-[1px]" style={{ background: teal }} />
          <div className="h-1.5 w-20 mb-0.5 rounded" style={{ background: teal, opacity: 0.7 }} />
          <div className="h-1 w-4/5 bg-gray-200 rounded mb-0.5" />
          <div className="h-1 w-3/4 bg-gray-200 rounded mb-1" />
          <div className="h-1.5 w-16 mb-0.5 rounded" style={{ background: teal, opacity: 0.7 }} />
          <div className="h-1 w-4/5 bg-gray-200 rounded" />
        </div>
        {/* Education */}
        <div>
          <div className="h-1.5 w-14 mb-1 rounded-[1px]" style={{ background: teal }} />
          <div className="h-1.5 w-24 mb-0.5 rounded" style={{ background: teal, opacity: 0.6 }} />
          <div className="h-1 w-3/4 bg-gray-200 rounded mb-0.5" />
          <div className="flex justify-between">
            <div className="h-1 w-12 bg-gray-300 rounded" />
            <div className="h-1 w-10 rounded" style={{ background: teal, opacity: 0.5 }} />
          </div>
        </div>
      </div>
      {/* Right column */}
      <div className="w-[42%] h-full p-3 flex flex-col gap-2" style={{ background: "#f7f8f9" }}>
        {/* Skills */}
        <div>
          <div className="h-1.5 w-8 mb-1.5 rounded-[1px]" style={{ background: teal }} />
          {[["Python", "SQL", "Java"], ["Tableau", "Power BI"], ["MySQL", "AWS"]].map((group, gi) => (
            <div key={gi} className="mb-1.5">
              <div className="h-1 w-12 mb-1 rounded" style={{ background: teal, opacity: 0.7 }} />
              <div className="flex flex-wrap gap-0.5">
                {group.map((chip) => (
                  <span
                    key={chip}
                    className="px-1 py-0.5 rounded-full border border-gray-300 bg-white text-gray-600"
                    style={{ fontSize: "5px" }}
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        {/* Projects */}
        <div>
          <div className="h-1.5 w-10 mb-1 rounded-[1px]" style={{ background: teal }} />
          <div className="h-1.5 w-16 bg-gray-800 rounded mb-0.5" />
          <div className="flex gap-0.5 mb-0.5">
            <span className="px-1 py-0.5 rounded-full border border-teal-200 bg-teal-50 text-teal-600" style={{ fontSize: "4px" }}>ML</span>
            <span className="px-1 py-0.5 rounded-full border border-teal-200 bg-teal-50 text-teal-600" style={{ fontSize: "4px" }}>Python</span>
          </div>
          <div className="h-1 w-full bg-gray-200 rounded mb-0.5" />
          <div className="h-1 w-4/5 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}

export function TemplateStep({
  selectedTemplate,
  onSelectTemplate,
  onNext,
  onBack,
}: TemplateStepProps) {
  return (
    <div className="w-[calc(100%-2rem)] md:w-[calc(100%-4rem)] max-w-7xl mx-auto h-[calc(100vh-12rem)] min-h-[500px] flex flex-col justify-between animate-fade-in">
      {/* Heading */}
      <div className="mb-6 shrink-0">
        <h1 className="font-['Geist'] text-[32px] sm:text-[40px] lg:text-[48px] font-bold leading-[1.1] tracking-[-0.04em] text-white mb-2">
          Choose a Resume Layout
        </h1>
        <p className="font-['Geist'] text-[14px] sm:text-[16px] text-[#c4c7c8]">
          Select a design template for your tailored resume.
        </p>
      </div>

      {/* Grid — 4 columns: 2 selectable + 2 locked */}
      <div className="grid grid-cols-4 gap-6 flex-grow min-h-0 mb-6 max-h-[480px]">

        {/* ── Classic (selectable) ── */}
        <div
          id="template-classic"
          onClick={() => onSelectTemplate("default")}
          className={`border-2 flex flex-col h-full min-h-0 relative cursor-pointer transition-all
            ${selectedTemplate === "default"
              ? "border-white bg-[#1c1b1b]"
              : "border-[#444748] bg-[#1c1b1b] hover:border-white"
            }`}
        >
          {selectedTemplate === "default" && (
            <div className="absolute top-3 right-3 z-10 w-6 h-6 bg-white flex items-center justify-center">
              <span className="material-symbols-outlined text-[#141313] text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                check
              </span>
            </div>
          )}
          <div className="flex-grow bg-[#201f1f] flex items-center justify-center border-b border-[#444748] min-h-0">
            <DefaultPreview />
          </div>
          <div className="p-4 bg-[#141313] flex flex-col gap-2 shrink-0">
            <h3 className="font-['Geist'] text-[20px] font-semibold text-white">Classic</h3>
            <span className={`font-['JetBrains_Mono'] text-[11px] border px-2 py-1 w-fit uppercase tracking-widest
              ${selectedTemplate === "default" ? "border-white text-white" : "border-[#444748] text-[#8e9192]"}`}>
              {selectedTemplate === "default" ? "Selected · Free" : "Free"}
            </span>
          </div>
        </div>

        {/* ── Modern (selectable) ── */}
        <div
          id="template-modern"
          onClick={() => onSelectTemplate("modern")}
          className={`border-2 flex flex-col h-full min-h-0 relative cursor-pointer transition-all
            ${selectedTemplate === "modern"
              ? "border-white bg-[#1c1b1b]"
              : "border-[#444748] bg-[#1c1b1b] hover:border-white"
            }`}
        >
          {selectedTemplate === "modern" && (
            <div className="absolute top-3 right-3 z-10 w-6 h-6 bg-white flex items-center justify-center">
              <span className="material-symbols-outlined text-[#141313] text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                check
              </span>
            </div>
          )}
          {/* Light background for white resume preview */}
          <div className="flex-grow bg-[#e8e8e8] flex items-center justify-center border-b border-[#444748] min-h-0 overflow-hidden">
            <ModernPreview />
          </div>
          <div className="p-4 bg-[#141313] flex flex-col gap-2 shrink-0">
            <h3 className="font-['Geist'] text-[20px] font-semibold text-white">Modern</h3>
            <span className={`font-['JetBrains_Mono'] text-[11px] border px-2 py-1 w-fit uppercase tracking-widest
              ${selectedTemplate === "modern" ? "border-white text-white" : "border-[#444748] text-[#8e9192]"}`}>
              {selectedTemplate === "modern" ? "Selected · Free" : "Free"}
            </span>
          </div>
        </div>

        {/* ── Locked cards ── */}
        {["Creative Layout", "Minimalist Layout"].map((name) => (
          <div
            key={name}
            className="border border-[#444748] bg-[#1c1b1b] flex flex-col h-full min-h-0 relative opacity-50 cursor-not-allowed grayscale"
          >
            <div className="flex-grow bg-[#201f1f] flex items-center justify-center border-b border-[#444748] min-h-0">
              <LockedPreview />
            </div>
            <div className="p-4 bg-[#141313] flex flex-col gap-2 shrink-0">
              <h3 className="font-['Geist'] text-[20px] font-semibold text-[#c4c7c8]">{name}</h3>
              <span className="font-['JetBrains_Mono'] text-[11px] border border-[#444748] text-[#8e9192] px-2 py-1 w-fit uppercase tracking-widest">
                Coming Soon
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center border-t border-[#444748] pt-6 shrink-0">
        <button
          onClick={onBack}
          className="h-12 px-8 border border-white text-white font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-white hover:text-[#141313] transition-all"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Upload
        </button>
        <button
          onClick={onNext}
          className="h-12 px-8 bg-white text-[#141313] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-transparent hover:text-white hover:border hover:border-white transition-all"
        >
          Go Ahead
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
