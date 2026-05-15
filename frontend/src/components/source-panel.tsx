"use client";

import Link from "next/link";
import { ArrowUpRight, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useChunkWithContext } from "@/hooks/use-chunks";
import type { SourceChunk } from "@/types/chat";

interface SourcePanelProps {
  source: SourceChunk | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SourcePanel({ source, open, onOpenChange }: SourcePanelProps) {
  const { data, isLoading } = useChunkWithContext(source?.chunk_id ?? null);
  const scorePct = source?.score != null ? Math.round(source.score * 100) : null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/20">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <SheetTitle className="truncate text-base font-semibold">
                {source?.filename ?? "Source"}
              </SheetTitle>
              {source && (
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Page {source.page_number}
                </p>
              )}
            </div>
            {scorePct != null && <ScoreBadge value={scorePct} />}
          </div>
        </SheetHeader>

        <div className="mt-6 space-y-3">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {data && (
            <>
              {data.previous_chunk && (
                <ContextChunk
                  label="Before"
                  content={data.previous_chunk.content}
                  variant="muted"
                />
              )}

              <ContextChunk
                label="Matched passage"
                content={data.chunk.content}
                variant="primary"
              />

              {data.next_chunk && (
                <ContextChunk
                  label="After"
                  content={data.next_chunk.content}
                  variant="muted"
                />
              )}

              <Button variant="outline" className="mt-4 w-full" asChild>
                <Link href={`/documents/${data.chunk.document_id}`}>
                  View full document
                  <ArrowUpRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

/** Circular relevance indicator, 0–100. */
function ScoreBadge({ value }: { value: number }) {
  const size = 44;
  const stroke = 3.5;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  // Hue mapping: cyan for high relevance, fading to muted at low
  const color =
    value >= 75 ? "var(--primary)" : value >= 50 ? "rgb(34 211 238)" : "rgb(148 163 184)";

  return (
    <div
      className="relative shrink-0"
      role="img"
      aria-label={`Relevance ${value} percent`}
      title={`Relevance: ${value}%`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-muted/40"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-semibold tabular-nums">
        {value}
      </span>
    </div>
  );
}

function ContextChunk({
  label,
  content,
  variant,
}: {
  label: string;
  content: string;
  variant: "primary" | "muted";
}) {
  const isPrimary = variant === "primary";
  return (
    <div
      className={[
        "relative rounded-lg p-4 transition-colors",
        isPrimary
          ? "border border-primary/30 bg-primary/[0.06] shadow-[0_0_24px_-12px_rgba(6,182,212,0.4)]"
          : "border border-border/60 bg-muted/30",
      ].join(" ")}
    >
      {isPrimary && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent"
        />
      )}
      <p
        className={[
          "mb-2 text-[10px] font-semibold uppercase tracking-wider",
          isPrimary ? "text-primary" : "text-muted-foreground",
        ].join(" ")}
      >
        {label}
      </p>
      <p
        className={[
          "text-sm leading-relaxed",
          isPrimary ? "text-foreground" : "text-muted-foreground",
        ].join(" ")}
      >
        {content.replace(/\n/g, " ")}
      </p>
    </div>
  );
}
