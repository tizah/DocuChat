"use client";

import { useMemo } from "react";
import { Particles, ParticlesProvider } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import type { Engine, ISourceOptions } from "@tsparticles/engine";

/**
 * Connected-line particle field, scoped to dark marketing surfaces.
 * Wraps `<Particles>` in its own `<ParticlesProvider>` so the engine only
 * loads on routes that mount this component.
 */
export function ParticlesBackdrop() {
  const options = useMemo<ISourceOptions>(
    () => ({
      background: { color: { value: "transparent" } },
      fpsLimit: 60,
      detectRetina: true,
      particles: {
        number: { value: 60, density: { enable: true } },
        color: { value: ["#06b6d4", "#22d3ee", "#67e8f9"] },
        links: {
          enable: true,
          color: "#06b6d4",
          distance: 150,
          opacity: 0.25,
          width: 1,
        },
        move: {
          enable: true,
          speed: 0.6,
          direction: "none",
          random: false,
          straight: false,
          outModes: { default: "out" },
        },
        size: { value: { min: 1, max: 2 } },
        opacity: {
          value: { min: 0.2, max: 0.6 },
          animation: { enable: true, speed: 0.6, sync: false },
        },
      },
      interactivity: {
        events: {
          onHover: { enable: true, mode: "grab" },
        },
        modes: {
          grab: { distance: 160, links: { opacity: 0.6 } },
        },
      },
    }),
    [],
  );

  return (
    <div aria-hidden className="pointer-events-auto absolute inset-0 -z-10">
      <ParticlesProvider init={initEngine}>
        <Particles
          id="tsparticles-marketing"
          options={options}
          className="h-full w-full"
        />
      </ParticlesProvider>
    </div>
  );
}

async function initEngine(engine: Engine) {
  await loadSlim(engine);
}
