import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Box,
  Check,
  ChevronDown,
  Download,
  Layers3,
  Lock,
  Rotate3d,
  Sparkles,
  ScanLine,
  Unlock,
} from "lucide-react";
import "./styles.css";

const toHex = (rgb) => `#${rgb.map((value) => Math.round(value * 255).toString(16).padStart(2, "0")).join("")}`;
const mixRgb = (rgb, target, amount) => rgb.map((value, index) => value + (target[index] - value) * amount);

const COLORS = [
  ["deep-learning-red", "Deep Learning Red", [0.59, 0.13, 0.13]],
  ["runtime-berry", "Runtime Berry", [0.39, 0.04, 0.29]],
  ["render-rose", "Render Rose", [0.64, 0.44, 0.50]],
  ["pixar-pink", "Pixar Pink", [0.80, 0.23, 0.39]],
  ["null-mauve", "Null Mauve", [0.96, 0.64, 0.85]],
  ["cudiva", "CuDiva", [0.88, 0.46, 0.37]],
  ["softmax", "Softmax", [0.93, 0.57, 0.59]],
].map(([id, name, rgb]) => ({
  id,
  name,
  rgb,
  value: toHex(rgb),
  dark: toHex(mixRgb(rgb, [0, 0, 0], 0.48)),
  light: toHex(mixRgb(rgb, [1, 1, 1], 0.32)),
}));

const INNER_SLEEVE_FINISHES = [
  { id: "noir", name: "Noir", color: toHex([0.05, 0.05, 0.05]), shine: "#3b3b3b", shadow: "#080808" },
  { id: "matte-black", name: "Matte Black", color: toHex([0.08, 0.08, 0.08]), shine: "#343434", shadow: "#0b0b0b" },
  { id: "rose-metal", name: "Rose Metal", color: toHex([0.65, 0.42, 0.38]), shine: "#efc0b8", shadow: "#70443d" },
  { id: "silver", name: "Silver", color: toHex([0.75, 0.75, 0.78]), shine: "#f5f5fa", shadow: "#72727b" },
  { id: "gold", name: "Gold", color: toHex([0.83, 0.68, 0.21]), shine: "#ffe59a", shadow: "#755a10" },
];

const CASE_FINISHES = [
  ["gold", "Gold", [0.83, 0.68, 0.21], 1.0, 0.1],
  ["chrome", "Chrome", [0.80, 0.80, 0.82], 1.0, 0.05],
  ["matte-black", "Matte Black", [0.08, 0.08, 0.08], 0.0, 0.8],
  ["rose-metal", "Rose Metal", [0.85, 0.60, 0.55], 1.0, 0.1],
  ["pearl", "Pearl", [0.95, 0.95, 0.95], 0.0, 0.6],
  ["navy", "Navy", [0.08, 0.10, 0.25], 0.0, 0.5],
  ["lacquer-red", "Lacquer Red", [0.55, 0.08, 0.08], 0.0, 0.3],
].map(([id, name, body, metallic, roughness]) => ({
  id,
  name,
  body,
  value: toHex(body),
  dark: toHex(mixRgb(body, [0, 0, 0], 0.48)),
  metallic,
  roughness,
}));

const TWIST_BASE_FINISHES = [
  ["noir", "Noir", [0.05, 0.05, 0.05], 0.0, 0.5],
  ["matte-black", "Matte Black", [0.08, 0.08, 0.08], 0.0, 0.8],
  ["rose-metal", "Rose Metal", [0.65, 0.42, 0.38], 1.0, 0.1],
  ["silver", "Silver", [0.75, 0.75, 0.78], 1.0, 0.12],
  ["gold", "Gold", [0.83, 0.68, 0.21], 1.0, 0.1],
].map(([id, name, rgb, metallic, roughness]) => ({
  id,
  name,
  rgb,
  value: toHex(rgb),
  dark: toHex(mixRgb(rgb, [0, 0, 0], 0.48)),
  metallic,
  roughness,
}));

