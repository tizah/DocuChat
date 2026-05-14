"use client";

import Link from "next/link";
import { ExternalLink, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useChunkWithContext } from "@/hooks/use-chunks";
import type { SourceChunk } from "@/types/chat";

interface SourcePanelProps {
  source: SourceChunk | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SourcePanel({ source, open, onOpenChange }: SourcePanelProps) {
  const { data, isLoading } = useChunkWithContext(source?.chunk_id ?? null);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {source?.filename ?? "Source"}
          </SheetTitle>
        </SheetHeader>

        {source && (
          <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
            <span>Page {source.page_number}</span>
            {source.score != null && (
              <span>Relevance: {Math.round(source.score * 100)}%</span>
            )}
          </div>
        )}

        <div className="mt-6 space-y-4">
          {isLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {data && (
            <>
              {data.previous_chunk && (
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Previous context
                  </p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {data.previous_chunk.content.replace(/\n/g, " ")}
                  </p>
                </div>
              )}

              <div className="rounded-md bg-primary/5 border border-primary/20 p-3">
                <p className="text-[10px] font-medium uppercase tracking-wider text-primary mb-1">
                  Matched chunk
                </p>
                <p className="text-sm leading-relaxed">
                  {data.chunk.content.replace(/\n/g, " ")}
                </p>
              </div>

              {data.next_chunk && (
                <div className="rounded-md bg-muted/50 p-3">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Next context
                  </p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {data.next_chunk.content.replace(/\n/g, " ")}
                  </p>
                </div>
              )}

              <Button variant="outline" className="w-full" asChild>
                <Link href={`/documents/${data.chunk.document_id}`}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Document
                </Link>
              </Button>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
