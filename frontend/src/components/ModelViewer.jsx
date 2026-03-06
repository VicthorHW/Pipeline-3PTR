// frontend/src/components/ModelViewer.jsx
import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { Stage, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';

export default function ModelViewer({ fileUrl, color = "#808080" }) {
  // Carrega o STL nativamente no navegador!
  const [geometry, setGeometry] = React.useState(null);

  React.useEffect(() => {
    if (!fileUrl) return;
    const loader = new STLLoader();
    loader.load(fileUrl, (geo) => {
      geo.center(); // Centraliza o pivô
      setGeometry(geo);
    });
  }, [fileUrl]);

  if (!geometry) return <div className="text-gray-400 text-sm">Carregando 3D...</div>;

  return (
    <div style={{ width: '100%', height: '200px', backgroundColor: '#1a1a1a', borderRadius: '8px' }}>
      <Canvas camera={{ position: [0, 50, 100], fov: 45 }}>
        <Stage environment="city" intensity={0.5}>
          <mesh geometry={geometry}>
            <meshStandardMaterial color={color} roughness={0.5} />
          </mesh>
        </Stage>
        <OrbitControls makeDefault autoRotate autoRotateSpeed={2.0} />
      </Canvas>
    </div>
  );
}