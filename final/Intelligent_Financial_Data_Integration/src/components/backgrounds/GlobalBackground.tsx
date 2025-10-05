// src/components/backgrounds/GlobalBackground.tsx
import LiquidEther from "./LiquidEther";

export default function GlobalBackground() {
  return (
    <div
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{ width: "100vw", height: "100vh" }}
    >
      <LiquidEther
        // keep background transparent; the shader already is alpha:0 for bg
        colors={["#5227FF", "#FF9FFC", "#B19EEF"]}
        resolution={0.75}        // tweak if you want more detail
        autoDemo={true}          // or false if you only want mouse-driven
        autoSpeed={0.6}
        autoIntensity={2.4}
        takeoverDuration={0.25}
        autoResumeDelay={3000}
        autoRampDuration={0.6}
        // IMPORTANT so it never eats clicks:
        style={{ width: "100%", height: "100%", pointerEvents: "none" }}
        className="touch-none"
      />
    </div>
  );
}
