"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { Toaster, toast } from "sonner";
import { UploadStep } from "@/components/steps/UploadStep";
import { TemplateStep } from "@/components/steps/TemplateStep";
import { ProcessingStep, PipelineNode } from "@/components/steps/ProcessingStep";
import { ResultStep } from "@/components/steps/ResultStep";
import { ChatbotPopup } from "@/components/ChatbotPopup";

type Step = "upload" | "template" | "processing" | "result";

const INITIAL_NODES: PipelineNode[] = [
  {
    id: "profile_analyzer",
    label: "Profile Analyzer",
    description: "Extracting skills, experience, and education from your resume",
    status: "pending",
  },
  {
    id: "job_scraper",
    label: "Job Scraper",
    description: "Parsing and structuring the job requirements",
    status: "pending",
  },
  {
    id: "gap_analyzer",
    label: "Gap Analyzer",
    description: "Computing alignment score and identifying missing keywords",
    status: "pending",
  },
  {
    id: "interviewer",
    label: "Generating Questions",
    description: "Building targeted questions to personalize your resume",
    status: "pending",
  },
  {
    id: "resume_rewriter",
    label: "Resume Rewriter",
    description: "Generating ATS-optimized LaTeX and compiling to PDF",
    status: "pending",
  },
];

const STEPS: Step[] = ["upload", "template", "processing", "result"];
const STEP_LABELS: Record<Step, string> = {
  upload: "01 Upload",
  template: "02 Template",
  processing: "03 Processing",
  result: "04 Result",
};

