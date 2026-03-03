import Link from "next/link";
import { FileText, MessageSquare, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-14 items-center border-b border-border px-6">
        <div className="flex items-center gap-2 font-semibold text-lg">
          <FileText className="h-6 w-6 text-primary" />
          <span>DocuChat</span>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Chat with your documents
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Upload PDFs and DOCX files, then ask questions and get AI-powered answers with source
            citations. Built with RAG for accurate, grounded responses.
          </p>

          <div className="mt-8">
            <Button asChild size="lg">
              <Link href="/documents">Get Started</Link>
            </Button>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-3">
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Upload Documents</h3>
              <p className="text-sm text-muted-foreground">
                Drag and drop PDFs or DOCX files for automatic processing.
              </p>
            </div>
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Search className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Semantic Search</h3>
              <p className="text-sm text-muted-foreground">
                AI-powered chunking and embeddings for accurate retrieval.
              </p>
            </div>
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold">Chat with Citations</h3>
              <p className="text-sm text-muted-foreground">
                Ask questions and get answers with inline source references.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
