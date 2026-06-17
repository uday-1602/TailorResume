"use client";

import React, { useState, useEffect, useRef } from "react";

// Declare window typing for pdfjsLib
declare global {
  interface Window {
    pdfjsLib?: any;
  }
}

interface ResultStepProps {
  jobId: string | null;
  onReIterate: () => void;
}

function PdfCanvasViewer({ url, zoom }: { url: string; zoom: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let renderTask: any = null;
    let pageObj: any = null;

    const renderPage = async (page: any) => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (!canvas || !container || !page) return;

      const context = canvas.getContext("2d");
      if (!context) return;

      // Calculate scale to fit container width/height
      const containerWidth = container.clientWidth - 32; // padding
      const containerHeight = container.clientHeight - 32; // padding
      
      const unscaledViewport = page.getViewport({ scale: 1.0 });
      const scaleX = containerWidth / unscaledViewport.width;
      const scaleY = containerHeight / unscaledViewport.height;
      const fitScale = Math.min(scaleX, scaleY);
      const scale = fitScale * zoom; // Apply zoom factor

      const viewport = page.getViewport({ scale });

      const devicePixelRatio = window.devicePixelRatio || 1;
      canvas.width = viewport.width * devicePixelRatio;
      canvas.height = viewport.height * devicePixelRatio;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      context.scale(devicePixelRatio, devicePixelRatio);

      // Cancel previous render task if any
      if (renderTask) {
        renderTask.cancel();
      }

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };
      
      renderTask = page.render(renderContext);
      try {
        await renderTask.promise;
        if (active) {
          setLoading(false);
          // Dynamically adjust centering style on each axis independently based on whether it overflows
          if (viewport.width > containerWidth) {
            container.style.justifyContent = "flex-start";
          } else {
            container.style.justifyContent = "center";
          }

          if (viewport.height > containerHeight) {
            container.style.alignItems = "flex-start";
          } else {
            container.style.alignItems = "center";
          }
        }
      } catch (err: any) {
        if (err.name !== "RenderingCancelledException") {
          console.error("Render error:", err);
        }
      }
    };

    const loadAndRender = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let checkCount = 0;
        while (!window.pdfjsLib) {
          if (checkCount > 50) {
            throw new Error("PDF renderer failed to load.");
          }
          await new Promise((resolve) => setTimeout(resolve, 100));
          checkCount++;
        }

        const pdfjsLib = window.pdfjsLib;
        pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js";

        const loadingTask = pdfjsLib.getDocument(url);
        const pdf = await loadingTask.promise;
        
        if (!active) return;
        
        pageObj = await pdf.getPage(1);
        if (!active) return;

        await renderPage(pageObj);

        // Listen to window resize to trigger re-rendering
        const handleResize = () => {
          if (pageObj) {
            renderPage(pageObj);
          }
        };

        window.addEventListener("resize", handleResize);
        return () => {
          window.removeEventListener("resize", handleResize);
        };
      } catch (err: any) {
        console.error("PDF loading error:", err);
        if (active) {
          setError(err.message || "Failed to render PDF");
          setLoading(false);
        }
      }
    };

    loadAndRender();

    return () => {
      active = false;
      if (renderTask) {
        renderTask.cancel();
      }
    };
  }, [url, zoom]);

  return (
    <div
      ref={containerRef}
      className="flex-grow w-full h-full flex overflow-auto p-4 bg-[#141313] min-h-0 justify-center items-center"
    >
      {loading && (
        <div className="m-auto flex flex-col items-center justify-center text-[#8e9192]">
          <span className="material-symbols-outlined text-[36px] animate-spin-slow mb-2">sync</span>
          <span className="font-['JetBrains_Mono'] text-[11px] uppercase tracking-widest">Rendering preview...</span>
        </div>
      )}
      {error && (
        <div className="m-auto flex flex-col items-center justify-center text-[#ff5555] p-6 text-center">
          <span className="material-symbols-outlined text-[36px] mb-2">error</span>
          <span className="font-['JetBrains_Mono'] text-[12px] uppercase">{error}</span>
        </div>
      )}
      <canvas
        ref={canvasRef}
        className={`m-auto shadow-2xl border border-[#444748] bg-white transition-opacity duration-300 ${
          loading ? "hidden" : "block"
        }`}
      />
    </div>
  );
}

