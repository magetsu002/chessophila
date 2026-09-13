import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";

import { BrainActivity } from "./BrainActivity";
import { ChessBoard3D } from "./ChessBoard";
import { Fly } from "./Fly";
import type { BoutTelemetry } from "./types";

export function LabScene({ bout }: { bout: BoutTelemetry }) {
  const activity = Math.min(1, bout.total_spikes / 2600);
  return (
    <Canvas
      frameloop="demand"
      dpr={[1, 1.35]}
      camera={{ position: [0, 5.7, 9.2], fov: 42 }}
      gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
    >
      <color attach="background" args={["#06080b"]} />
      <fog attach="fog" args={["#06080b", 10, 22]} />
      <ambientLight intensity={0.72} />
      <directionalLight position={[1.5, 7, 5]} intensity={1.75} />
      <pointLight position={[-5, 1, 2]} intensity={0.75} color="#57a3ff" />
      <pointLight position={[5, 1, 2]} intensity={0.75} color="#e6a65f" />

      <ChessBoard3D
        fen={bout.left_fen}
        move={bout.left}
        side="left"
        selected={bout.selected_side === "left"}
      />
      <ChessBoard3D
        fen={bout.right_fen}
        move={bout.right}
        side="right"
        selected={bout.selected_side === "right"}
      />
      <Fly selectedSide={bout.selected_side} activity={activity} motionKey={bout.seed} />
      <BrainActivity activity={activity} motionKey={bout.seed} />

      <mesh position={[0, -0.78, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[22, 16]} />
        <meshStandardMaterial color="#0b1016" roughness={0.86} metalness={0.04} />
      </mesh>

      <OrbitControls
        makeDefault
        enableDamping={false}
        enablePan={false}
        minDistance={7.5}
        maxDistance={13}
        minPolarAngle={0.75}
        maxPolarAngle={1.35}
        target={[0, 0.4, 0]}
      />
    </Canvas>
  );
}