const ROBOVISION_VIEWS = [
  { id: "beauty", name: "RGB", purpose: "Color camera view used for appearance and visual inspection." },
  { id: "semantic", name: "Parts", purpose: "Per-pixel OpenUSD class labels: every color identifies an authored object part." },
  { id: "depth", name: "Depth", purpose: "Camera distance per pixel; warm pixels are nearer and cool pixels are farther away." },
  { id: "normals", name: "Normals", purpose: "Surface direction per pixel, useful for pose, contact, and shape reasoning." },
  { id: "pointcloud", name: "RGB-D Cloud", purpose: "3D points reconstructed from the RGB camera and its depth buffer—not a LiDAR scan." },
  { id: "affordance", name: "Robot Affordances", purpose: "Robot actions derived from part semantics and mechanism state: grasp, support, rotate, or avoid." },
];

const SEMANTIC_CLASSES = [
  "cap",
  "lipstick_bullet",
  "plastic_collar",
  "inner_sleeve",
  "twist_base",
  "outer_casing",
  "support_surface",
  "background",
];

const SEMANTIC_COLORS = [
  "#e26848",
  "#e7b33e",
  "#80c44e",
  "#34c2a4",
  "#489ae0",
  "#776de0",
  "#be5fd5",
  "#e05e8b",
];

const BACKDROPS = [
  { id: "warm", name: "Warm studio", from: "#ded1bd", to: "#a58e73" },
  { id: "graphite", name: "Graphite", from: "#575657", to: "#1d1d1f" },
  { id: "sage", name: "Sage", from: "#b5bdac", to: "#68745e" },
  { id: "sky", name: "Sky", from: "#cbd9df", to: "#7f9daa" },
];

const ANGLES = [
  { id: "front", name: "Front", transform: "rotateY(0deg) rotateX(0deg)" },
  { id: "three-quarter", name: "3/4", transform: "rotateY(-12deg) rotateX(1deg)" },
  { id: "side", name: "Side", transform: "rotateY(-48deg) rotateX(2deg)" },
  { id: "detail", name: "Detail", transform: "scale(1.38) translateY(9%)" },
];