export function ResultStep({ jobId, onReIterate }: ResultStepProps) {
  const [downloading, setDownloading] = useState(false);
  const [pdfjsLoaded, setPdfjsLoaded] = useState(false);
  const [zoom, setZoom] = useState(1.0);

  const downloadUrl = jobId
    ? `http://127.0.0.1:8000/api/download/${jobId}`
    : null;

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (window.pdfjsLib) {
        setPdfjsLoaded(true);
      } else {
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js";
        script.async = true;
        script.onload = () => setPdfjsLoaded(true);
        document.head.appendChild(script);
      }
    }
  }, []);

  const handleDownload = () => {
    if (!downloadUrl) return;
    setDownloading(true);
    const a = document.createElement("a");
    a.href = `${downloadUrl}?download=true`;
    a.download = "tailored_resume.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => setDownloading(false), 1500);
  };

  return (
    <div className="w-full max-w-7xl mx-auto h-[calc(100vh-12rem)] min-h-[500px] animate-fade-in">
      {/* Split: PDF preview + actions */}
      <div className="grid grid-cols-[1fr_320px] gap-6 h-full min-h-0">
        {/* PDF Preview */}
        <div className="border border-[#444748] bg-[#0e0e0e] flex flex-col overflow-hidden h-full min-h-0">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#444748] bg-[#1c1b1b] shrink-0">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-white text-[18px]">picture_as_pdf</span>
              <span className="font-['JetBrains_Mono'] text-[12px] text-white">
                tailored_resume.pdf
              </span>
            </div>

            {/* Zoom Controls */}
            {downloadUrl && pdfjsLoaded && (
              <div className="flex items-center gap-1.5 bg-[#141313] border border-[#444748] px-2 py-0.5">
                <button
                  onClick={() => setZoom(1.0)}
                  className={`px-2 py-0.5 font-['JetBrains_Mono'] text-[11px] transition-colors cursor-pointer ${
                    zoom === 1.0 ? "text-white bg-[#353434] font-bold" : "text-[#8e9192] hover:text-white"
                  }`}
                >
                  100%
                </button>
                <button
                  onClick={() => setZoom(2.0)}
                  className={`px-2 py-0.5 font-['JetBrains_Mono'] text-[11px] transition-colors cursor-pointer ${
                    zoom === 2.0 ? "text-white bg-[#353434] font-bold" : "text-[#8e9192] hover:text-white"
                  }`}
                >
                  200%
                </button>
                <button
                  onClick={() => setZoom(3.0)}
                  className={`px-2 py-0.5 font-['JetBrains_Mono'] text-[11px] transition-colors cursor-pointer ${
                    zoom === 3.0 ? "text-white bg-[#353434] font-bold" : "text-[#8e9192] hover:text-white"
                  }`}
                >
                  300%
                </button>
              </div>
            )}

            <span className="font-['JetBrains_Mono'] text-[11px] border border-[#444748] text-[#8e9192] px-2 py-0.5 uppercase">
              PDF
            </span>
          </div>

          {/* PDF rendering Canvas */}
          {downloadUrl && pdfjsLoaded ? (
            <PdfCanvasViewer url={downloadUrl} zoom={zoom} />
          ) : downloadUrl ? (
            <div className="flex-grow flex items-center justify-center text-[#8e9192]">
              <div className="text-center">
                <span className="material-symbols-outlined text-[36px] animate-spin-slow mb-2 block">sync</span>
                <p className="font-['JetBrains_Mono'] text-[11px] uppercase tracking-widest">Loading renderer...</p>
              </div>
            </div>
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
        <div className="flex flex-col gap-4 h-full overflow-y-auto pr-1 shrink-0">
          {/* Status & Download */}
          <div className="flex flex-col gap-2 shrink-0">
            <span className="font-['JetBrains_Mono'] text-[11px] text-[#c4c7c8] uppercase tracking-widest select-none mb-1">
              ATS-optimised · LaTeX compiled · PDF Ready
            </span>
            <button
              id="download-pdf-btn"
              onClick={handleDownload}
              disabled={!downloadUrl || downloading}
              className="w-full h-12 bg-white text-[#141313] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-transparent hover:text-white hover:border hover:border-white transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 cursor-pointer"
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

          {/* Re-iterate Button */}
          <div className="relative group shrink-0 opacity-50">
            <button
              disabled
              className="w-full h-12 border border-[#444748] bg-[#1c1b1b] text-[#8e9192] font-['JetBrains_Mono'] text-[12px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 cursor-not-allowed"
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

          {/* Stats */}
          <div className="border border-[#444748] bg-[#0e0e0e] p-4 flex flex-col gap-3 shrink-0">
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
