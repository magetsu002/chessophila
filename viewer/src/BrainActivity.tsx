import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import {
  BufferAttribute,
  BufferGeometry,
  Group,
  InstancedMesh,
  LineBasicMaterial,
  MeshStandardMaterial,
  Object3D,
  PointLight,
  SphereGeometry,
} from "three";

function noise(seed: number) {
  const value = Math.sin(seed * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

export function BrainActivity({ activity, motionKey }: { activity: number; motionKey: number }) {
  const mesh = useRef<InstancedMesh>(null);
  const group = useRef<Group>(null);
  const light = useRef<PointLight>(null);
  const burstStart = useRef(performance.now());
  const { invalidate } = useThree();
  const nodes = useMemo(
    () => Array.from({ length: 30 }, (_, i) => {
      const theta = noise(i + 1) * Math.PI * 2;
      const phi = Math.acos(2 * noise(i + 41) - 1);
      const radius = 0.18 + noise(i + 81) * 0.42;
      return [
        Math.sin(phi) * Math.cos(theta) * radius * 1.25,
        Math.cos(phi) * radius * 0.72,
        Math.sin(phi) * Math.sin(theta) * radius,
      ] as [number, number, number];
    }),
    [],
  );
  const lineGeometry = useMemo(() => {
    const positions: number[] = [];
    for (let i = 0; i < 24; i += 1) {
      const a = nodes[i];
      const b = nodes[(i * 7 + 9) % nodes.length];
      positions.push(...a, ...b);
    }
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(new Float32Array(positions), 3));
    return geometry;
  }, [nodes]);

  const nodeGeometry = useMemo(() => new SphereGeometry(0.025, 8, 6), []);
  const nodeMaterial = useMemo(
    () => new MeshStandardMaterial({
      color: "#6ef6d4",
      emissive: "#2a8d7c",
      emissiveIntensity: 0.35 + activity * 1.4,
      roughness: 0.25,
    }),
    [activity],
  );
  const lineMaterial = useMemo(
    () => new LineBasicMaterial({
      color: "#3e8f88",
      transparent: true,
      opacity: 0.08 + activity * 0.18,
    }),
    [activity],
  );
  useEffect(() => {
    burstStart.current = performance.now();
    invalidate();
  }, [motionKey, activity, invalidate]);

  useFrame(() => {
    const age = (performance.now() - burstStart.current) / 1000;
    if (age > 1.65) return;
    const pulse = 1 + Math.sin(age * 12) * 0.045 * (1 - age / 1.65);
    if (group.current) {
      group.current.rotation.y = Math.sin(age * 2.6) * 0.16;
      group.current.scale.setScalar(1.18 * pulse);
    }
    if (light.current) {
      light.current.intensity = 0.12 + activity * 1.2 + Math.max(0, Math.sin(age * 15)) * 0.6;
    }
    invalidate();
  });

  useEffect(() => {
    const instance = mesh.current;
    if (!instance) return;
    const dummy = new Object3D();
    nodes.forEach((position, index) => {
      dummy.position.set(...position);
      const scale = 0.8 + noise(index + 160) * 0.9 + activity * 0.35;
      dummy.scale.setScalar(scale);
      dummy.updateMatrix();
      instance.setMatrixAt(index, dummy.matrix);
    });
    instance.instanceMatrix.needsUpdate = true;
  }, [nodes, activity]);

  useEffect(() => () => {
    lineGeometry.dispose();
    nodeGeometry.dispose();
    nodeMaterial.dispose();
    lineMaterial.dispose();
  }, [lineGeometry, lineMaterial, nodeGeometry, nodeMaterial]);

  return (
    <group ref={group} position={[0, 2.18, -1.15]} scale={1.18}>
      <lineSegments geometry={lineGeometry} material={lineMaterial} />
      <instancedMesh
        ref={mesh}
        args={[nodeGeometry, nodeMaterial, nodes.length]}
        frustumCulled
      />
      <pointLight ref={light} intensity={0.12 + activity * 1.2} distance={2.5} color="#74ffe0" />
    </group>
  );
}
