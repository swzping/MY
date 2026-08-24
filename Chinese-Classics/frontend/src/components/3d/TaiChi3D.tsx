import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface TaiChi3DProps {
  position?: [number, number, number];
  rotationSpeed?: number;
  scale?: number;
}

export const TaiChi3D: React.FC<TaiChi3DProps> = ({
  position = [0, 0, 0],
  rotationSpeed = 0.005,
  scale = 1,
}) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += rotationSpeed;
    }
  });

  // 创建太极图的几何形状
  const taiChiGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    const radius = 2;

    // 外圆
    shape.absarc(0, 0, radius, 0, Math.PI * 2, false);

    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: 0.2,
      bevelEnabled: true,
      bevelThickness: 0.05,
      bevelSize: 0.05,
      bevelSegments: 5,
    });

    return geometry;
  }, []);



  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* 底座圆盘 */}
      <mesh geometry={taiChiGeometry} rotation={[-Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color="#2C2C2C"
          metalness={0.8}
          roughness={0.2}
          emissive="#1a1a1a"
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* 太极主体 - 阴（黑） */}
      <mesh position={[0, 0.15, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[1.9, 64]} />
        <meshStandardMaterial
          color="#0a0a0a"
          metalness={0.6}
          roughness={0.4}
        />
      </mesh>

      {/* 太极主体 - 阳（白） */}
      <mesh position={[0, 0.16, 0]} rotation={[-Math.PI / 2, Math.PI, 0]}>
        <circleGeometry args={[1.9, 64, 0, Math.PI]} />
        <meshStandardMaterial
          color="#f5f5f5"
          metalness={0.6}
          roughness={0.4}
        />
      </mesh>

      {/* S曲线分割 */}
      <mesh position={[0, 0.17, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.95, 0.02, 8, 64, Math.PI]} />
        <meshStandardMaterial color="#C41E3A" metalness={0.9} roughness={0.1} />
      </mesh>

      {/* 阳眼（黑点） */}
      <mesh position={[0, 0.18, 0.95]}>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial
          color="#0a0a0a"
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* 阴眼（白点） */}
      <mesh position={[0, 0.18, -0.95]}>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial
          color="#f5f5f5"
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* 装饰光环 */}
      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.1, 2.2, 64]} />
        <meshStandardMaterial
          color="#FFD700"
          metalness={1}
          roughness={0.1}
          emissive="#FFD700"
          emissiveIntensity={0.3}
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  );
};

export default TaiChi3D;
