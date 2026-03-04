"use client";

import { FileText } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { useDocuments } from "@/hooks/use-documents";

interface DocumentSelectorProps {
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

export function DocumentSelector({
  selectedIds,
  onSelectionChange,
}: DocumentSelectorProps) {
  const { data, isLoading } = useDocuments();
  const readyDocs =
    data?.documents.filter((d) => d.status === "ready") ?? [];

  const toggleDocument = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((s) => s !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  const toggleAll = () => {
    if (selectedIds.length === readyDocs.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(readyDocs.map((d) => d.id));
    }
  };

  if (isLoading) {
    return (
      <div className="p-3 text-sm text-muted-foreground">
        Loading documents...
      </div>
    );
  }

  if (readyDocs.length === 0) {
    return (
      <div className="p-3 text-sm text-muted-foreground">
        No documents ready. Upload and process documents first.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Documents ({selectedIds.length}/{readyDocs.length})
        </span>
        <button
          onClick={toggleAll}
          className="text-xs text-primary hover:underline"
        >
          {selectedIds.length === readyDocs.length
            ? "Deselect all"
            : "Select all"}
        </button>
      </div>
      <div className="max-h-48 overflow-y-auto">
        <div className="flex flex-col gap-1">
          {readyDocs.map((doc) => (
            <label
              key={doc.id}
              className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted cursor-pointer"
            >
              <Checkbox
                checked={selectedIds.includes(doc.id)}
                onCheckedChange={() => toggleDocument(doc.id)}
              />
              <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              <span className="text-sm truncate">{doc.filename}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
