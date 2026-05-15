"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/auth-context";
import { MarketingShell } from "@/components/marketing/marketing-shell";
import { AuthCard } from "@/components/marketing/auth-card";

function LoginForm() {
  const { login, user, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(redirect || "/documents");
    }
  }, [user, isLoading, router, redirect]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login({ email, password });
      if (redirect) {
        window.location.href = redirect;
      }
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Login failed");
      } else {
        setError("Login failed");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      description="Sign in to continue chatting with your documents"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-cyan-300 hover:text-cyan-200">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div
            role="alert"
            className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200"
          >
            {error}
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="email" className="text-white/70">
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="border-white/10 bg-white/[0.04] text-white placeholder:text-white/30 focus-visible:border-cyan-400/50 focus-visible:ring-cyan-400/20"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password" className="text-white/70">
            Password
          </Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="border-white/10 bg-white/[0.04] text-white placeholder:text-white/30 focus-visible:border-cyan-400/50 focus-visible:ring-cyan-400/20"
          />
        </div>
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gradient-to-r from-cyan-500 to-cyan-400 text-black hover:from-cyan-400 hover:to-cyan-300 shadow-[0_0_24px_-6px_rgba(6,182,212,0.6)]"
        >
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthCard>
  );
}

export default function LoginPage() {
  return (
    <MarketingShell>
      <div className="flex min-h-screen items-center justify-center px-4 py-12">
        <Suspense>
          <LoginForm />
        </Suspense>
      </div>
    </MarketingShell>
  );
}
