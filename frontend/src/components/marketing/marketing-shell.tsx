"use client";

import { ParticlesBackdrop } from "./particles-backdrop";

/**
 * Wrapper for landing/login/register: forces dark theme via the `.dark` class
 * regardless of user preference, drops in the particle field, and applies the
 * deep-navy → black gradient that the cyan particles read on top of.
 *
 * Why a wrapper and not a route-group layout: shadcn's `next-themes` provider
 * lives in the root layout, so we don't override it — we just hard-paint dark
 * on the marketing surfaces. Interior workspace continues to honour the toggle.
 */
export function MarketingShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark relative min-h-screen overflow-hidden bg-[#05060a] text-foreground">
      {/* Soft cyan halo behind everything */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-20"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(6,182,212,0.15), transparent 60%), radial-gradient(ellipse 60% 40% at 50% 110%, rgba(34,211,238,0.08), transparent 60%)",
        }}
      />
      <ParticlesBackdrop />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
