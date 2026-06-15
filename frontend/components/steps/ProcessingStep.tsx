"use client";

import React from "react";

export type NodeStatus = "pending" | "running" | "done" | "error";

export interface PipelineNode {
  id: string;
  label: string;
  description: string;
  status: NodeStatus;
}

interface ProcessingStepProps {
  nodes: PipelineNode[];
  statusMessage: string;
}

const NODE_LABELS: Record<string, string> = {
  profile_analyzer: "01. Profile Analyzer",
  job_scraper:      "02. Job Scraper",
  gap_analyzer:     "03. Gap Analyzer",
  interviewer:      "04. Interviewer Chat",
  resume_rewriter:  "05. Resume Rewriter & Compiler",
};

function NodeIcon({ status }: { status: NodeStatus }) {
  if (status === "done") {
    return (
      <span
        className="material-symbols-outlined text-green-400 text-[22px]"
        style={{ fontVariationSettings: "'FILL' 1" }}
      >
        check_circle
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="material-symbols-outlined text-white text-[22px] animate-spin-slow">
        sync
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="material-symbols-outlined text-red-400 text-[22px]">
        error
      </span>
    );
  }
  return (
    <span className="material-symbols-outlined text-[#8e9192] text-[22px]">
      radio_button_unchecked
    </span>
  );
}

export function ProcessingStep({ nodes, statusMessage }: ProcessingStepProps) {
  const doneCount = nodes.filter((n) => n.status === "done").length;
  const progress = Math.round((doneCount / nodes.length) * 100);

  return (
    <div className="w-full max-w-2xl mx-auto animate-fade-in">
      {/* Spinner + title */}
      <div className="text-center mb-10 relative">
        <div className="inline-block mb-4 relative">
          <span className="material-symbols-outlined text-white text-[56px] animate-spin-slow" style={{ fontVariationSettings: "'wght' 200" }}>
            progress_activity
          </span>
          {/* Scanline */}
          <div className="scanline" />
        </div>
        <h1 className="font-['Geist'] text-[32px] font-semibold text-white uppercase tracking-tight mb-2">
          Tailoring Your Resume...
        </h1>
        <p className="font-['JetBrains_Mono'] text-[12px] text-[#8e9192] uppercase tracking-widest">
          Neural Alignment Engine · LangGraph Pipeline
        </p>
      </div>

      {/* Progress bar */}
      <div className="w-full h-[2px] bg-[#353434] mb-8 overflow-hidden">
        <div
          className="h-full bg-white transition-all duration-700"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Pipeline nodes */}
      <div className="border border-[#444748] bg-[#1c1b1b] divide-y divide-[#444748] mb-6">
        {nodes.map((node) => (
          <div
            key={node.id}
            className={`flex items-center justify-between p-4 transition-colors
              ${node.status === "running"
                ? "bg-white/5 border-l-2 border-l-white"
                : "hover:bg-[#201f1f]"
              }`}
          >
            <div className="flex items-center gap-4">
              <NodeIcon status={node.status} />
              <span
                className={`font-['JetBrains_Mono'] text-[12px] tracking-wide
                  ${node.status === "running" ? "text-white font-bold" : ""}
                  ${node.status === "done"    ? "text-[#c4c7c8]" : ""}
                  ${node.status === "pending" ? "text-[#8e9192]" : ""}
                  ${node.status === "error"   ? "text-red-400"   : ""}
                `}
              >
                {NODE_LABELS[node.id] ?? node.label}
              </span>
            </div>
            <span
              className={`font-['JetBrains_Mono'] text-[11px] uppercase tracking-widest
                ${node.status === "running" ? "text-white animate-pulse" : ""}
                ${node.status === "done"    ? "text-green-400" : ""}
                ${node.status === "pending" ? "text-[#8e9192]" : ""}
                ${node.status === "error"   ? "text-red-400"   : ""}
              `}
            >
              {node.status === "running" ? "Running..." : node.status}
            </span>
          </div>
        ))}
      </div>

      {/* Status log */}
      <div className="border border-[#444748] bg-[#0e0e0e] p-4">
        <div className="flex items-start gap-3">
          <span className="font-['JetBrains_Mono'] text-[12px] text-white shrink-0">[LOG]:</span>
          <p className="font-['JetBrains_Mono'] text-[12px] text-[#c4c7c8]">
            {statusMessage || "Initializing pipeline..."}
          </p>
        </div>
      </div>

      {/* Stats bento */}
      <div className="grid grid-cols-2 gap-[1px] border border-[#444748] mt-4 bg-[#444748]">
        <div className="bg-[#141313] p-4 flex flex-col gap-3">
          <span className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase">Processing Load</span>
          <div className="w-full h-[3px] bg-[#353434] overflow-hidden">
            <div
              className="h-full bg-white transition-all duration-1000"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between font-['JetBrains_Mono'] text-[10px] text-[#8e9192]">
            <span>{doneCount}/{nodes.length} nodes</span>
            <span>{progress}% complete</span>
          </div>
        </div>
        <div className="bg-[#141313] p-4 flex items-center justify-center gap-6">
          <div className="flex flex-col items-center">
            <span className="font-['JetBrains_Mono'] text-white text-[20px] font-bold">{doneCount}</span>
            <span className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase">Done</span>
          </div>
          <div className="w-px h-8 bg-[#444748]" />
          <div className="flex flex-col items-center">
            <span className="font-['JetBrains_Mono'] text-white text-[20px] font-bold">
              {nodes.filter((n) => n.status === "pending").length}
            </span>
            <span className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase">Pending</span>
          </div>
        </div>
      </div>
    </div>
  );
}
