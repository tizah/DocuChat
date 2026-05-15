import Link from "next/link";
import { FileText } from "lucide-react";

interface AuthCardProps {
  title: string;
  description: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}

/**
 * Glassmorphism card used by /login and /register. Renders on top of the
 * MarketingShell particle backdrop.
 */
export function AuthCard({ title, description, children, footer }: AuthCardProps) {
  return (
    <div className="w-full max-w-md">
      {/* Logo + product name above the card so the card itself stays focused */}
      <Link
        href="/"
        className="mb-8 flex items-center justify-center gap-2 text-lg font-semibold tracking-tight"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-cyan-400 to-cyan-600 shadow-[0_0_20px_-4px_rgba(6,182,212,0.6)]">
          <FileText className="h-4 w-4 text-black" />
        </div>
        <span>DocuChat</span>
      </Link>

      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-8 shadow-2xl backdrop-blur-2xl">
        {/* hairline accent at the top edge */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent"
        />
        <div className="space-y-1 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-white">{title}</h1>
          <p className="text-sm text-white/55">{description}</p>
        </div>

        <div className="mt-6">{children}</div>

        <div className="mt-6 text-center text-sm text-white/55">{footer}</div>
      </div>
    </div>
  );
}
