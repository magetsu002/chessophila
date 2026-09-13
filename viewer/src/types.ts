export type Side = "left" | "right";

export interface BoutTelemetry {
  left: string;
  right: string;
  left_fen: string;
  right_fen: string;
  dna02_left_spikes: number;
  dna02_right_spikes: number;
  selected_side: Side | null;
  selected_move: string | null;
  seed: number;
  active_neurons: number;
  total_spikes: number;
}

export interface ReplayTelemetry {
  schema_version: number;
  source: "real-connectome";
  simulator: {
    name: string;
    commit: string;
    flywire_materialization: number;
    codegen: string;
  };
  experiment: {
    a: string;
    b: string;
    best_of: number;
    duration_ms: number;
    seed: number;
  };
  winner: string;
  bouts: BoutTelemetry[];
}
