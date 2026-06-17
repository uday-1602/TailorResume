"use client";

import React from "react";

interface TemplateStepProps {
  selectedTemplate: string;
  onSelectTemplate: (t: string) => void;
  onNext: () => void;
  onBack: () => void;
}

const LOCKED_CARDS = ["Executive Layout", "Creative Layout", "Minimalist Layout"];

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

function LockedPreview({ name }: { name: string }) {
  return (
    <div className="w-4/5 h-4/5 border border-[#444748] p-4 bg-[#141313] flex flex-col items-center justify-center gap-3">
      <span className="material-symbols-outlined text-[#8e9192] text-5xl">lock</span>
      <div className="w-full h-2 bg-[#353434]/20" />
      <div className="w-full h-2 bg-[#353434]/20" />
      <div className="w-3/4 h-2 bg-[#353434]/20" />
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

      {/* Grid */}
      <div className="grid grid-cols-4 gap-6 flex-grow min-h-0 mb-6 max-h-[480px]">
        {/* Default — selectable */}
        <div
          onClick={() => onSelectTemplate("default")}
          className={`border-2 flex flex-col h-full min-h-0 relative cursor-pointer transition-all
            ${selectedTemplate === "default"
              ? "border-white bg-[#1c1b1b]"
              : "border-[#444748] bg-[#1c1b1b] hover:border-white"
            }`}
        >
          {/* Checkmark badge */}
          {selectedTemplate === "default" && (
            <div className="absolute top-3 right-3 z-10 w-6 h-6 bg-white flex items-center justify-center">
              <span className="material-symbols-outlined text-[#141313] text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                check
              </span>
            </div>
          )}
          {/* Preview area */}
          <div className="flex-grow bg-[#201f1f] flex items-center justify-center border-b border-[#444748] min-h-0">
            <DefaultPreview />
          </div>
          {/* Info */}
          <div className="p-4 bg-[#141313] flex flex-col gap-2 shrink-0">
            <div className="flex justify-between items-start">
              <h3 className="font-['Geist'] text-[20px] font-semibold text-white">
                Default Layout
              </h3>
            </div>
            <span className="font-['JetBrains_Mono'] text-[11px] border border-white text-white px-2 py-1 w-fit uppercase tracking-widest">
              Selected · Free
            </span>
          </div>
        </div>

        {/* Locked cards */}
        {LOCKED_CARDS.map((name) => (
          <div
            key={name}
            className="border border-[#444748] bg-[#1c1b1b] flex flex-col h-full min-h-0 relative opacity-50 cursor-not-allowed grayscale"
          >
            <div className="flex-grow bg-[#201f1f] flex items-center justify-center border-b border-[#444748] min-h-0">
              <LockedPreview name={name} />
            </div>
            <div className="p-4 bg-[#141313] flex flex-col gap-2 shrink-0">
              <h3 className="font-['Geist'] text-[20px] font-semibold text-[#c4c7c8]">
                {name}
              </h3>
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
