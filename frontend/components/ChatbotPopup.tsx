"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";

interface ChatbotPopupProps {
  questions: string[];
  onComplete: (answers: Record<string, string>) => void;
}

interface Message {
  role: "bot" | "user";
  text: string;
}

export function ChatbotPopup({ questions, onComplete }: ChatbotPopupProps) {
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isBotTyping, setIsBotTyping] = useState(true);
  const [isWaitingForElaboration, setIsWaitingForElaboration] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom
  const scrollDown = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Add first question with typing delay
  useEffect(() => {
    if (questions.length === 0) return;
    const timer = setTimeout(() => {
      setMessages([{ role: "bot", text: questions[0] }]);
      setIsBotTyping(false);
    }, 900);
    return () => clearTimeout(timer);
  }, [questions]);

  // Keep input focused whenever bot stops typing and input gets enabled
  useEffect(() => {
    if (!isBotTyping) {
      // Small timeout to guarantee DOM is updated and input is fully enabled
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isBotTyping]);

  useEffect(() => {
    scrollDown();
  }, [messages, isBotTyping, scrollDown]);

  const isProjectRelated = (text: string): boolean => {
    const keywords = ["project", "developed", "built", "implemented", "designed", "created", "worked on", "system", "app", "application", "platform", "tool", "dashboard", "database", "pipeline"];
    const lower = text.toLowerCase();
    return keywords.some(kw => lower.includes(kw));
  };

  const handleSend = useCallback(() => {
    const val = inputValue.trim();
    if (!val || isBotTyping) return;

    setMessages((prev) => [...prev, { role: "user", text: val }]);
    setInputValue("");

    const isProject = isProjectRelated(val);

    if (isProject && !isWaitingForElaboration) {
      setIsBotTyping(true);
      setLastUserMessage(val);
      setIsWaitingForElaboration(true);

      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: "That sounds like a great project! Could you please elaborate on it? (Tell me about the core technologies you used, your specific role, and any key achievements or metrics)",
          },
        ]);
        setIsBotTyping(false);
      }, 1000);
      return;
    }

    let finalAnswer = val === "skip" ? "" : val;
    if (isWaitingForElaboration) {
      finalAnswer = `${lastUserMessage} [Elaboration]: ${val}`;
      setIsWaitingForElaboration(false);
      setLastUserMessage("");
    }

    const newAnswers = { ...answers, [questions[currentQ]]: finalAnswer };
    setAnswers(newAnswers);

    const nextQ = currentQ + 1;
    if (nextQ < questions.length) {
      setIsBotTyping(true);
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          { role: "bot", text: questions[nextQ] },
        ]);
        setIsBotTyping(false);
        setCurrentQ(nextQ);
      }, 1200);
    } else {
      // All answered
      setIsBotTyping(true);
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: "Thank you! Resuming the pipeline to tailor your resume...",
          },
        ]);
        setTimeout(() => onComplete(newAnswers), 1500);
      }, 800);
    }
  }, [inputValue, isBotTyping, answers, currentQ, questions, onComplete, isWaitingForElaboration, lastUserMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSend();
  };

  const progress = questions.length > 0 ? ((currentQ) / questions.length) * 100 : 0;

  return (
    /* Dark overlay */
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ background: "rgba(20,19,19,0.85)", backdropFilter: "blur(8px)" }}
    >
      {/* Modal */}
      <div
        className="w-full max-w-2xl bg-[#0e0e0e] border border-white flex flex-col animate-fade-in"
        style={{ boxShadow: "0 0 60px rgba(255,255,255,0.06)" }}
      >
        {/* Header */}
        <div className="p-6 border-b border-[#444748] flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white flex items-center justify-center">
                <span
                  className="material-symbols-outlined text-[#141313] text-[20px]"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  smart_toy
                </span>
              </div>
              <span className="font-['Geist'] text-[20px] font-semibold text-white">
                Resume Assistant
              </span>
            </div>
            <span className="font-['JetBrains_Mono'] text-[11px] text-[#c4c7c8] uppercase tracking-widest">
              Question {Math.min(currentQ + 1, questions.length)} of {questions.length}
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full h-[2px] bg-[#353434] overflow-hidden">
            <div
              className="h-full bg-white transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="flex-grow overflow-y-auto p-6 flex flex-col gap-6 h-[380px]">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`w-full flex items-start gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 shrink-0 flex items-center justify-center
                  ${msg.role === "bot" ? "bg-[#353434]" : "bg-white"}`}
              >
                <span
                  className={`material-symbols-outlined text-[16px]
                    ${msg.role === "bot" ? "text-white" : "text-[#141313]"}`}
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  {msg.role === "bot" ? "smart_toy" : "person"}
                </span>
              </div>
              {/* Bubble */}
              <div
                className={`max-w-[78%] p-3 font-['Geist'] text-[14px] leading-relaxed
                  ${msg.role === "bot"
                    ? "bg-[#201f1f] border border-[#444748] text-[#e5e2e1]"
                    : "bg-white text-[#141313] font-medium"
                  }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {/* Bot typing indicator */}
          {isBotTyping && (
            <div className="w-full flex items-start gap-3">
              <div className="w-7 h-7 shrink-0 bg-[#353434] flex items-center justify-center">
                <span
                  className="material-symbols-outlined text-white text-[16px]"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  smart_toy
                </span>
              </div>
              <div className="bg-[#201f1f] border border-[#444748] p-3 px-4 flex gap-1 items-center">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-[#444748] p-4 flex flex-col gap-2">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your response or 'skip' to continue..."
              disabled={isBotTyping}
              className="flex-grow bg-[#141313] border border-[#444748] px-4 py-3 font-['JetBrains_Mono'] text-[12px] text-white placeholder:text-[#8e9192] focus:outline-none focus:border-white transition-colors disabled:opacity-40"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isBotTyping}
              className="px-6 py-3 bg-white text-[#141313] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-transparent hover:text-white hover:border hover:border-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Send
              <span className="material-symbols-outlined text-[16px]">send</span>
            </button>
          </div>
          <p className="font-['JetBrains_Mono'] text-[10px] text-[#8e9192] uppercase tracking-widest">
            Press Enter to send · Type 'skip' to skip a question
          </p>
        </div>
      </div>
    </div>
  );
}