function ProductVisual({
  color,
  innerSleeve,
  caseFinish = CASE_FINISHES[0],
  twistBaseFinish = TWIST_BASE_FINISHES[0],
  backdrop,
  angle,
  output,
  compact = false,
}) {
  const uid = React.useId().replace(/:/g, "");
  const leatherId = `leather-${uid}`;
  const metalId = `metal-${uid}`;
  const shadowId = `shadow-${uid}`;
  const selectedAngle = ANGLES.find((item) => item.id === angle) || ANGLES[0];
  const outputClass = output === "beauty" ? "" : `output-${output}`;

  return (
    <div
      className={`product-stage ${outputClass} ${compact ? "compact" : ""}`}
      style={{ "--bg-from": backdrop.from, "--bg-to": backdrop.to }}
    >
      <div className="studio-horizon" />
      <div className="product-orbit" style={{ transform: selectedAngle.transform }}>
        <svg viewBox="0 0 680 650" role="img" aria-label={`${color.name} lipstick`}>
          <defs>
            <linearGradient id={leatherId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor={color.light} />
              <stop offset=".28" stopColor={color.value} />
              <stop offset=".72" stopColor={color.dark} />
              <stop offset="1" stopColor={color.value} />
            </linearGradient>
            <linearGradient id={metalId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor={innerSleeve.shine} />
              <stop offset=".32" stopColor={innerSleeve.color} />
              <stop offset=".65" stopColor={innerSleeve.shadow} />
              <stop offset="1" stopColor={innerSleeve.shine} />
            </linearGradient>
            <filter id={shadowId} x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="18" />
            </filter>
            <pattern id={`grain-${uid}`} width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="7" r="1" fill="#fff" opacity=".12" />
              <circle cx="14" cy="15" r=".8" fill="#000" opacity=".16" />
            </pattern>
          </defs>

          <ellipse cx="350" cy="570" rx="176" ry="32" fill="#14110d" opacity=".3" filter={`url(#${shadowId})`} />
          <g transform="translate(-90 28) rotate(-9 220 430)" opacity=".88">
            <rect x="128" y="285" width="170" height="270" rx="22" fill={caseFinish.value} />
            <rect x="140" y="300" width="146" height="238" rx="15" fill={caseFinish.dark} />
            <path d="M150 315H276" stroke="#fff" opacity=".2" strokeWidth="4" />
          </g>
          <rect x="268" y="305" width="174" height="256" rx="20" fill={caseFinish.value} />
          <rect x="280" y="320" width="150" height="224" rx="13" fill={caseFinish.dark} />
          <path d="M292 334H415" stroke="#fff" opacity=".15" strokeWidth="5" />
          <path d="M270 525H440V541C440 552 431 561 420 561H290C279 561 270 552 270 541Z" fill={twistBaseFinish.value} />
          <path d="M287 532H423" stroke="#fff" opacity=".16" strokeWidth="4" />
          <g className="semantic-hardware">
            <rect x="263" y="284" width="184" height="67" rx="13" fill={`url(#${metalId})`} />
            <rect x="279" y="297" width="152" height="43" rx="8" fill="#171719" opacity=".68" />
          </g>
          <rect x="297" y="255" width="116" height="50" rx="10" fill="#18181a" />
          <path
            className="semantic-body bag-body"
            d="M307 258V137C307 86 337 57 382 69C404 75 415 90 415 112V258Z"
            fill={`url(#${leatherId})`}
          />
          <path d="M329 238V137C329 99 346 76 380 71" fill="none" stroke={color.light} strokeWidth="11" opacity=".3" />
          <path d="M307 258H415" stroke={color.dark} strokeWidth="5" opacity=".7" />
          <rect x="268" y="305" width="174" height="256" rx="20" fill={`url(#grain-${uid})`} opacity=".14" />
        </svg>
      </div>
      {!compact && (
        <>
          <div className="render-label">
            <span>{output === "beauty" ? "RTX PRODUCT PREVIEW / PROTOTYPE" : `${output.toUpperCase()} RENDERVAR PREVIEW`}</span>
            <strong>2048 × 2048</strong>
          </div>
          <div className="axis-widget"><i /> Y <b /> X</div>
        </>
      )}
    </div>
  );
}

function Swatch({ item, active, onClick, metal = false }) {
  return (
    <button
      className={`swatch ${active ? "active" : ""}`}
      onClick={onClick}
      aria-label={item.name}
      title={item.name}
    >
      <span style={{
        background: metal ? item.color : item.value,
      }} />
      {active && <Check size={12} />}
    </button>
  );
}

function App() {
  const [color, setColor] = useState(COLORS[0]);
  const [innerSleeve, setInnerSleeve] = useState(INNER_SLEEVE_FINISHES[0]);
  const [caseFinish, setCaseFinish] = useState(CASE_FINISHES[0]);
  const [twistBaseFinish, setTwistBaseFinish] = useState(TWIST_BASE_FINISHES[0]);
  const [backdrop, setBackdrop] = useState(BACKDROPS[0]);
  const [angle, setAngle] = useState("front");
  const [showTech, setShowTech] = useState(false);
  const [visionMode, setVisionMode] = useState("beauty");
  const [visibleSemanticClasses, setVisibleSemanticClasses] = useState(SEMANTIC_CLASSES);
  const [bridge, setBridge] = useState({ state: "connecting", live: false, fps: 0 });
  const [physics, setPhysics] = useState({
    state: "connecting",
    twist: { target: 0, position: 0 },
    cap: { active: false, state: "open" },
  });
  const [twistValue, setTwistValue] = useState(0);
  const dragRef = useRef(null);
  const physicsSeenRef = useRef(false);

  const selectedVisionView = ROBOVISION_VIEWS.find((view) => view.id === visionMode) || ROBOVISION_VIEWS[0];

  const sendControl = async (payload) => {
    try {
      await fetch("/api/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch {
      // The SVG preview remains usable while the local GPU bridge is offline.
    }
  };

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const response = await fetch("/api/status", { cache: "no-store" });
        const status = await response.json();
        if (!active) return;
        setBridge({
          state: status.runtime?.state || "idle",
          live: Boolean(status.live),
          fps: status.runtime?.fps || 0,
          gpu: status.gpu?.name,
          error: status.runtime?.error,
          frame: status.runtime?.frame_index || 0,
          robovision: status.robovision,
        });
        if (status.runtime?.state === "idle" || status.runtime?.state === "stopped") {
          await fetch("/api/render/start", { method: "POST" });
        }
      } catch {
        if (active) setBridge({ state: "offline", live: false, fps: 0 });
      }
    };
    refresh();
    const timer = window.setInterval(refresh, 1500);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    let active = true;
    const refreshPhysics = async () => {
      try {
        const response = await fetch("/physics/api/status", {
          cache: "no-store",
        });
        const status = await response.json();
        if (!active) return;
        setPhysics(status);
        if (!physicsSeenRef.current && status.state === "running") {
          setTwistValue((status.twist?.target || 0) * 360);
          physicsSeenRef.current = true;
        }
        await sendControl({
          action: "physics",
          available: status.state === "running",
          twist_position: status.twist?.position || 0,
          twist_angle_degrees: status.twist?.angle_degrees || 0,
          carrier_height: status.mechanism?.carrier_height_cm || 0,
          cap_active: Boolean(status.cap?.active),
          cap_position: status.cap?.position,
          cap_state: status.cap?.state,
        });
      } catch {
        if (active) {
          setPhysics({
            state: "offline",
            twist: { target: 0, position: 0 },
            cap: { active: false, state: "open" },
          });
        }
      }
    };
    refreshPhysics();
    const timer = window.setInterval(refreshPhysics, 100);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    sendControl({
      action: "material",
      color: color.id,
      inner_sleeve: innerSleeve.id,
      case: caseFinish.id,
      twist_base: twistBaseFinish.id,
      backdrop: backdrop.id,
    });
  }, [color.id, innerSleeve.id, caseFinish.id, twistBaseFinish.id, backdrop.id]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.target.closest("input, textarea, select")) return;
      const key = event.key.toLowerCase();
      const moves = {
        w: { z: -0.28 },
        s: { z: 0.28 },
        a: { x: -0.28 },
        d: { x: 0.28 },
        q: { y: -0.2 },
        e: { y: 0.2 },
      };
      if (moves[key]) {
        event.preventDefault();
        sendControl({ action: "move", ...moves[key] });
      } else if (event.code === "Space") {
        event.preventDefault();
        sendControl({ action: "toggle_auto_spin" });
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const chooseAngle = (id) => {
    const presets = {
      front: { x: 0, y: 4, z: 0, distance: 28, yaw: 0, pitch: 0.04 },
      "three-quarter": { x: 0, y: 4, z: 0, distance: 28, yaw: 0.55, pitch: 0.06 },
      side: { x: 0, y: 4, z: 0, distance: 25, yaw: 1.3, pitch: 0.04 },
      detail: { x: 0, y: 5.8, z: 0, distance: 15, yaw: 0.38, pitch: 0.03 },
    };
    setAngle(id);
    sendControl({
      action: "focus",
      ...presets[id],
      object_angle: 0,
      auto_spin: false,
    });
  };

  const setTwist = (degrees) => {
    const next = Number(degrees);
    setTwistValue(next);
    fetch("/physics/api/twist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: next / 360 }),
    }).catch(() => {});
  };

  const capAction = (action) => {
    if (action === "drop") {
      fetch("/physics/api/cap/drop", { method: "POST" }).catch(() => {});
      return;
    }
    fetch("/physics/api/cap/open", { method: "POST" }).catch(() => {});
  };

  const setSemanticVisibility = (nextClasses) => {
    setVisibleSemanticClasses(nextClasses);
    sendControl({
      action: "semantic_visibility",
      visible_classes: nextClasses,
    });
  };

  const toggleSemanticClass = (label) => {
    const nextClasses = visibleSemanticClasses.includes(label)
      ? visibleSemanticClasses.filter((item) => item !== label)
      : [...visibleSemanticClasses, label];
    setSemanticVisibility(nextClasses);
  };

  const onPointerDown = (event) => {
    if (event.target.closest("button, a")) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY };
  };

  const onPointerMove = (event) => {
    if (!dragRef.current) return;
    const dx = event.clientX - dragRef.current.x;
    const dy = event.clientY - dragRef.current.y;
    dragRef.current = { x: event.clientX, y: event.clientY };
    if (Math.abs(dx) + Math.abs(dy) > 1) {
      sendControl({ action: "orbit", dx, dy });
    }
  };

  const capClosed = Boolean(physics.cap?.active);
  const fullyRetracted =
    (physics.twist?.position || 0) <= 0.03
    && (physics.twist?.target || 0) <= 0.03;
  const interactionHint = capClosed
    ? "Open the cap to unlock the twist mechanism."
    : fullyRetracted
    ? "Cap is open and lipstick is retracted. Twist outward or close the cap."
    : "Twist completely inward to 0° before closing the cap.";

  return (
    <main>
      <header>
        <a className="brand" href="#">
          <span className="brand-gem"><Sparkles size={16} /></span>
          <span>OMNIGLAM <b>RTX</b></span>
        </a>
        <div className="project-tag">PRODUCT STUDIO / 01</div>
        <div className="header-actions">
          <button className="text-button" onClick={() => setShowTech(!showTech)}>
            Pipeline <ChevronDown size={14} />
          </button>
          <div className={`gpu-state ${bridge.live ? "live" : ""}`} title={bridge.error || "RTX render status"}>
            <i /> {bridge.live ? `RTX LIVE · ${bridge.fps.toFixed(1)} FPS` : bridge.state.replace("-", " ").toUpperCase()}
          </div>
        </div>
      </header>

      {showTech && (
        <section className="tech-drawer">
          <div>
            <Layers3 size={18} />
            <span>01 / OPENUSD</span>
            <strong>Product, camera, lights & materials</strong>
            <small>/World/Product · referenced lipstick.usd</small>
          </div>
          <em />
          <div>
            <Box size={18} />
            <span>02 / OVSTAGE</span>
            <strong>Ordinal scene updates</strong>
            <small>material:binding · omni:xform</small>
          </div>
          <em />
          <div>
            <Sparkles size={18} />
            <span>03 / OVRTX</span>
            <strong>RTX RenderProduct outputs</strong>
            <small>LdrColor · Depth · Semantic · Normal</small>
          </div>
          <em />
          <div>
            <Download size={18} />
            <span>04 / YOUR APP</span>
            <strong>PNG + deterministic JSON</strong>
            <small>No Isaac Sim · No Replicator</small>
          </div>
        </section>
      )}

      <section className="studio">
        <div className="viewport-column">
          <div className="viewport-top">
            <div>
              <span className="kicker">LIVE CONFIGURATION</span>
              <h1>Lipstick <em>01</em></h1>
            </div>
            <div className="view-actions">
              <button title="Reset live camera" onClick={() => {
                setAngle("front");
                sendControl({ action: "reset" });
              }}><Rotate3d size={17} /></button>
              <span>USD / <b>/World/Product</b></span>
            </div>
          </div>

          <div className="robovision-bar">
            <span><ScanLine size={13} /> ROBOVISION</span>
            {ROBOVISION_VIEWS.map((view) => (
              <button
                key={view.id}
                className={visionMode === view.id ? "active" : ""}
                title={view.name}
                onClick={() => setVisionMode(view.id)}
              >
                {view.name}
              </button>
            ))}
            <em>{bridge.robovision?.point_count || 0} PTS</em>
          </div>
          <div className="vision-purpose">
            <b>{selectedVisionView.name}</b>
            <span>{selectedVisionView.purpose}</span>
          </div>

          <div
            className={`viewport ${bridge.live ? "gpu-live" : ""}`}
            tabIndex="0"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={() => { dragRef.current = null; }}
            onPointerCancel={() => { dragRef.current = null; }}
            onWheel={(event) => sendControl({ action: "zoom", delta: event.deltaY })}
          >
            <ProductVisual color={color} innerSleeve={innerSleeve} caseFinish={caseFinish} twistBaseFinish={twistBaseFinish} backdrop={backdrop} angle={angle} output="beauty" />
            {bridge.live && (
              <div className="gpu-stream">
                <img
                  src={
                    visionMode === "beauty"
                      ? "/api/stream.mjpg"
                      : `/api/view/${visionMode === "affordance" ? "semantic" : visionMode}.jpg?frame=${bridge.frame || 0}`
                  }
                  alt={`RoboVision ${visionMode} view of the lipstick`}
                />
                {visionMode === "affordance" && (
                  <div className="affordance-overlay">
                    <b>ROBOT ACTION MAP</b>
                    <span className="grasp">CAP · GRASP / OPEN</span>
                    <span className="support">CASING · SUPPORT</span>
                    <span className="rotate">BASE · {capClosed ? "LOCKED" : "ROTATE"}</span>
                    <span className="avoid">BULLET · AVOID CONTACT</span>
                  </div>
                )}
                {visionMode === "semantic" && (
                  <div className="semantic-overlay">
                    <b>OPENUSD SEMANTIC LABELS</b>
                    <div>
                      {(bridge.robovision?.semantic_classes || []).map((label, index) => (
                        <button
                          key={label}
                          className={visibleSemanticClasses.includes(label) ? "visible" : "hidden"}
                          onClick={() => toggleSemanticClass(label)}
                          aria-pressed={visibleSemanticClasses.includes(label)}
                          title={`${visibleSemanticClasses.includes(label) ? "Hide" : "Show"} ${label.replaceAll("_", " ")}`}
                        >
                          <i style={{ "--semantic-color": SEMANTIC_COLORS[index % SEMANTIC_COLORS.length] }} />
                          {label.replaceAll("_", " ")}
                        </button>
                      ))}
                    </div>
                    <small>Click a class to include or exclude its pixels.</small>
                  </div>
                )}
                {visionMode === "depth" && (
                  <div className="depth-legend">
                    <b>CAMERA DEPTH</b>
                    <div className="depth-gradient" />
                    <div className="depth-scale">
                      <span>NEAR</span>
                      <span>MID</span>
                      <span>FAR</span>
                    </div>
                    <small><i /> BLACK · INVALID / NO RETURN</small>
                    <p>Relative range · rescales with the visible scene</p>
                  </div>
                )}
                {visionMode === "normals" && (
                  <div className="normal-legend">
                    <b>SURFACE NORMAL DIRECTION</b>
                    <div className="normal-axes">
                      <span className="axis-x"><i /> RED · X · LEFT / RIGHT</span>
                      <span className="axis-y"><i /> GREEN · Y · DOWN / UP</span>
                      <span className="axis-z"><i /> BLUE · Z · AWAY / TOWARD</span>
                    </div>
                    <div className="normal-range">
                      <span>− DIRECTION</span>
                      <span>ZERO</span>
                      <span>+ DIRECTION</span>
                    </div>
                    <p>Each pixel’s RGB mix encodes its outward-facing 3D direction.</p>
                  </div>
                )}
                <span><i /> {visionMode.toUpperCase()} · OVRTX · RTX LIVE</span>
              </div>
            )}
            <div className="control-hint">
              <span>DRAG orbit</span><span>SCROLL zoom</span><span>WASD move</span><span>Q/E height</span><span>SPACE turntable</span>
            </div>
            <div className="view-presets">
              {ANGLES.map((item) => (
                <button key={item.id} className={angle === item.id ? "active" : ""} onClick={() => chooseAngle(item.id)}>
                  <span className={`angle-icon ${item.id}`} />
                  {item.name}
                </button>
              ))}
            </div>
          </div>

        </div>

        <aside className="configurator">
          <div className="panel-heading">
            <span className="kicker">PRODUCT CONFIGURATOR</span>
            <small>USD STAGE / READY</small>
          </div>

          <div className="field material-field">
            <div className="field-title"><span>01 &nbsp; SHADES</span><strong>{color.name}</strong></div>
            <div className="swatches shade-swatches">
              {COLORS.map((item) => <Swatch key={item.id} item={item} active={color.id === item.id} onClick={() => setColor(item)} />)}
            </div>
            <small className="attribute">live MDL shade → {color.name} · {color.value}</small>
          </div>

          <div className="field material-field">
            <div className="field-title"><span>02 &nbsp; INNER SLEEVE</span><strong>{innerSleeve.name}</strong></div>
            <div className="swatches">
              {INNER_SLEEVE_FINISHES.map((item) => <Swatch key={item.id} item={item} metal active={innerSleeve.id === item.id} onClick={() => setInnerSleeve(item)} />)}
            </div>
          </div>

          <div className="field material-field">
            <div className="field-title"><span>03 &nbsp; TWIST BASE</span><strong>{twistBaseFinish.name}</strong></div>
            <div className="swatches">
              {TWIST_BASE_FINISHES.map((item) => <Swatch key={item.id} item={item} active={twistBaseFinish.id === item.id} onClick={() => setTwistBaseFinish(item)} />)}
            </div>
            <small className="attribute">twist base only · metallic {twistBaseFinish.metallic.toFixed(1)} · roughness {twistBaseFinish.roughness.toFixed(2)}</small>
          </div>

          <div className="field material-field">
            <div className="field-title"><span>04 &nbsp; CASE BODY</span><strong>{caseFinish.name}</strong></div>
            <div className="swatches">
              {CASE_FINISHES.map((item) => <Swatch key={item.id} item={item} active={caseFinish.id === item.id} onClick={() => setCaseFinish(item)} />)}
            </div>
            <small className="attribute">outer case only · metallic {caseFinish.metallic.toFixed(1)} · roughness {caseFinish.roughness.toFixed(2)}</small>
          </div>

          <div className="field physics-field">
            <div className="field-title">
              <span>05 &nbsp; O V P H Y S X</span>
              <strong className={`physics-state ${physics.state === "running" ? "live" : ""}`}>
                {physics.state}
              </strong>
            </div>
            <div className="physics-control">
              <div>
                <label htmlFor="twist-control">Twist base rotation</label>
                <output>{Math.round(physics.twist?.angle_degrees || 0)}°</output>
              </div>
              <input
                id="twist-control"
                type="range"
                min="0"
                max="360"
                step="1"
                value={twistValue}
                disabled={physics.state !== "running" || Boolean(physics.cap?.active)}
                title={capClosed ? "Open the cap before twisting" : "Rotate the twist base"}
                onChange={(event) => setTwist(event.target.value)}
              />
            </div>
            <div className="mechanism-readout">
              <span><i /> case + base {physics.twist?.direction || "holding"}</span>
              <span><i /> inner sleeve fixed</span>
              <span><i /> carrier {(physics.mechanism?.carrier_height_cm || 0).toFixed(2)} cm</span>
            </div>
            <div className="cap-actions">
              {capClosed ? (
                <button
                  className="cap-primary"
                  disabled={physics.state !== "running"}
                  onClick={() => capAction("open")}
                >
                  <Unlock size={14} /> Open cap
                </button>
              ) : (
                <button
                  className="cap-primary"
                  disabled={physics.state !== "running" || !fullyRetracted}
                  title={!fullyRetracted ? "Twist completely inward to 0° before closing" : "Close cap"}
                  onClick={() => capAction("drop")}
                >
                  <Lock size={14} /> Close cap
                </button>
              )}
              <span className={capClosed ? "closed" : "open"}>
                Cap {physics.cap?.state || "offline"}
              </span>
            </div>
            <div className={`interaction-hint ${capClosed ? "locked" : fullyRetracted ? "ready" : ""}`}>
              <b>{capClosed ? "NEXT: OPEN CAP" : fullyRetracted ? "READY" : "NEXT: RETRACT"}</b>
              <span>{interactionHint}</span>
            </div>
          </div>

          <div className="field environment-field">
            <div className="field-title"><span>06 &nbsp; ENVIRONMENT</span><strong>{backdrop.name}</strong></div>
            <div className="backdrops">
              {BACKDROPS.map((item) => (
                <button
                  key={item.id}
                  className={backdrop.id === item.id ? "active" : ""}
                  onClick={() => setBackdrop(item)}
                  style={{ background: `linear-gradient(135deg, ${item.from}, ${item.to})` }}
                  title={item.name}
                >
                  {backdrop.id === item.id && <Check size={12} />}
                </button>
              ))}
            </div>
          </div>

          <div className="render-summary">
            <div><span>Render mode</span><strong>RTX live</strong></div>
            <div><span>Scene updates</span><strong>ovstage</strong></div>
            <div><span>Output</span><strong>LdrColor</strong></div>
          </div>
          <div className={`live-change-note ${bridge.live ? "active" : ""}`}>
            <i /> {bridge.live ? "Changes apply directly to the live USD stage." : "Waiting for the local ovrtx bridge."}
          </div>
        </aside>
      </section>

    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
