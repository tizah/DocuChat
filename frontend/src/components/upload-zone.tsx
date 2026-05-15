"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Check,
  CloudUpload,
  FileText,
  Layers,
  Loader2,
  ScanText,
  Sparkles,
  X,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useDocumentStatus, useUploadDocument } from "@/hooks/use-documents";
import { isProcessing } from "@/types/document";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const PIPELINE_STEPS = [
  { key: "extracting", label: "Extracting", icon: ScanText },
  { key: "chunking", label: "Chunking", icon: Layers },
  { key: "embedding", label: "Embedding", icon: Sparkles },
] as const;

/**
 * Stages that come from user actions (managed directly).
 * Server-driven stages ("processing", "done") are derived from the status poll.
 */
type LocalStage = "idle" | "dragging" | "uploading" | "error";
type Stage = LocalStage | "processing" | "done";

export function UploadZone() {
  const [localStage, setLocalStage] = useState<LocalStage>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [activeFilename, setActiveFilename] = useState<string | null>(null);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDocument();

  // Poll the doc that was just uploaded so we can show extracting → chunking → embedding.
  const { data: status } = useDocumentStatus(activeDocId);

  // Derive the visible stage. Server-side statuses take over once we have one.
  const stage: Stage = (() => {
    if (localStage === "uploading" || localStage === "dragging") return localStage;
    if (localStage === "error") return "error";
    if (status?.status === "ready") return "done";
    if (status?.status === "failed") return "error";
    if (status && isProcessing(status.status)) return "processing";
    return localStage;
  })();

  // When the doc reaches a terminal state, auto-reset back to idle after a delay.
  useEffect(() => {
    if (status?.status !== "ready") return;
    const t = setTimeout(() => {
      setLocalStage("idle");
      setActiveDocId(null);
      setActiveFilename(null);
    }, 2200);
    return () => clearTimeout(t);
  }, [status?.status]);

  // Backend error (from polling) and local error (from validation/upload mutation)
  // are merged at render time so we never imperatively setError in an effect.
  const displayedError =
    error ?? (status?.status === "failed" ? status.error_message : null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError("Only PDF and DOCX files are supported.");
        setLocalStage("error");
        return;
      }

      setError(null);
      setProgress(0);
      setActiveFilename(file.name);
      setLocalStage("uploading");

      try {
        const doc = await upload.mutateAsync({
          file,
          onProgress: setProgress,
        });
        setActiveDocId(doc.id);
        // Drop back to idle locally — the derived stage will become "processing"
        // as soon as the status poll returns.
        setLocalStage("idle");
        toast.success(`${file.name} uploaded — processing…`);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Upload failed. Please try again.";
        setError(message);
        setLocalStage("error");
        toast.error(message);
      }
    },
    [upload],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (localStage === "idle") setLocalStage("dragging");
    },
    [localStage],
  );

  const handleDragLeave = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (localStage === "dragging") setLocalStage("idle");
    },
    [localStage],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleClick = () => {
    if (stage === "idle" || stage === "error") fileInputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const reset = () => {
    setLocalStage("idle");
    setError(null);
    setProgress(0);
    setActiveDocId(null);
    setActiveFilename(null);
  };

  const isInteractive = stage === "idle" || stage === "error";
  const isBusy = stage === "uploading" || stage === "processing";

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={isInteractive ? 0 : -1}
        aria-label="Upload document. Drag and drop or click to select a PDF or DOCX file."
        aria-disabled={!isInteractive}
        data-stage={stage}
        className={[
          "group relative flex flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed p-8 transition-all duration-300",
          isInteractive ? "cursor-pointer" : "cursor-default",
          stage === "dragging" &&
            "scale-[1.01] border-primary bg-primary/5 shadow-[0_0_30px_-8px_rgba(6,182,212,0.45)]",
          stage === "idle" && "border-border hover:border-primary/50 hover:bg-muted/50",
          stage === "uploading" && "border-primary/40 bg-primary/5",
          stage === "processing" && "border-primary/40 bg-primary/5",
          stage === "done" && "border-emerald-500/50 bg-emerald-500/5",
          stage === "error" && "border-destructive/50 bg-destructive/5",
        ]
          .filter(Boolean)
          .join(" ")}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && isInteractive) {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        {/* sliding shimmer while uploading */}
        {stage === "uploading" && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-primary/10 to-transparent animate-[shimmer_1.4s_infinite] [background-size:200%_100%]"
          />
        )}

        {stage === "idle" && <IdleState />}
        {stage === "dragging" && <DraggingState />}
        {stage === "uploading" && (
          <UploadingState filename={activeFilename} progress={progress} />
        )}
        {stage === "processing" && (
          <ProcessingState
            filename={activeFilename}
            currentStatus={status?.status ?? "extracting"}
          />
        )}
        {stage === "done" && <DoneState filename={activeFilename} />}
        {stage === "error" && <ErrorState message={displayedError} onReset={reset} />}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleInputChange}
        aria-hidden="true"
      />

      {isBusy && progress > 0 && progress < 100 && stage === "uploading" && (
        <Progress value={progress} className="h-1.5" />
      )}

      <style jsx>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
}

