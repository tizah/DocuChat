"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { FileText, FileIcon, Trash2, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { DocumentListSkeleton } from "@/components/document-list-skeleton";
import { useDocuments, useDeleteDocument } from "@/hooks/use-documents";
import type { Document } from "@/types/document";
import { isProcessing } from "@/types/document";

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

function statusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "ready":
      return "default";
    case "uploaded":
    case "extracted":
    case "extracting":
    case "chunking":
    case "embedding":
      return "secondary";
    case "failed":
      return "destructive";
    default:
      return "outline";
  }
}

const PIPELINE_STEPS = ["extracting", "chunking", "embedding", "ready"] as const;

function ProcessingIndicator({ status }: { status: string }) {
  if (!isProcessing(status) && status !== "ready") return null;

  const currentIdx = PIPELINE_STEPS.indexOf(status as (typeof PIPELINE_STEPS)[number]);

  return (
    <div className="mt-2 flex items-center gap-1.5">
      {PIPELINE_STEPS.map((step, idx) => {
        const isDone = idx < currentIdx || status === "ready";
        const isCurrent = step === status;

        return (
          <div key={step} className="flex items-center gap-1">
            {isDone ? (
              <CheckCircle className="h-3 w-3 text-green-500" />
            ) : isCurrent ? (
              <Loader2 className="h-3 w-3 animate-spin text-primary" />
            ) : (
              <div className="h-3 w-3 rounded-full border border-muted-foreground/30" />
            )}
            <span
              className={`text-[10px] ${
                isDone ? "text-green-600" : isCurrent ? "text-primary font-medium" : "text-muted-foreground/50"
              }`}
            >
              {step.charAt(0).toUpperCase() + step.slice(1)}
            </span>
            {idx < PIPELINE_STEPS.length - 1 && (
              <div className="mx-0.5 h-px w-3 bg-muted-foreground/20" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function FileTypeIcon({ type }: { type: string }) {
  if (type === "pdf") {
    return <FileText className="h-8 w-8 text-red-500" />;
  }
  return <FileIcon className="h-8 w-8 text-blue-500" />;
}

function DocumentCard({
  doc,
  onDelete,
}: {
  doc: Document;
  onDelete: (doc: Document) => void;
}) {
  const processing = isProcessing(doc.status);

  return (
    <Card>
      <CardContent className="flex items-start gap-4 p-4">
        <div className="mt-0.5">
          <FileTypeIcon type={doc.file_type} />
        </div>
        <div className="flex-1 min-w-0">
          <Link
            href={`/documents/${doc.id}`}
            className="truncate font-medium text-sm hover:underline"
          >
            {doc.filename}
          </Link>
          <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
            <span>{formatBytes(doc.size_bytes)}</span>
            <span>{formatDate(doc.created_at)}</span>
            {doc.page_count && <span>{doc.page_count} page(s)</span>}
          </div>
          {(processing || doc.status === "ready") && <ProcessingIndicator status={doc.status} />}
          {doc.status === "failed" && doc.error_message && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-destructive">
              <AlertCircle className="h-3 w-3" />
              <span className="truncate">{doc.error_message}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={statusVariant(doc.status)}>{doc.status}</Badge>
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Delete ${doc.filename}`}
            onClick={() => onDelete(doc)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function DocumentList() {
  const { data, isLoading, error } = useDocuments();
  const deleteMutation = useDeleteDocument();
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast.success("Document deleted");
    } catch {
      toast.error("Failed to delete document");
    } finally {
      setDeleteTarget(null);
    }
  };

  if (isLoading) {
    return <DocumentListSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4" role="alert">
        <p className="text-sm text-destructive">
          Failed to load documents. Make sure the backend is running.
        </p>
      </div>
    );
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-sm font-medium">No documents yet</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Upload a PDF or DOCX to get started.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        {data.documents.map((doc) => (
          <DocumentCard key={doc.id} doc={doc} onDelete={setDeleteTarget} />
        ))}
      </div>

      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.filename}&rdquo;? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
