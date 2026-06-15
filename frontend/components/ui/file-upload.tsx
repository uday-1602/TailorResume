"use client";

import React, { useCallback, useState } from "react";
import { Upload, FileText, X, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface FileUploadProps {
  onFileSelect: (file: File | null) => void;
  file: File | null;
}

export function FileUpload({ onFileSelect, file }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile && isPdfOrDocx(droppedFile)) {
        onFileSelect(droppedFile);
      }
    },
    [onFileSelect]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected && isPdfOrDocx(selected)) {
      onFileSelect(selected);
    }
  };

  const isPdfOrDocx = (f: File) =>
    f.type === "application/pdf" ||
    f.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex flex-col gap-4 w-full h-full">
      {!file ? (
        <label
          htmlFor="resume-upload"
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            "flex flex-col items-center justify-center gap-4 border-2 border-dashed p-10 cursor-pointer transition-all duration-200 flex-1 min-h-[280px]",
            isDragging
              ? "border-foreground bg-muted"
              : "border-input hover:border-muted-foreground hover:bg-muted/50"
          )}
        >
          <div
            className={cn(
              "flex items-center justify-center w-14 h-14 border transition-all duration-200",
              isDragging ? "border-foreground bg-foreground/5" : "border-input"
            )}
          >
            <Upload
              className={cn(
                "w-6 h-6 transition-colors",
                isDragging ? "text-foreground" : "text-muted-foreground"
              )}
            />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-foreground">
              Drag &amp; drop your resume here
            </p>
            <p className="text-xs text-muted-foreground">
              or{" "}
              <span className="underline underline-offset-2 text-foreground">
                browse files
              </span>
            </p>
          </div>
          <p className="text-xs text-muted-foreground">PDF or DOCX · Max 10 MB</p>
          <input
            id="resume-upload"
            type="file"
            accept=".pdf,.docx"
            className="sr-only"
            onChange={handleFileInput}
          />
        </label>
      ) : (
        <div className="flex flex-col gap-3 flex-1">
          {/* File preview card */}
          <div className="flex items-center gap-3 border border-input bg-muted p-4 relative">
            <div className="flex items-center justify-center w-10 h-10 bg-background border border-input shrink-0">
              <FileText className="w-5 h-5 text-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {file.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatSize(file.size)}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-foreground" />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onFileSelect(null)}
                aria-label="Remove file"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
          {/* Replace prompt */}
          <label
            htmlFor="resume-upload-replace"
            className="text-xs text-muted-foreground underline underline-offset-2 cursor-pointer hover:text-foreground transition-colors"
          >
            Replace file
            <input
              id="resume-upload-replace"
              type="file"
              accept=".pdf,.docx"
              className="sr-only"
              onChange={handleFileInput}
            />
          </label>
        </div>
      )}
    </div>
  );
}
