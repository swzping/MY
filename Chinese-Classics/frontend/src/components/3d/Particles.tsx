import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ParticlesProps {
  count?: number;
  radius?: number;
}

export const Particles: React.FC<ParticlesProps> = ({
  count = 200,
  radius = 15,
}) => {
  const pointsRef = useRef<THREE.Points>(null);

  // 粒子位置数据
  const { positions, colors } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const colorPalette = [
      new THREE.Color('#FFD700'), // 金色
      new THREE.Color('#C41E3A'), // 深红
      new THREE.Color('#FFA500'), // 橙色
      new THREE.Color('#FFFFFF'), // 白色
    ];

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      
      // 在球体范围内随机分布
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = Math.random() * radius;

      positions[i3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = r * Math.cos(phi);

      // 随机颜色
      const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i3] = color.r;
      colors[i3 + 1] = color.g;
      colors[i3 + 2] = color.b;
    }

    return { positions, colors };
  }, [count, radius]);

  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.05;
      pointsRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.02) * 0.1;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={count}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.1}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
};

// 背景光效
export const BackgroundLight: React.FC = () => {
  return (
    <>
      {/* 环境光 */}
      <ambientLight intensity={0.2} color="#1a1a2e" />
      
      {/* 主光源 - 暖色调 */}
      <directionalLight
        position={[5, 10, 5]}
        intensity={1}
        color="#FFD700"
        castShadow
      />
      
      {/* 辅助光源 - 营造层次感 */}
      <pointLight
        position={[-5, 5, -5]}
        intensity={0.5}
        color="#C41E3A"
        distance={20}
      />
      
      <pointLight
        position={[5, -5, 5]}
        intensity={0.3}
        color="#FFA500"
        distance={15}
      />

      {/* 顶部光源 */}
      <spotLight
        position={[0, 10, 0]}
        angle={Math.PI / 6}
        penumbra={0.5}
        intensity={0.8}
        color="#FFD700"
        castShadow
      />
    </>
  );
};

// 辉光效果组件
export const GlowEffect: React.FC<{ position?: [number, number, number]; color?: string }> = ({
  position = [0, 0, 0],
  color = '#FFD700',
}) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
      meshRef.current.scale.setScalar(scale);
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[2, 32, 32]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.1}
        blending={THREE.AdditiveBlending}
        side={THREE.BackSide}
      />
    </mesh>
  );
};

export default Particles;
