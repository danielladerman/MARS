import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { flip } from "@remotion/transitions/flip";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { clockWipe } from "@remotion/transitions/clock-wipe";

const INTRO_DURATION_FRAMES = 90;
const UI_DURATION_FRAMES = 120;
const ORCHESTRATION_DURATION_FRAMES = 120;
const OUTPUT_ONE_DURATION_FRAMES = 110;
const OUTPUT_TWO_DURATION_FRAMES = 110;
const FINALE_DURATION_FRAMES = 80;
const TRANSITION_DURATION_FRAMES = 16;

const COLOR = {
  ink: "#05060d",
  white: "#f8f9ff",
  lavender: "#c7c3ff",
  gold: "#f7d154",
  cyan: "#5eead4",
  magenta: "#f472b6",
  violet: "#8b5cf6",
};

const BACKGROUND_GRADIENT =
  "linear-gradient(135deg, #06081b 0%, #1a0b35 35%, #2d0b5a 70%, #4f179e 100%)";

const getSceneStyles = (
  frame: number,
  durationInFrames: number,
  fps: number
) => {
  const enter = spring({
    fps,
    frame,
    config: { damping: 170, mass: 0.9 },
  });
  const exit = spring({
    fps,
    frame: frame - (durationInFrames - 18),
    config: { damping: 170, mass: 0.9 },
  });

  const opacity = interpolate(
    frame,
    [0, 12, durationInFrames - 12, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const translateY = interpolate(enter, [0, 1], [26, 0]) +
    interpolate(exit, [0, 1], [0, -16]);
  const scale =
    interpolate(enter, [0, 1], [0.985, 1]) *
    interpolate(exit, [0, 1], [1, 0.985]);

  return {
    opacity,
    transform: `translateY(${translateY}px) scale(${scale})`,
  };
};

const SceneShell: React.FC<{
  frame: number;
  durationInFrames: number;
  fps: number;
  children: React.ReactNode;
}> = ({ frame, durationInFrames, fps, children }) => {
  const scene = getSceneStyles(frame, durationInFrames, fps);
  const glowShift = interpolate(frame, [0, durationInFrames], [-30, 30]);

  return (
    <AbsoluteFill style={{ background: COLOR.ink }}>
      <AbsoluteFill
        style={{
          background: BACKGROUND_GRADIENT,
          color: COLOR.white,
          fontFamily: "Inter, system-ui, sans-serif",
          padding: 72,
          ...scene,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: -160,
            background:
              "radial-gradient(circle at 20% 20%, rgba(94, 234, 212, 0.18), transparent 52%), radial-gradient(circle at 80% 10%, rgba(244, 114, 182, 0.18), transparent 55%), radial-gradient(circle at 70% 80%, rgba(139, 92, 246, 0.24), transparent 60%)",
            transform: `translate(${glowShift}px, ${-glowShift}px)`,
          }}
        />
        <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Kicker: React.FC<{ label: string }> = ({ label }) => (
  <div
    style={{
      fontSize: 16,
      letterSpacing: 3,
      textTransform: "uppercase",
      color: COLOR.gold,
    }}
  >
    {label}
  </div>
);

const HeroTitle: React.FC<{ title: string; subtitle: string }> = ({
  title,
  subtitle,
}) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
    <h1 style={{ fontSize: 62, margin: 0, lineHeight: 1.05 }}>{title}</h1>
    <p style={{ fontSize: 26, margin: 0, maxWidth: 800, color: COLOR.lavender }}>
      {subtitle}
    </p>
  </div>
);

const Chip: React.FC<{ label: string; color: string }> = ({
  label,
  color,
}) => (
  <div
    style={{
      padding: "8px 14px",
      borderRadius: 999,
      background: color,
      color: "#0f1022",
      fontWeight: 600,
      fontSize: 16,
    }}
  >
    {label}
  </div>
);

const BrowserFrame: React.FC<{
  title: string;
  children: React.ReactNode;
}> = ({ title, children }) => (
  <div
    style={{
      borderRadius: 22,
      overflow: "hidden",
      border: "1px solid rgba(255,255,255,0.18)",
      background: "rgba(12, 14, 30, 0.9)",
      boxShadow: "0 28px 80px rgba(0,0,0,0.55)",
    }}
  >
    <div
      style={{
        display: "flex",
        gap: 8,
        alignItems: "center",
        padding: "12px 16px",
        background: "rgba(255,255,255,0.06)",
      }}
    >
      {["#f87171", "#fbbf24", "#34d399"].map((color) => (
        <span
          key={color}
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: color,
          }}
        />
      ))}
      <div
        style={{
          marginLeft: 10,
          padding: "6px 14px",
          borderRadius: 999,
          background: "rgba(255,255,255,0.08)",
          fontSize: 12,
          color: "#cbd5f5",
          flex: 1,
        }}
      >
        {title}
      </div>
    </div>
    <div style={{ padding: 20 }}>{children}</div>
  </div>
);

const StreamlitMock: React.FC = () => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "2fr 1fr",
      gap: 18,
    }}
  >
    <div
      style={{
        background: "#14162a",
        borderRadius: 16,
        padding: 24,
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      <div style={{ fontSize: 20, fontWeight: 600 }}>
        🍬 M&M's Strategic Intelligence System
      </div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>
        Generate Strategic Intelligence Report
      </div>
      <div style={{ color: COLOR.lavender, fontSize: 18 }}>
        Competitive analysis → checkpoint → creative strategy.
      </div>
      <div
        style={{
          background: "linear-gradient(90deg, #f7d154, #ffac4d)",
          color: "#1a103f",
          padding: "14px 18px",
          borderRadius: 14,
          width: 220,
          textAlign: "center",
          fontWeight: 700,
        }}
      >
        Start Analysis
      </div>
    </div>
    <div
      style={{
        background: "#0f1124",
        borderRadius: 16,
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ fontSize: 14, color: COLOR.lavender }}>
        Workflow Progress
      </div>
      {["Phase 1: Competitive Analysis", "Phase 2: Audience Strategy"].map(
        (label) => (
          <div
            key={label}
            style={{
              background: "#e2e3e5",
              color: "#111827",
              padding: 10,
              borderRadius: 10,
              fontWeight: 600,
            }}
          >
            ⏸️ {label}
          </div>
        )
      )}
      <div style={{ fontSize: 14, color: "#9aa4ff" }}>About</div>
      <div style={{ fontSize: 14, color: COLOR.lavender }}>
        MCP tools + LangSmith tracing
      </div>
    </div>
  </div>
);

const WebsiteMockup: React.FC<{ frame: number; fps: number }> = ({
  frame,
  fps,
}) => {
  const reveal = spring({ fps, frame, config: { damping: 180, mass: 0.8 } });
  const rotateY = interpolate(reveal, [0, 1], [-16, 0]);
  const rotateX = interpolate(reveal, [0, 1], [8, 0]);
  const float = interpolate(reveal, [0, 1], [24, 0]);

  return (
    <div
      style={{
        transform: `translateY(${float}px) perspective(1600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
      }}
    >
      <BrowserFrame title="streamlit.app/mars-intelligence">
        <StreamlitMock />
      </BrowserFrame>
    </div>
  );
};

const WorkflowLanes: React.FC<{ frame: number; fps: number }> = ({
  frame,
  fps,
}) => {
  const progress = spring({ fps, frame, config: { damping: 180, mass: 0.8 } });
  const glow = interpolate(progress, [0, 1], [0.15, 0.5]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
      {[
        {
          title: "Workflow 1",
          subtitle: "Competitive Intelligence",
          items: [
            "CEP benchmarking",
            "Performance clustering",
            "Strategic insights",
          ],
          color: COLOR.gold,
        },
        {
          title: "Workflow 2",
          subtitle: "Audience Strategy",
          items: [
            "GROW / SWITCH / RECRUIT",
            "Priority CEP mapping",
            "Creative playbooks",
          ],
          color: COLOR.cyan,
        },
      ].map((lane) => (
        <div
          key={lane.title}
          style={{
            background: "rgba(255,255,255,0.08)",
            borderRadius: 20,
            padding: 24,
            border: `1px solid ${lane.color}`,
            boxShadow: `0 20px 50px rgba(0,0,0,${glow})`,
          }}
        >
          <div style={{ fontSize: 18, color: lane.color, fontWeight: 700 }}>
            {lane.title}
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>
            {lane.subtitle}
          </div>
          <ul
            style={{
              marginTop: 18,
              paddingLeft: 18,
              display: "flex",
              flexDirection: "column",
              gap: 8,
              color: COLOR.white,
              fontSize: 18,
            }}
          >
            {lane.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

const OutputCard: React.FC<{
  frame: number;
  fps: number;
  imageSrc: string;
  title: string;
  description: string;
}> = ({ frame, fps, imageSrc, title, description }) => {
  const reveal = spring({ fps, frame, config: { damping: 200, mass: 0.7 } });
  const scale = interpolate(reveal, [0, 1], [0.92, 1]);
  const lift = interpolate(reveal, [0, 1], [32, 0]);
  const baseRotate = interpolate(reveal, [0, 1], [-14, -6]);
  const floatRotate = interpolate(frame, [0, 90], [-4, 4], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rotateY = baseRotate + floatRotate;
  const rotateX = interpolate(reveal, [0, 1], [9, 3]);
  const glow = interpolate(reveal, [0, 1], [0.2, 0.65]);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.6fr 1fr",
        gap: 28,
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `translateY(${lift}px) scale(${scale}) perspective(1800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
          boxShadow: `0 50px 130px rgba(0,0,0,0.6)`,
          borderRadius: 24,
          overflow: "hidden",
          border: `1px solid rgba(255,255,255,${glow})`,
        }}
      >
        <BrowserFrame title={imageSrc}>
          <div
            style={{
              background: "rgba(8, 10, 20, 0.9)",
              borderRadius: 16,
              padding: 10,
            }}
          >
            <Img
              src={staticFile(imageSrc)}
              style={{
                width: "100%",
                height: 360,
                objectFit: "contain",
                borderRadius: 12,
                background: "#0b0f1f",
              }}
            />
          </div>
        </BrowserFrame>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ fontSize: 28, fontWeight: 700 }}>{title}</div>
        <div style={{ fontSize: 18, color: COLOR.lavender }}>{description}</div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Chip label="Executive ready" color={COLOR.gold} />
          <Chip label="Insight rich" color={COLOR.cyan} />
          <Chip label="High-fidelity" color={COLOR.magenta} />
        </div>
      </div>
    </div>
  );
};

