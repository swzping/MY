import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface Bagua3DProps {
  position?: [number, number, number];
  rotationSpeed?: number;
  scale?: number;
  showTrigrams?: boolean;
}

// 八卦符号定义
const TRIGRAMS = [
  { name: '乾', symbol: '☰', lines: [1, 1, 1], angle: 0 },      // 天
  { name: '兑', symbol: '☱', lines: [0, 1, 1], angle: 45 },     // 泽
  { name: '离', symbol: '☲', lines: [1, 0, 1], angle: 90 },     // 火
  { name: '震', symbol: '☳', lines: [0, 0, 1], angle: 135 },    // 雷
  { name: '巽', symbol: '☴', lines: [1, 1, 0], angle: 180 },    // 风
  { name: '坎', symbol: '☵', lines: [0, 1, 0], angle: 225 },    // 水
  { name: '艮', symbol: '☶', lines: [1, 0, 0], angle: 270 },    // 山
  { name: '坤', symbol: '☷', lines: [0, 0, 0], angle: 315 },    // 地
];

export const Bagua3D: React.FC<Bagua3DProps> = ({
  position = [0, 0, 0],
  rotationSpeed = 0.003,
  scale = 1,
  showTrigrams = true,
}) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y -= rotationSpeed;
    }
  });

  // 创建八卦盘底座
  const baseGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    const outerRadius = 3;
    const innerRadius = 1.5;

    // 外圆
    shape.absarc(0, 0, outerRadius, 0, Math.PI * 2, false);
    // 内圆（创建圆环）
    const hole = new THREE.Path();
    hole.absarc(0, 0, innerRadius, 0, Math.PI * 2, true);
    shape.holes.push(hole);

    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: 0.15,
      bevelEnabled: true,
      bevelThickness: 0.03,
      bevelSize: 0.03,
      bevelSegments: 3,
    });

    return geometry;
  }, []);

  // 创建卦象线条
  const createTrigramLines = (lines: number[]) => {
    const group = new THREE.Group();
    const lineLength = 0.4;
    const lineGap = 0.12;
    const yaoHeight = 0.08;

    lines.forEach((line, index) => {
      const y = (1 - index) * lineGap;
      
      if (line === 1) {
        // 阳爻 - 实线
        const geometry = new THREE.BoxGeometry(lineLength, yaoHeight, 0.02);
        const mesh = new THREE.Mesh(
          geometry,
          new THREE.MeshStandardMaterial({
            color: '#FFD700',
            metalness: 0.9,
            roughness: 0.1,
          })
        );
        mesh.position.set(0, y, 0);
        group.add(mesh);
      } else {
        // 阴爻 - 断线
        const segmentLength = lineLength * 0.4;
        const gap = lineLength * 0.2;
        
        const leftGeometry = new THREE.BoxGeometry(segmentLength, yaoHeight, 0.02);
        const rightGeometry = new THREE.BoxGeometry(segmentLength, yaoHeight, 0.02);
        
        const material = new THREE.MeshStandardMaterial({
          color: '#FFD700',
          metalness: 0.9,
          roughness: 0.1,
        });
        
        const leftMesh = new THREE.Mesh(leftGeometry, material);
        leftMesh.position.set(-gap, y, 0);
        
        const rightMesh = new THREE.Mesh(rightGeometry, material);
        rightMesh.position.set(gap, y, 0);
        
        group.add(leftMesh);
        group.add(rightMesh);
      }
    });

    return group;
  };

  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* 八卦底盘 */}
      <mesh geometry={baseGeometry} rotation={[-Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color="#1a1a2e"
          metalness={0.7}
          roughness={0.3}
          emissive="#0f0f1a"
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* 外圈装饰环 */}
      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.9, 3.0, 64]} />
        <meshStandardMaterial
          color="#C41E3A"
          metalness={0.9}
          roughness={0.1}
          emissive="#C41E3A"
          emissiveIntensity={0.3}
        />
      </mesh>

      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.5, 1.6, 64]} />
        <meshStandardMaterial
          color="#C41E3A"
          metalness={0.9}
          roughness={0.1}
          emissive="#C41E3A"
          emissiveIntensity={0.3}
        />
      </mesh>

      {/* 八卦符号 */}
      {showTrigrams && TRIGRAMS.map((trigram, index) => {
        const angle = (trigram.angle * Math.PI) / 180;
        const radius = 2.2;
        const x = Math.sin(angle) * radius;
        const z = Math.cos(angle) * radius;

        return (
          <group key={index} position={[x, 0.2, z]} rotation={[0, angle, 0]}>
            {/* 卦象底盘 */}
            <mesh>
              <cylinderGeometry args={[0.35, 0.35, 0.05, 32]} />
              <meshStandardMaterial
                color="#2C2C2C"
                metalness={0.6}
                roughness={0.4}
              />
            </mesh>
            
            {/* 爻线 */}
            <primitive
              object={createTrigramLines(trigram.lines)}
              position={[0, 0.05, 0]}
            />
          </group>
        );
      })}

      {/* 中心太极 */}
      <group position={[0, 0.2, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[1.3, 64]} />
          <meshStandardMaterial
            color="#0a0a0a"
            metalness={0.6}
            roughness={0.4}
          />
        </mesh>

        <mesh rotation={[-Math.PI / 2, 0, Math.PI]}>
          <circleGeometry args={[1.3, 64, 0, Math.PI]} />
          <meshStandardMaterial
            color="#f5f5f5"
            metalness={0.6}
            roughness={0.4}
          />
        </mesh>

        {/* 阳眼 */}
        <mesh position={[0, 0.05, 0.65]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#0a0a0a" metalness={0.8} roughness={0.2} />
        </mesh>

        {/* 阴眼 */}
        <mesh position={[0, 0.05, -0.65]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#f5f5f5" metalness={0.8} roughness={0.2} />
        </mesh>
      </group>

      {/* 发光效果 */}
      <pointLight position={[0, 5, 0]} intensity={0.5} color="#FFD700" distance={10} />
      <pointLight position={[3, 3, 3]} intensity={0.3} color="#C41E3A" distance={8} />
      <pointLight position={[-3, 3, -3]} intensity={0.3} color="#C41E3A" distance={8} />
    </group>
  );
};

export default Bagua3D;
