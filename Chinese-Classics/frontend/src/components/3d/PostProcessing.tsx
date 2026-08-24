import React from 'react';
import { EffectComposer, Bloom, DepthOfField } from '@react-three/postprocessing';
import { BlendFunction, KernelSize } from 'postprocessing';

interface PostProcessingProps {
  enableBloom?: boolean;
  enableDepthOfField?: boolean;
  focusDistance?: number;
  focalLength?: number;
  bokehScale?: number;
}

export const PostProcessing: React.FC<PostProcessingProps> = ({
  enableBloom = true,
  enableDepthOfField = true,
  focusDistance = 0.02,
  focalLength = 0.5,
  bokehScale = 3,
}) => {
  return (
    <EffectComposer multisampling={8}>
      <>
        {enableBloom && (
          <Bloom
            blendFunction={BlendFunction.ADD}
            intensity={0.8}
            width={300}
            height={300}
            kernelSize={KernelSize.LARGE}
            luminanceThreshold={0.4}
            luminanceSmoothing={0.1}
          />
        )}
        {enableDepthOfField && (
          <DepthOfField
            focusDistance={focusDistance}
            focalLength={focalLength}
            bokehScale={bokehScale}
            height={480}
          />
        )}
      </>
    </EffectComposer>
  );
};

export default PostProcessing;
