import Link from "next/link";
import { ArrowRight, FileText, MessageSquare, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/marketing/marketing-shell";

const features = [
  {
    icon: FileText,
    title: "Upload anything",
    body: "PDFs and DOCX files up to 20MB. Extracted, chunked, and indexed in seconds.",
  },
  {
    icon: Search,
    title: "Semantic retrieval",
    body: "pgvector cosine search over OpenAI embeddings. Filtered to your documents only.",
  },
  {
    icon: MessageSquare,
    title: "Cited answers",
    body: "Streamed responses with inline source references you can click to verify.",
  },
];

export default function Home() {
  return (
    <MarketingShell>
      <header className="flex h-16 items-center justify-between border-b border-white/5 px-6 backdrop-blur-sm">
        <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-cyan-400 to-cyan-600 shadow-[0_0_20px_-4px_rgba(6,182,212,0.6)]">
            <FileText className="h-4 w-4 text-black" />
          </div>
          <span className="tracking-tight">DocuChat</span>
        </Link>
        <Button asChild variant="ghost" size="sm" className="text-white/80 hover:text-white hover:bg-white/5">
          <Link href="/login">Sign in</Link>
        </Button>
      </header>

      <main className="flex flex-col items-center px-4 py-24 sm:py-32">
        <div className="mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-3 py-1 text-xs font-medium text-cyan-300 backdrop-blur-sm">
            <Sparkles className="h-3 w-3" />
            RAG with inline citations
          </div>

          <h1 className="mt-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
              Chat with your
            </span>
            <br />
            <span className="bg-gradient-to-r from-cyan-300 via-cyan-200 to-white bg-clip-text text-transparent">
              documents.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-white/60">
            Upload PDFs and Word docs, then ask questions and get streamed answers
            grounded in the source — not the model&apos;s prior knowledge.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Button
              asChild
              size="lg"
              className="group bg-gradient-to-r from-cyan-500 to-cyan-400 text-black hover:from-cyan-400 hover:to-cyan-300 shadow-[0_0_30px_-5px_rgba(6,182,212,0.6)]"
            >
              <Link href="/register">
                Get started
                <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              size="lg"
              className="text-white/80 hover:text-white hover:bg-white/5"
            >
              <Link href="/login">Sign in</Link>
            </Button>
          </div>
        </div>

        <div className="mt-24 grid w-full max-w-5xl gap-4 sm:grid-cols-3">
          {features.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm transition-colors hover:border-cyan-500/30 hover:bg-white/[0.04]"
            >
              <div
                aria-hidden
                className="pointer-events-none absolute -top-px left-1/2 h-px w-2/3 -translate-x-1/2 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
              />
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 ring-1 ring-cyan-400/20">
                <Icon className="h-5 w-5 text-cyan-300" />
              </div>
              <h3 className="mt-5 font-semibold tracking-tight text-white">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/55">{body}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className="border-t border-white/5 px-6 py-6 text-center text-xs text-white/40">
        Built with Next.js, FastAPI, and pgvector. Open source on{" "}
        <a
          href="https://github.com/tizah/DocuChat"
          className="text-cyan-300/80 hover:text-cyan-300"
          target="_blank"
          rel="noreferrer noopener"
        >
          GitHub
        </a>
        .
      </footer>
    </MarketingShell>
  );
}
