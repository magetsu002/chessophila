import { useEffect, useMemo, useState } from "react";

import { LabScene } from "./Scene";
import type { ReplayTelemetry } from "./types";

const replayUrl = "/replays/real-e4-d4.json";

export default function App() {
  const [replay, setReplay] = useState<ReplayTelemetry | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(replayUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`replay HTTP ${response.status}`);
        return response.json();
      })
      .then((data: ReplayTelemetry) => setReplay(data))
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  useEffect(() => {
    if (!playing || !replay || replay.bouts.length < 2) return;
    const timer = window.setInterval(
      () => setIndex((current) => (current + 1) % replay.bouts.length),
      4200,
    );
    return () => window.clearInterval(timer);
  }, [playing, replay]);

  const bout = replay?.bouts[index];
  const decisive = useMemo(() => replay?.bouts.filter((item) => item.selected_move) ?? [], [replay]);

  if (error) return <div className="fatal">Unable to load real replay: {error}</div>;
  if (!replay || !bout) return <div className="fatal">Loading connectome replay…</div>;
  const label = bout.selected_side
    ? `${bout.selected_side.toUpperCase()} → ${bout.selected_move}`
    : "NO DECISIVE RESPONSE";

  return (
    <main className="app-shell">
      <div className="scene-wrap">
        <LabScene bout={bout} />
      </div>

      <header className="brand-block">
        <div className="brand-kicker">CONNECTOME CHESS</div>
        <h1>CHESSOPHILA</h1>
      </header>

      <div className="run-state" aria-label="Replay source">
        <span className="run-dot" />
        <span>REAL REPLAY</span>
        <span className="run-separator">·</span>
        <span>FlyWire v{replay.simulator.flywire_materialization}</span>
      </div>

      <section className="bout-card glass">
        <div className="bout-card-head">
          <span>BOUT {index + 1} / {replay.bouts.length}</span>
          <strong className={bout.selected_side ? "decision" : "neutral"}>{label}</strong>
        </div>
        <div className="duel-row">
          <div>
            <small>LEFT</small>
            <strong>{bout.left}</strong>
          </div>
          <span className="versus">vs</span>
          <div className="align-right">
            <small>RIGHT</small>
            <strong>{bout.right}</strong>
          </div>
        </div>
        <div className="steer-meter">
          <div
            className="steer-fill left"
            style={{ flex: Math.max(1, bout.dna02_left_spikes) }}
          />
          <div
            className="steer-fill right"
            style={{ flex: Math.max(1, bout.dna02_right_spikes) }}
          />
        </div>
        <div className="steer-labels">
          <span>DNa02-L {bout.dna02_left_spikes}</span>
          <span>DNa02-R {bout.dna02_right_spikes}</span>
        </div>
      </section>
      <section className="stats-card glass">
        <div className="stat">
          <span>ACTIVE NEURONS</span>
          <strong>{bout.active_neurons.toLocaleString()}</strong>
        </div>
        <div className="stat">
          <span>TOTAL SPIKES</span>
          <strong>{bout.total_spikes.toLocaleString()}</strong>
        </div>
        <div className="stat">
          <span>DECISIVE</span>
          <strong>{decisive.length}/{replay.bouts.length}</strong>
        </div>
        <div className="stat">
          <span>WINNER</span>
          <strong>{replay.winner}</strong>
        </div>
      </section>

      <footer className="timeline glass">
        <button
          type="button"
          aria-label="Previous bout"
          onClick={() => setIndex((index - 1 + replay.bouts.length) % replay.bouts.length)}
        >
          ‹
        </button>
        <button type="button" className="play" onClick={() => setPlaying((value) => !value)}>
          {playing ? "PAUSE" : "PLAY"}
        </button>
        <div className="ticks">
          {replay.bouts.map((item, boutIndex) => (
            <button
              key={item.seed}
              type="button"
              className={`tick ${boutIndex === index ? "active" : ""} ${item.selected_move ? "decisive" : ""}`}
              onClick={() => setIndex(boutIndex)}
              aria-label={`Bout ${boutIndex + 1}`}
            />
          ))}
        </div>
        <button
          type="button"
          aria-label="Next bout"
          onClick={() => setIndex((index + 1) % replay.bouts.length)}
        >
          ›
        </button>
      </footer>

    </main>
  );
}
