---
name: home-panorama-tour
description: Build home decoration 360 panorama and virtual-tour experiences like JustEasy/VR house viewing pages, including equirectangular panoramas, room-to-room hotspots, floorplan navigation, mobile gyro controls, fullscreen/VR mode, and frontend implementation choices with Photo Sphere Viewer, Pannellum, Marzipano, A-Frame, WebXR, or Three.js.
metadata:
  short-description: Build 360 home panorama virtual tours
---

# Home Panorama Tour

Use this skill when the user asks to build, clone, prototype, or explain an interior decoration 360 panorama, VR house viewing page, virtual tour, room walkthrough, panorama hotspot tour, or a page similar to `vr.justeasy.cn`.

## First Choice

For most web apps, prefer a purpose-built panorama viewer instead of hand-rolling sphere/camera math:

- **Photo Sphere Viewer**: best default for polished single-page tours, markers, navbar, plugins, React/Vue integration.
- **Pannellum**: light, simple, good for static tours and straightforward hotspot linking.
- **Marzipano**: best when there are many scenes, tiled panoramas, or high-resolution production tours.
- **A-Frame/WebXR**: use when the user explicitly wants VR headset/WebXR behavior or a 3D scene around the panorama.
- **Three.js**: use when custom 3D interaction, mixed 3D objects, or unusual rendering is required.

Avoid building the core panorama renderer from scratch unless the user asks for a custom engine.

## Expected Features

For a JustEasy-style home panorama, include the features that fit the scope:

- 360-degree equirectangular panorama rendering.
- Multiple room scenes with clear transitions.
- Hotspots for moving to another room, opening labels, or showing product/detail info.
- Bottom or side scene strip for room switching.
- Optional floorplan/minimap with current room indicator.
- Fullscreen button and mobile-friendly touch drag.
- Optional autorotate with pause on interaction.
- Optional gyroscope/device-orientation controls on mobile.
- Optional WebXR/VR entry if the library and browser support it.
- Loading, error, and unsupported-browser states.

## Implementation Workflow

1. Inspect the existing project before choosing a stack.
2. Reuse the app's framework, routing, styling system, and asset pipeline.
3. If no project exists, choose a minimal Vite app for prototypes.
4. Use sample panorama assets only as placeholders; tell the user to replace them with real equirectangular room renders or photos.
5. Model scenes as data:

```ts
type TourScene = {
  id: string;
  name: string;
  panoramaUrl: string;
  thumbnailUrl?: string;
  yaw?: number;
  pitch?: number;
  hotspots?: Array<{
    id: string;
    type: "navigate" | "info";
    yaw: number;
    pitch: number;
    label: string;
    targetSceneId?: string;
    body?: string;
  }>;
};
```

6. Keep viewer lifecycle explicit: create on mount, update on scene changes, destroy on unmount.
7. Validate in a real browser. Check drag, zoom, scene switching, fullscreen, responsive layout, and asset loading.

## UI Guidance

- Make the panorama the primary full-viewport experience.
- Keep controls compact and familiar: fullscreen, rotate, VR, scene list, map toggle.
- Do not hide core navigation behind explanatory text.
- On mobile, keep bottom controls thumb-accessible and avoid covering hotspots.
- Use dark translucent controls over the panorama, but maintain readable contrast.
- If using cards, reserve them for hotspots/modals; do not wrap the whole panorama in a decorative card.

## Asset Requirements

- Use equirectangular images with a 2:1 aspect ratio, commonly 4096x2048 or 8192x4096.
- Prefer compressed JPG/WebP for photos and rendered interiors.
- For large tours, use tiled panoramas or lazy-load scenes.
- Avoid normal flat room photos unless the implementation intentionally uses a 2D gallery fallback.

## Library Notes

Photo Sphere Viewer packages commonly used:

```bash
npm install @photo-sphere-viewer/core @photo-sphere-viewer/markers-plugin
```

Pannellum package/CDN is useful for simple static tours:

```bash
npm install pannellum-react pannellum
```

A-Frame is useful for quick WebXR scenes:

```bash
npm install aframe
```

Always confirm current package names and APIs from the installed version or official docs when implementing.

## Validation Checklist

- Panorama image renders nonblank.
- Drag/zoom works with mouse and touch.
- Hotspots appear in correct approximate directions.
- Room switching updates the panorama and active UI state.
- Browser console has no missing asset or lifecycle errors.
- Mobile viewport has no overlapping controls.
- Fullscreen and optional VR/gyro controls degrade gracefully.
