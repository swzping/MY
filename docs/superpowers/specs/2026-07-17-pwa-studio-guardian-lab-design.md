# Mini PWA Studio Guardian Lab Design

## Purpose

Create a learning project at `/Users/edy/Documents/MY/pwa-studio-guardian-lab` that extracts the main technical ideas and special business features from the Guardian Magento PWA project into a runnable, study-friendly lab.

The lab should help a learner understand how a Magento PWA Studio style storefront is organized without requiring a real Magento backend, Adobe Commerce license, payment provider, or production API credentials.

## Scope

The chosen scope is **C. Engineering simulation project**.

The project will be a Mini PWA Studio Clone: a Vite + React app with a mock GraphQL layer, PWA behavior, plugin-style registries, and simplified commerce modules inspired by the source project.

## Goals

- Demonstrate the architecture of a PWA Studio/Venia style storefront.
- Show how routes, payment methods, and feature modules can be registered through plugin-like configuration.
- Simulate Peregrine-style `talons` and hooks for app logic.
- Include a mock OAuth + Magento customer token refresh flow.
- Include PWA offline awareness and a service worker registration path.
- Include the special feature areas observed in the Guardian project: rewards, store credit, health services, offline events, free gifts, ads, tracking, PageBuilder-like banners, and account/order pages.
- Keep the app small enough to read and modify as a learning project.

## Non-Goals

- Do not connect to a real Magento backend.
- Do not copy proprietary business code from the Guardian project.
- Do not implement a complete checkout or real payment settlement.
- Do not implement UPWARD, SSR, or production Magento deployment.
- Do not build a large admin system.

## Recommended Stack

- Vite
- React
- React Router
- Plain CSS modules or scoped CSS files
- Mock GraphQL client implemented locally
- Browser localStorage for session simulation
- Service worker registration through Vite PWA-friendly structure

The project should avoid heavy framework setup. The point is to make the architecture visible.

## Architecture

The project will use this structure:

```text
pwa-studio-guardian-lab/
  docs/
    learning-map.md
    source-project-notes.md
  public/
    mock-sw.js
  src/
    app/
      App.jsx
      routes.jsx
      shell/
    buildpack/
      featureFlags.js
      paymentRegistry.js
      routeRegistry.js
    graphql/
      mockClient.js
      mockData.js
      operations.js
    lib/
      authSession.js
      tracking.js
      ads.js
      pwa.js
    modules/
      account/
      catalog/
      checkout/
      health/
      offlineEvents/
      rewards/
      pageBuilder/
    talons/
      useAuthSession.js
      useCart.js
      useNetworkStatus.js
      useTracking.js
    styles/
  package.json
  README.md
```

## Core Modules

### App Shell

The shell provides the storefront frame: header, navigation, account status, cart indicator, offline indicator, and main route outlet.

Routes are loaded from `routeRegistry`, so learners can see how PWA Studio target-style registration maps to React Router.

### Mock GraphQL

The mock GraphQL layer will expose functions that behave like named queries and mutations:

- products and categories
- customer profile
- cart summary
- orders
- coupons and rewards
- health records
- offline event tickets
- token refresh

This keeps the data flow GraphQL-like while remaining local and easy to inspect.

### Auth Session Lab

The auth lab simulates the source project's dual-token model:

- `access_token`
- `refresh_token`
- `access_token_expires_at`
- `customer_token`
- `signin_token`

It will include:

- sign in demo
- near-expiry refresh before GraphQL operations
- proactive refresh timer
- manual force-expire button for learning
- clear session/sign out

### Buildpack-Style Registries

The project will include lightweight registries:

- `routeRegistry`: modules add pages by name and path.
- `paymentRegistry`: payment methods are registered by code.
- `featureFlags`: toggles modules such as rewards, health, offline events, ads, and tracking.

This mirrors the source project's use of PWA Studio targets without recreating the whole Buildpack.

### Business Feature Modules

The first version will include simplified pages for:

- catalog and product detail
- cart and checkout overview
- payment methods demo
- account dashboard and orders
- rewards and store credit
- coupon list
- health services and health result page
- offline event booking and ticket list
- free gift list
- PageBuilder-like banner with ad slot and tracking

### Marketing Layer

The marketing layer will simulate:

- ad slot configuration for desktop and mobile
- shared ad pool consumption
- event tracking calls
- page view and click tracking log

The UI should expose the tracking log so learners can see which actions fire events.

### PWA / Offline

The PWA lab will include:

- service worker registration
- online/offline state hook
- offline banner
- local fallback data messaging

It does not need production caching sophistication in the first version.

## User Experience

The first screen should be the learning storefront itself, not a marketing landing page.

The UI should feel like a compact commerce operations lab:

- left or top navigation for modules
- visible status panel for session, network, feature flags, and tracking events
- cards or panels only for repeated items and contained tools
- clear labels that describe concepts without overwhelming the screen

## Error Handling

- Mock GraphQL operations should return structured success/error responses.
- Token refresh failure should show a non-blocking warning in the UI.
- Offline mode should clearly mark data as local/mock.
- Disabled feature flags should route to a clear "module disabled" state.

## Testing / Verification

Initial verification should include:

- install dependencies
- run lint or build
- start local dev server
- manually verify key flows:
  - sign in
  - force token expiry and refresh
  - navigate modules
  - toggle offline simulation or browser offline mode
  - register payment methods
  - fire tracking events

## Deliverables

- A new project directory: `/Users/edy/Documents/MY/pwa-studio-guardian-lab`
- `README.md` explaining what each module teaches
- runnable Vite React application
- source notes connecting each lab feature back to the Guardian PWA concept
- local mock data and mock GraphQL operations

## Open Decisions

The first implementation will use plain React and local mock APIs. If a later iteration needs closer Magento fidelity, a mock GraphQL HTTP server can be added after the basic lab is stable.