export default function Home() {
  const [step, setStep] = useState<Step>("upload");

  // Upload state
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState("");
  const [jobText, setJobText] = useState("");
  const [jobTab, setJobTab] = useState<"url" | "text">("text");

  // Template state
  const [selectedTemplate, setSelectedTemplate] = useState("default");

  // Pipeline state
  const [nodes, setNodes] = useState<PipelineNode[]>(INITIAL_NODES);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);

  // Chatbot state
  const [showChatbot, setShowChatbot] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState<string[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);

  const updateNode = useCallback(
    (nodeId: string, status: PipelineNode["status"]) => {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, status } : n))
      );
    },
    []
  );

  const connectSSE = useCallback(
    (id: string) => {
      const es = new EventSource(`http://127.0.0.1:8000/api/status/${id}`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case "node_start":
              updateNode(data.node, "running");
              setStatusMessage(`Running: ${data.label ?? data.node}...`);
              break;
            case "node_done":
              updateNode(data.node, "done");
              break;
            case "node_error":
              updateNode(data.node, "error");
              setStatusMessage(`Error in ${data.node}: ${data.message}`);
              toast.error(`Pipeline error in ${data.node}`, {
                description: data.message,
              });
              break;
            case "interview_questions":
              setInterviewQuestions(data.questions ?? []);
              setShowChatbot(true);
              break;
            case "complete":
              es.close();
              setStep("result");
              toast.success("Resume ready!", {
                description: "Your tailored resume has been generated.",
              });
              break;
            case "status":
              setStatusMessage(data.message ?? "");
              break;
          }
        } catch {
          // Non-JSON keepalive — ignore
        }
      };

      es.onerror = () => es.close();
    },
    [updateNode]
  );

  const handleChatbotComplete = useCallback(
    async (answers: Record<string, string>) => {
      setShowChatbot(false);
      if (!jobId) return;

      updateNode("interviewer", "done");
      updateNode("resume_rewriter", "running");
      setStatusMessage("Rewriting your resume...");

      try {
        await fetch(`http://127.0.0.1:8000/api/answers/${jobId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers }),
        });
      } catch {
        toast.error("Failed to submit answers. Please try again.");
      }
    },
    [jobId, updateNode]
  );

  const startPipeline = useCallback(async () => {
    if (!resumeFile) return;

    setStep("processing");
    setNodes(INITIAL_NODES);
    setStatusMessage("Uploading files...");

    const formData = new FormData();
    formData.append("resume", resumeFile);
    if (jobTab === "url" && jobUrl) {
      formData.append("job_url", jobUrl);
    } else {
      formData.append("job_text", jobText);
    }
    formData.append("template", selectedTemplate);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/run", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Failed to start pipeline");
      }

      const data = await res.json();
      setJobId(data.job_id);
      setStatusMessage("Pipeline started — analyzing your documents...");
      connectSSE(data.job_id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      toast.error("Failed to start pipeline", { description: message });
      setStep("template");
    }
  }, [resumeFile, jobTab, jobUrl, jobText, selectedTemplate, connectSSE]);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const currentStepIdx = STEPS.indexOf(step);

  return (
    <div className="min-h-screen bg-[#141313] flex flex-col">
      <Toaster position="top-right" richColors theme="dark" />

      {/* ── Header ── */}
      <header className="w-full border-b border-[#444748] bg-[#141313] flex justify-between items-center px-10 h-16 shrink-0 z-50">
        {/* Logo + wordmark */}
        <div className="flex items-center gap-3">
          {/* Square logo SVG */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="6" height="6" fill="white"/>
            <rect x="14" y="14" width="6" height="6" fill="white"/>
            <rect x="14" y="4" width="2" height="2" fill="white"/>
            <rect x="8" y="18" width="2" height="2" fill="white"/>
          </svg>
          <span className="font-['Geist'] text-[20px] font-bold text-white uppercase tracking-tight">
            TailorResume
          </span>
        </div>

        {/* Step indicators */}
        <nav className="hidden md:flex items-center gap-6">
          {STEPS.map((s, idx) => {
            const isActive = s === step;
            const isPast = idx < currentStepIdx;
            return (
              <span
                key={s}
                className={`font-['JetBrains_Mono'] text-[11px] font-bold uppercase tracking-widest transition-colors
                  ${isActive ? "text-white border-b-2 border-white pb-1" : ""}
                  ${isPast ? "text-[#8e9192] line-through" : ""}
                  ${!isActive && !isPast ? "text-[#c4c7c8]" : ""}
                `}
              >
                {STEP_LABELS[s]}
              </span>
            );
          })}
        </nav>

        {/* Account icon */}
        <div className="w-10 h-10 border border-[#444748] flex items-center justify-center hover:border-white transition-colors cursor-pointer">
          <span className="material-symbols-outlined text-white">account_circle</span>
        </div>
      </header>

      {/* ── Main ── */}
      <main
        className={`flex-grow flex items-center justify-center
          ${step === "upload" ? "p-0" : "p-10"}
        `}
      >
        <AnimatePresence mode="wait">
          {step === "upload" && (
            <div key="upload" className="w-full h-full flex items-center justify-center p-10">
              <UploadStep
                resumeFile={resumeFile}
                jobUrl={jobUrl}
                jobText={jobText}
                jobTab={jobTab}
                onResumeChange={setResumeFile}
                onUrlChange={setJobUrl}
                onTextChange={setJobText}
                onTabChange={setJobTab}
                onNext={() => setStep("template")}
              />
            </div>
          )}

          {step === "template" && (
            <div key="template" className="w-full">
              <TemplateStep
                selectedTemplate={selectedTemplate}
                onSelectTemplate={setSelectedTemplate}
                onNext={startPipeline}
                onBack={() => setStep("upload")}
              />
            </div>
          )}

          {step === "processing" && (
            <div key="processing" className="w-full flex items-center justify-center relative overflow-hidden">
              {/* Background dot grid */}
              <div
                className="absolute inset-0 pointer-events-none opacity-10"
                style={{
                  backgroundImage: "radial-gradient(#353434 1px, transparent 1px)",
                  backgroundSize: "24px 24px",
                }}
              />
              <ProcessingStep nodes={nodes} statusMessage={statusMessage} />
            </div>
          )}

          {step === "result" && (
            <div key="result" className="w-full">
              <ResultStep jobId={jobId} onReIterate={() => {}} />
            </div>
          )}
        </AnimatePresence>
      </main>

      {/* ── Footer ── */}
      <footer className="w-full border-t border-[#444748] bg-[#141313] flex justify-between items-center px-10 py-4 shrink-0">
        <span className="font-['JetBrains_Mono'] text-[12px] text-white font-bold uppercase">
          TailorResume
        </span>
        <span className="font-['JetBrains_Mono'] text-[12px] text-[#c4c7c8]">
          Powered by LangGraph · Groq · LaTeX Online
        </span>
        <span className="font-['JetBrains_Mono'] text-[12px] text-[#8e9192]">
          TailorResume © 2026
        </span>
      </footer>

      {/* ── Chatbot overlay ── */}
      <AnimatePresence>
        {showChatbot && (
          <ChatbotPopup
            questions={interviewQuestions}
            onComplete={handleChatbotComplete}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
