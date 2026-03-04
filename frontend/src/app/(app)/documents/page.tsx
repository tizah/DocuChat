import { UploadZone } from "@/components/upload-zone";
import { DocumentList } from "@/components/document-list";

export default function DocumentsPage() {
  return (
    <div className="mx-auto max-w-3xl p-6 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold">Documents</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Upload and manage your documents for AI-powered Q&A.
      </p>

      <div className="mt-6">
        <UploadZone />
      </div>

      <div className="mt-8">
        <DocumentList />
      </div>
    </div>
  );
}
