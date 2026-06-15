"use client";

import React, { useState } from "react";
import { Link2, AlignLeft } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface JobInputProps {
  jobUrl: string;
  jobText: string;
  onUrlChange: (url: string) => void;
  onTextChange: (text: string) => void;
  activeTab: "url" | "text";
  onTabChange: (tab: "url" | "text") => void;
}

export function JobInput({
  jobUrl,
  jobText,
  onUrlChange,
  onTextChange,
  activeTab,
  onTabChange,
}: JobInputProps) {
  return (
    <div className="flex flex-col gap-4 w-full h-full">
      <Tabs
        value={activeTab}
        onValueChange={(v) => onTabChange(v as "url" | "text")}
        className="flex flex-col flex-1"
      >
        <TabsList className="w-full grid grid-cols-2 h-10">
          <TabsTrigger
            value="url"
            className="flex items-center gap-2 text-xs"
          >
            <Link2 className="w-3.5 h-3.5" />
            Paste Link
          </TabsTrigger>
          <TabsTrigger
            value="text"
            className="flex items-center gap-2 text-xs"
          >
            <AlignLeft className="w-3.5 h-3.5" />
            Paste Text
          </TabsTrigger>
        </TabsList>

        <TabsContent value="url" className="flex flex-col gap-3 mt-4 flex-1">
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Paste the job posting URL. We&apos;ll scrape the description automatically.
            </p>
            <div className="relative">
              <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              <Input
                id="job-url-input"
                type="url"
                placeholder="https://linkedin.com/jobs/view/..."
                value={jobUrl}
                onChange={(e) => onUrlChange(e.target.value)}
                className="pl-9 text-sm"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Note: Some job boards block automated access. If scraping fails, switch to{" "}
              <button
                type="button"
                onClick={() => onTabChange("text")}
                className="underline underline-offset-2 hover:text-foreground transition-colors"
              >
                Paste Text
              </button>
              .
            </p>
          </div>
        </TabsContent>

        <TabsContent value="text" className="flex flex-col flex-1 mt-4">
          <div className="space-y-2 flex flex-col flex-1">
            <p className="text-xs text-muted-foreground">
              Copy-paste the full job description below.
            </p>
            <textarea
              id="job-text-input"
              placeholder="Senior AI/ML Engineer&#10;&#10;Company: Acme Corp&#10;Location: Remote&#10;&#10;We are looking for..."
              value={jobText}
              onChange={(e) => onTextChange(e.target.value)}
              className={cn(
                "flex-1 min-h-[220px] w-full border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none font-mono"
              )}
            />
            <p className="text-xs text-muted-foreground">
              {jobText.length > 0
                ? `${jobText.length.toLocaleString()} characters`
                : "Minimum 100 characters recommended"}
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