function IdleState() {
  return (
    <>
      <CloudUpload className="mb-3 h-9 w-9 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:text-primary" />
      <p className="text-sm font-medium">Drag &amp; drop or click to upload</p>
      <p className="mt-1 text-xs text-muted-foreground">PDF or DOCX, up to 20MB</p>
    </>
  );
}

function DraggingState() {
  return (
    <>
      <CloudUpload className="mb-3 h-9 w-9 animate-bounce text-primary" />
      <p className="text-sm font-semibold text-primary">Drop your file</p>
      <p className="mt-1 text-xs text-muted-foreground">Release to start uploading</p>
    </>
  );
}

function UploadingState({
  filename,
  progress,
}: {
  filename: string | null;
  progress: number;
}) {
  return (
    <>
      <div className="relative mb-3">
        <Loader2 className="h-9 w-9 animate-spin text-primary" />
      </div>
      <p className="text-sm font-medium">Uploading {filename ?? "file"}</p>
      <p className="mt-1 text-xs text-muted-foreground">{progress}%</p>
    </>
  );
}

function ProcessingState({
  filename,
  currentStatus,
}: {
  filename: string | null;
  currentStatus: string;
}) {
  const currentIndex = PIPELINE_STEPS.findIndex((s) => s.key === currentStatus);
  return (
    <div className="flex w-full max-w-sm flex-col items-center">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
        <FileText className="h-4 w-4 text-primary" />
        <span className="truncate">{filename ?? "Document"}</span>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Indexing for retrieval — this usually takes a few seconds
      </p>
      <div className="flex w-full items-center justify-between">
        {PIPELINE_STEPS.map(({ key, label, icon: Icon }, i) => {
          const isDone = i < currentIndex;
          const isCurrent = i === currentIndex || (currentIndex === -1 && i === 0);
          return (
            <div key={key} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={[
                    "flex h-9 w-9 items-center justify-center rounded-full ring-1 transition-colors",
                    isDone && "bg-emerald-500/15 ring-emerald-500/30 text-emerald-400",
                    isCurrent &&
                      "bg-primary/15 ring-primary/40 text-primary animate-pulse",
                    !isDone && !isCurrent && "bg-muted/30 ring-border text-muted-foreground",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {isDone ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                </div>
                <span className="text-[10px] font-medium text-muted-foreground">
                  {label}
                </span>
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <div
                  className={[
                    "mx-1 h-px flex-1 transition-colors",
                    i < currentIndex ? "bg-emerald-500/40" : "bg-border",
                  ].join(" ")}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DoneState({ filename }: { filename: string | null }) {
  return (
    <>
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/15 ring-1 ring-emerald-500/30">
        <Check className="h-5 w-5 text-emerald-400" />
      </div>
      <p className="text-sm font-medium">{filename ?? "Document"} ready</p>
      <p className="mt-1 text-xs text-muted-foreground">Available in the chat sidebar</p>
    </>
  );
}

function ErrorState({
  message,
  onReset,
}: {
  message: string | null;
  onReset: () => void;
}) {
  return (
    <>
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-destructive/15 ring-1 ring-destructive/30">
        <X className="h-5 w-5 text-destructive" />
      </div>
      <p className="text-sm font-medium text-destructive">Upload failed</p>
      <p className="mt-1 text-xs text-muted-foreground">{message ?? "Please try again"}</p>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onReset();
        }}
        className="mt-3 text-xs font-medium text-primary hover:underline"
      >
        Try another file
      </button>
    </>
  );
}
