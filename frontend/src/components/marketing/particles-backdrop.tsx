"use client";

import { useEffect, useMemo, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import type { ISourceOptions } from "@tsparticles/engine";

/**
 * Connected-line cyan particle field, scoped to dark marketing surfaces.
 * Uses the v3 initParticlesEngine + Particles pattern.
 */
export function ParticlesBackdrop() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    })
      .then(() => setReady(true))
      .catch((err) => {
        console.error("[tsparticles] init failed", err);
      });
  }, []);

  const options = useMemo<ISourceOptions>(
    () => ({
      // Render inside our absolutely-positioned container, not as a fixed
      // fullscreen canvas (which would land at z-index -1 behind the wrapper).
      fullScreen: { enable: false },
      background: { color: { value: "transparent" } },
      fpsLimit: 60,
      detectRetina: true,
      particles: {
        number: { value: 80, density: { enable: true, area: 900 } },
        color: { value: ["#06b6d4", "#22d3ee", "#67e8f9"] },
        links: {
          enable: true,
          color: "#06b6d4",
          distance: 150,
          opacity: 0.3,
          width: 1,
        },
        move: {
          enable: true,
          speed: 0.7,
          direction: "none",
          random: false,
          straight: false,
          outModes: { default: "out" },
        },
        size: { value: { min: 1, max: 2.5 } },
        opacity: {
          value: { min: 0.3, max: 0.7 },
          animation: { enable: true, speed: 0.6, sync: false },
        },
      },
      interactivity: {
        events: {
          onHover: { enable: true, mode: "grab" },
        },
        modes: {
          grab: { distance: 160, links: { opacity: 0.7 } },
        },
      },
    }),
    [],
  );

  if (!ready) return null;
  return (
    <Particles
      id="tsparticles-marketing"
      options={options}
      className="absolute inset-0 -z-10"
    />
  );
}
