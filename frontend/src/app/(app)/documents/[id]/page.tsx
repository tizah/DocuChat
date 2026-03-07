"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Calendar, File, Hash, Layers, Loader2, Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDocument } from "@/hooks/use-documents";
import { useDocumentChunks } from "@/hooks/use-chunks";
import type { Chunk } from "@/types/document";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function highlightMatch(text: string, query: string): React.ReactNode {
  if (!query) return text;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 rounded-sm px-0.5">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: doc, isLoading: docLoading } = useDocument(id);
  const { data: chunksData, isLoading: chunksLoading } = useDocumentChunks(id);
  const [search, setSearch] = useState("");

  const isLoading = docLoading || chunksLoading;

  // Group chunks by page number and filter by search
  const groupedChunks = useMemo(() => {
    if (!chunksData?.chunks) return new Map<number, Chunk[]>();

    const filtered = search
      ? chunksData.chunks.filter((c) =>
          c.content.toLowerCase().includes(search.toLowerCase()),
        )
      : chunksData.chunks;

    const grouped = new Map<number, Chunk[]>();
    for (const chunk of filtered) {
      const page = chunk.page_number;
      if (!grouped.has(page)) grouped.set(page, []);
      grouped.get(page)!.push(chunk);
    }
    return grouped;
  }, [chunksData, search]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-6">
        <p className="text-sm text-muted-foreground">Document not found.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="border-b px-6 py-3 shrink-0">
        <Link
          href="/documents"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to documents
        </Link>
        <h1 className="text-lg font-semibold mt-1">{doc.filename}</h1>
      </div>

      <div className="p-6 space-y-6 max-w-4xl">
        {/* Metadata cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card>
            <CardContent className="p-3 flex items-center gap-2">
              <File className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-[10px] uppercase text-muted-foreground">Size</p>
                <p className="text-sm font-medium">{formatBytes(doc.size_bytes)}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 flex items-center gap-2">
              <Layers className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-[10px] uppercase text-muted-foreground">Pages</p>
                <p className="text-sm font-medium">{doc.page_count ?? "—"}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 flex items-center gap-2">
              <Hash className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-[10px] uppercase text-muted-foreground">Chunks</p>
                <p className="text-sm font-medium">{chunksData?.total ?? "—"}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-[10px] uppercase text-muted-foreground">Uploaded</p>
                <p className="text-sm font-medium">{formatDate(doc.created_at)}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search document text..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Chunks grouped by page */}
        {groupedChunks.size === 0 && search && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No chunks match &ldquo;{search}&rdquo;
          </p>
        )}

        {Array.from(groupedChunks.entries())
          .sort(([a], [b]) => a - b)
          .map(([page, chunks]) => (
            <div key={page}>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                Page {page}
              </h3>
              <div className="space-y-2">
                {chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className={`rounded-md border p-3 text-sm leading-relaxed whitespace-pre-wrap ${
                      search ? "bg-accent/30" : ""
                    }`}
                  >
                    {search ? highlightMatch(chunk.content, search) : chunk.content}
                  </div>
                ))}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
