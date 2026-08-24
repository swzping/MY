import React, { useState, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Stars } from '@react-three/drei';
import * as THREE from 'three';

// 简化的太极符号 - 使用圆形和平面
function SimpleTaiChi({ rotationSpeed = 0.005 }: { rotationSpeed?: number }) {
  const meshRef = useRef<THREE.Group>(null);
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += rotationSpeed;
    }
  });

  return (
    <group ref={meshRef}>
      {/* 外圆环 */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.8, 2, 64]} />
        <meshBasicMaterial color="#C41E3A" transparent opacity={0.8} />
      </mesh>
      
      {/* 阴（黑色半圆） */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.1, 0]}>
        <circleGeometry args={[1.8, 64, 0, Math.PI]} />
        <meshStandardMaterial color="#1a1a1a" metalness={0.5} roughness={0.5} />
      </mesh>
      
      {/* 阳（白色半圆） */}
      <mesh rotation={[-Math.PI / 2, Math.PI, 0]} position={[0, 0.1, 0]}>
        <circleGeometry args={[1.8, 64, 0, Math.PI]} />
        <meshStandardMaterial color="#f5f5f5" metalness={0.5} roughness={0.5} />
      </mesh>
      
      {/* 阳眼（黑点） */}
      <mesh position={[0, 0.2, 0.9]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      
      {/* 阴眼（白点） */}
      <mesh position={[0, 0.2, -0.9]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#f5f5f5" />
      </mesh>

      {/* 中心发光效果 */}
      <mesh position={[0, -0.5, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[3, 32]} />
        <meshBasicMaterial 
          color="#FFD700" 
          transparent 
          opacity={0.1} 
        />
      </mesh>
    </group>
  );
}

// 简化的八卦 - 只显示8个卦象符号
function SimpleBagua() {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y -= 0.002;
    }
  });

  return (
    <group ref={groupRef}>
      {/* 外环 */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.5, 2.7, 64]} />
        <meshBasicMaterial color="#FFD700" transparent opacity={0.6} />
      </mesh>
      
      {/* 中心太极 */}
      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[1.5, 32]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
    </group>
  );
}

// 粒子效果
function SimpleParticles() {
  const points = useRef<THREE.Points>(null);
  
  const particleCount = 50;
  const positions = new Float32Array(particleCount * 3);
  
  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 20;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
  }

  useFrame((state) => {
    if (points.current) {
      points.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.1}
        color="#FFD700"
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

interface Scene3DProps {
  initialMode?: 'taichi' | 'bagua' | 'both';
  height?: string;
}

export const Scene3D: React.FC<Scene3DProps> = ({
  initialMode = 'taichi',
  height = '500px',
}) => {
  const [mode, setMode] = useState<'taichi' | 'bagua' | 'both'>(initialMode);
  const [autoRotate, setAutoRotate] = useState(true);
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return (
      <div 
        style={{ height }} 
        className="w-full bg-gradient-to-br from-[#1a1a2e] to-[#0f0f1a] rounded-lg flex items-center justify-center"
      >
        <div className="text-center">
          <div className="text-6xl mb-4">☯️</div>
          <h3 className="text-xl text-[#E0E0E0] font-serif">太极八卦</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-lg overflow-hidden border border-[#C41E3A]/30">
      {/* 控制栏 */}
      <div className="bg-[#1a1a2e] px-4 py-3 flex items-center justify-between border-b border-[#C41E3A]/20">
        <span className="text-lg font-bold text-[#C41E3A]">3D 国学视界</span>
        <div className="flex gap-2">
          {(['taichi', 'bagua', 'both'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                mode === m 
                  ? 'bg-[#C41E3A] text-white' 
                  : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
            >
              {m === 'taichi' ? '太极' : m === 'bagua' ? '八卦' : '合参'}
            </button>
          ))}
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className="px-3 py-1 rounded text-sm bg-white/5 text-gray-400 hover:bg-white/10 transition-colors ml-2"
          >
            {autoRotate ? '停止' : '旋转'}
          </button>
        </div>
      </div>

      {/* 3D Canvas */}
      <div style={{ height }} className="relative">
        <Canvas
          dpr={[1, 1.5]}
          gl={{ antialias: true, alpha: true }}
          camera={{ position: [0, 0, 10] }}
          onError={() => setHasError(true)}
        >
          {/* 基础光照 */}
          <ambientLight intensity={0.4} />
          <directionalLight position={[5, 10, 7]} intensity={1} color="#FFD700" />
          <pointLight position={[-5, 5, -5]} intensity={0.5} color="#C41E3A" />

          {/* 背景星星 */}
          <Stars radius={100} depth={50} count={100} factor={4} saturation={0} fade speed={1} />

          {/* 粒子 */}
          <SimpleParticles />

          {/* 3D对象 */}
          {(mode === 'taichi' || mode === 'both') && (
            <SimpleTaiChi rotationSpeed={autoRotate ? 0.005 : 0} />
          )}
          
          {(mode === 'bagua' || mode === 'both') && (
            <SimpleBagua />
          )}

          {/* 控制器 */}
          <OrbitControls
            enablePan={false}
            enableZoom={true}
            enableRotate={true}
            minDistance={5}
            maxDistance={20}
            autoRotate={false}
          />
          
          <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={50} />
        </Canvas>

        {/* 操作提示 */}
        <div className="absolute bottom-0 left-0 right-0 px-4 py-2 text-xs text-center text-gray-500 bg-gradient-to-t from-black/50 to-transparent">
          💡 拖拽旋转 | 滚轮缩放
        </div>
      </div>
    </div>
  );
};

// 简化的横幅版本
export const Scene3DBanner: React.FC = () => {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return (
      <div className="w-full h-64 md:h-80 lg:h-96 bg-gradient-to-br from-[#1a1a2e] to-[#0f0f1a] rounded-2xl flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse">☯️</div>
          <h3 className="text-xl text-[#E0E0E0] font-serif">3D 沉浸式体验</h3>
          <p className="text-gray-500 text-sm mt-2">太极八卦 · 立体呈现</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-64 md:h-80 lg:h-96 rounded-2xl overflow-hidden">
      <Canvas
        dpr={1}
        gl={{ antialias: true, alpha: true }}
        camera={{ position: [0, 0, 8] }}
        onError={() => setHasError(true)}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} color="#FFD700" />
        <pointLight position={[-5, 5, -5]} intensity={0.4} color="#C41E3A" />
        
        <Stars radius={50} depth={30} count={50} factor={3} fade speed={0.5} />
        <SimpleTaiChi rotationSpeed={0.003} />
        
        <OrbitControls
          enablePan={false}
          enableZoom={false}
          enableRotate={true}
          autoRotate={true}
          autoRotateSpeed={0.5}
        />
        
        <PerspectiveCamera makeDefault position={[0, 0, 6]} fov={55} />
      </Canvas>
    </div>
  );
};

export default Scene3D;