const FinaleRow: React.FC = () => (
  <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
    <Chip label="CEP benchmarking" color={COLOR.gold} />
    <Chip label="Creative strategy" color={COLOR.cyan} />
    <Chip label="Click of a button" color={COLOR.magenta} />
  </div>
); 

export const MyComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const introFrame = frame;
  const uiFrame = Math.max(0, frame - (INTRO_DURATION_FRAMES - TRANSITION_DURATION_FRAMES));
  const orchestrationFrame = Math.max(
    0,
    frame - (INTRO_DURATION_FRAMES + UI_DURATION_FRAMES - 2 * TRANSITION_DURATION_FRAMES)
  );
  const outputOneFrame = Math.max(
    0,
    frame -
      (INTRO_DURATION_FRAMES +
        UI_DURATION_FRAMES +
        ORCHESTRATION_DURATION_FRAMES -
        3 * TRANSITION_DURATION_FRAMES)
  );
  const outputTwoFrame = Math.max(
    0,
    frame -
      (INTRO_DURATION_FRAMES +
        UI_DURATION_FRAMES +
        ORCHESTRATION_DURATION_FRAMES +
        OUTPUT_ONE_DURATION_FRAMES -
        4 * TRANSITION_DURATION_FRAMES)
  );
  const finaleFrame = Math.max(
    0,
    frame -
      (INTRO_DURATION_FRAMES +
        UI_DURATION_FRAMES +
        ORCHESTRATION_DURATION_FRAMES +
        OUTPUT_ONE_DURATION_FRAMES +
        OUTPUT_TWO_DURATION_FRAMES -
        5 * TRANSITION_DURATION_FRAMES)
  );

  const transitionTiming = linearTiming({
    durationInFrames: TRANSITION_DURATION_FRAMES,
  });
  const clockWipePresentation = clockWipe({ width, height });

  return (
    <AbsoluteFill style={{ background: COLOR.ink }}>
      <Audio
        src={staticFile(
          "female.mp3"
        )}
        volume={0.9}
      />
      <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={INTRO_DURATION_FRAMES}>
        <SceneShell frame={introFrame} durationInFrames={INTRO_DURATION_FRAMES} fps={fps}>
          <Kicker label="Mars Strategic Intelligence" />
          <HeroTitle
            title="AI orchestration for intelligent content"
            subtitle="A two-workflow system that turns competitive data into creative strategy for Mars."
          />
          <div style={{ marginTop: 32, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Chip label="Multi-agent LangGraph" color={COLOR.gold} />
            <Chip label="Human-in-the-loop checkpoint" color={COLOR.cyan} />
            <Chip label="Executive-ready outputs" color={COLOR.magenta} />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={slide({ direction: "from-right" })}
        timing={transitionTiming}
      />

      <TransitionSeries.Sequence durationInFrames={UI_DURATION_FRAMES}>
        <SceneShell frame={uiFrame} durationInFrames={UI_DURATION_FRAMES} fps={fps}>
          <Kicker label="Agentic Flow" />
          <HeroTitle
            title="Data to strategy in minutes"
            subtitle="The flow guides stakeholders through analysis, checkpoints, and audience strategy."
          />
          <div style={{ marginTop: 28 }}>
            <WebsiteMockup frame={uiFrame} fps={fps} />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={transitionTiming} />

      <TransitionSeries.Sequence durationInFrames={ORCHESTRATION_DURATION_FRAMES}>
        <SceneShell
          frame={orchestrationFrame}
          durationInFrames={ORCHESTRATION_DURATION_FRAMES}
          fps={fps}
        >
          <Kicker label="Two Workflow Orchestration" />
          <HeroTitle
            title="Competitive intelligence to creative strategy"
            subtitle="From 22 days to 4 hours."
          />
          <div style={{ marginTop: 28 }}>
            <WorkflowLanes frame={orchestrationFrame} fps={fps} />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={wipe({ direction: "from-bottom" })} timing={transitionTiming} />

      <TransitionSeries.Sequence durationInFrames={OUTPUT_ONE_DURATION_FRAMES}>
        <SceneShell
          frame={outputOneFrame}
          durationInFrames={OUTPUT_ONE_DURATION_FRAMES}
          fps={fps}
        >
          <Kicker label="Workflow Output 1" />
          <HeroTitle
            title="CEP analysis and insights"
            subtitle="Competitive signals distilled into white space and winning CEP opportunities."
          />
          <div style={{ marginTop: 24 }}>
            <OutputCard
              frame={outputOneFrame}
              fps={fps}
              imageSrc="Attached_image.png"
              title="CEP Opportunity Map"
              description="Visualize brand performance and opportunity across key Category Entry Points."
            />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={flip({ direction: "from-left" })} timing={transitionTiming} />

      <TransitionSeries.Sequence durationInFrames={OUTPUT_TWO_DURATION_FRAMES}>
        <SceneShell
          frame={outputTwoFrame}
          durationInFrames={OUTPUT_TWO_DURATION_FRAMES}
          fps={fps}
        >
          <Kicker label="Workflow Output 2" />
          <HeroTitle
            title="Audience + creative playbook"
            subtitle="Audience segments, CEP matchups, and idea pipelines built for Mars."
          />
          <div style={{ marginTop: 24 }}>
            <OutputCard
              frame={outputTwoFrame}
              fps={fps}
              imageSrc="Screenshot 2026-01-29 at 11.01.51 AM.png"
              title="Switch Audience Strategy"
              description="Segment-specific creative ideas and competitive context at a glance."
            />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={clockWipePresentation} timing={transitionTiming} />

      <TransitionSeries.Sequence durationInFrames={FINALE_DURATION_FRAMES}>
        <SceneShell frame={finaleFrame} durationInFrames={FINALE_DURATION_FRAMES} fps={fps}>
          <Kicker label="Launch Ready" />
          <HeroTitle
            title="Fuel your your intelligent content with data"
            subtitle="Deliver stakeholder-ready outputs."
          />
          <div style={{ marginTop: 28 }}>
            <FinaleRow />
          </div>
        </SceneShell>
      </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
