import { useGLTF } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import { Group, type Object3D, Vector3 } from "three";

import type { Side } from "./types";

interface FlyProps {
  selectedSide: Side | null;
  activity: number;
  motionKey: number;
}

interface FlyRig {
  model: Object3D;
  leftWing: Group;
  rightWing: Group;
}

const FLYBODY_URL = "/models/flybody-neutral.glb";

function addWingPivot(root: Object3D, names: string[], pivotAt: [number, number, number]) {
  const pivot = new Group();
  const offset = new Vector3(...pivotAt);
  pivot.position.copy(offset);
  for (const name of names) {
    const wing = root.getObjectByName(name);
    if (!wing) continue;
    wing.parent?.remove(wing);
    wing.position.sub(offset);
    pivot.add(wing);
  }
  root.add(pivot);
  return pivot;
}
function prepareRig(source: Group): FlyRig {
  const clone = source.clone(true);
  clone.traverse((child) => {
    child.frustumCulled = true;
    if ("isMesh" in child && child.isMesh) {
      child.castShadow = false;
      child.receiveShadow = false;
    }
  });
  const leftWing = addWingPivot(
    clone,
    ["wing_left_brown", "wing_left_membrane"],
    [-0.0069, 0.043, 0.048],
  );
  const rightWing = addWingPivot(
    clone,
    ["wing_right_brown", "wing_right_membrane"],
    [-0.0069, -0.043, 0.048],
  );
  return { model: clone, leftWing, rightWing };
}

export function Fly({ selectedSide, activity, motionKey }: FlyProps) {
  const motion = useRef<Group>(null);
  const burstStart = useRef(performance.now());
  const { scene } = useGLTF(FLYBODY_URL);
  const { invalidate } = useThree();
  const rig = useMemo(() => prepareRig(scene), [scene]);

  useEffect(() => {
    burstStart.current = performance.now();
    invalidate();
  }, [motionKey, selectedSide, activity, invalidate]);
  useFrame((_, delta) => {
    const group = motion.current;
    if (!group) return;

    const age = (performance.now() - burstStart.current) / 1000;
    const side = selectedSide === "left" ? -1 : selectedSide === "right" ? 1 : 0;
    const choosing = age > 0.38 && side !== 0;
    const indecision = side === 0 && age < 1.65 ? Math.sin(age * 6.5) : 0;
    const targetX = choosing ? side * 0.82 : indecision * 0.28;
    const targetZ = choosing ? 0.22 : 0.05;
    const targetYaw = choosing ? -side * 0.46 : -indecision * 0.16;
    const targetBank = choosing ? -side * 0.12 : -indecision * 0.045;
    const hover = age < 1.9 ? Math.sin(age * 11) * 0.035 : 0;
    const lerp = Math.min(1, delta * 4.8);

    group.position.x += (targetX - group.position.x) * lerp;
    group.position.z += (targetZ - group.position.z) * lerp;
    group.position.y += (0.22 + hover - group.position.y) * lerp;
    group.rotation.y += (targetYaw - group.rotation.y) * lerp;
    group.rotation.z += (targetBank - group.rotation.z) * lerp;

    const flapAmount = age < 1.7 ? 0.48 * (1 - age / 2.2) : 0.025;
    const flap = Math.sin(age * 58) * flapAmount;
    rig.leftWing.rotation.x = flap;
    rig.rightWing.rotation.x = -flap;

    const unsettled =
      Math.abs(group.position.x - targetX) > 0.004 ||
      Math.abs(group.rotation.y - targetYaw) > 0.004 ||
      Math.abs(group.rotation.z - targetBank) > 0.004;
    if (age < 1.95 || unsettled) invalidate();
  });

  return (
    <group ref={motion} position={[0, 0.22, 0.05]}>
      <group rotation={[0, Math.PI / 2, 0]}>
        <primitive object={rig.model} rotation={[-Math.PI / 2, 0, 0]} scale={3.7} />
      </group>
      <pointLight
        position={[0, 0.3, 0.1]}
        intensity={0.08 + activity * 0.55}
        distance={2}
        color="#9fffe7"
      />
    </group>
  );
}

useGLTF.preload(FLYBODY_URL);
