import { Html, useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import { Mesh, MeshStandardMaterial, type Object3D } from "three";

interface PieceSpec {
  code: string;
  file: number;
  rank: number;
}

const CHESS_URL = "/models/a-beautiful-game.glb";
const MODEL_SCALE = 5.4;
const SQUARE = 0.0625;

const IVORY = new MeshStandardMaterial({
  color: "#d8d3c7",
  roughness: 0.42,
  metalness: 0.08,
});
const OBSIDIAN = new MeshStandardMaterial({
  color: "#171a1f",
  roughness: 0.3,
  metalness: 0.18,
});
function parseFen(fen: string): PieceSpec[] {
  const rows = fen.split(" ")[0].split("/");
  const pieces: PieceSpec[] = [];
  rows.forEach((row, rowIndex) => {
    let file = 0;
    for (const token of row) {
      if (/\d/.test(token)) file += Number(token);
      else {
        pieces.push({ code: token, file, rank: 7 - rowIndex });
        file += 1;
      }
    }
  });
  return pieces;
}

function sourceName(code: string): string {
  switch (code) {
    case "P": return "Pawn_Body_W1";
    case "p": return "Pawn_Body_B1";
    case "R": return "Castle_W1";
    case "r": return "Castle_B1";
    case "N": return "Knight_W1";
    case "n": return "Knight_B1";
    case "B": return "Bishop_W1";
    case "b": return "Bishop_B1";
    case "Q": return "Queen_W";
    case "q": return "Queen_B";
    case "K": return "King_W";
    case "k": return "King_B";
    default: throw new Error(`unsupported piece code: ${code}`);
  }
}
function preparePiece(object: Object3D, material: MeshStandardMaterial): Object3D {
  const clone = object.clone(true);
  clone.traverse((child) => {
    child.frustumCulled = true;
    if (child instanceof Mesh) {
      child.castShadow = false;
      child.receiveShadow = false;
      child.material = material;
    }
  });
  return clone;
}

function prepareBoard(object: Object3D): Object3D {
  const clone = object.clone(true);
  clone.traverse((child) => {
    child.frustumCulled = true;
    if (child instanceof Mesh) {
      child.castShadow = false;
      child.receiveShadow = false;
    }
  });
  return clone;
}

function RealPiece({ code, file, rank }: PieceSpec) {
  const { scene } = useGLTF(CHESS_URL);
  const { piece, anchor } = useMemo(() => {
    const source = scene.getObjectByName(sourceName(code));
    if (!source) throw new Error(`missing chess asset node: ${sourceName(code)}`);
    return {
      piece: preparePiece(source, code === code.toUpperCase() ? IVORY : OBSIDIAN),
      anchor: source.position.clone(),
    };
  }, [scene, code]);

  const targetX = (file - 3.5) * SQUARE;
  const targetZ = (rank - 3.5) * SQUARE;
  return (
    <group position={[targetX - anchor.x, 0, targetZ - anchor.z]}>
      <primitive object={piece} />
    </group>
  );
}
function RealBoard() {
  const { scene } = useGLTF(CHESS_URL);
  const board = useMemo(() => {
    const source = scene.getObjectByName("Chessboard");
    if (!source) throw new Error("missing Chessboard node in A Beautiful Game asset");
    return prepareBoard(source);
  }, [scene]);
  return <primitive object={board} />;
}

interface ChessBoard3DProps {
  fen: string;
  move: string;
  selected: boolean;
  side: "left" | "right";
}

export function ChessBoard3D({ fen, move, selected, side }: ChessBoard3DProps) {
  const pieces = useMemo(() => parseFen(fen), [fen]);
  const xOffset = side === "left" ? -3.25 : 3.25;
  return (
    <group
      position={[xOffset, -0.7, 0]}
      rotation={[0.08, side === "left" ? 0.05 : -0.05, 0]}
    >
      <group scale={MODEL_SCALE}>
        <RealBoard />
        {pieces.map((piece) => (
          <RealPiece
            key={`${piece.code}-${piece.file}-${piece.rank}`}
            code={piece.code}
            file={piece.file}
            rank={piece.rank}
          />
        ))}
      </group>
      {selected && (
        <pointLight position={[0, 1.05, 0]} intensity={1.1} distance={3.2} color="#64ffd6" />
      )}
      <Html center position={[0, 0.95, -2.15]} transform distanceFactor={7}>
        <div className={`board-label ${selected ? "selected" : ""}`}>
          <span>{side.toUpperCase()}</span>
          <strong>{move}</strong>
        </div>
      </Html>
    </group>
  );
}

useGLTF.preload(CHESS_URL);
