# app-guardian Technical Summary

## Project Type

`app-guardian` is a React Native mobile commerce application. It targets iOS and Android and uses a React Native CLI structure rather than a web-only or Expo-only setup.

## Main Technology Points

- **React Native 0.79 and React 19:** the app is a modern RN codebase with native iOS/Android projects.
- **Core/override architecture:** `aliases.json` maps `@app` to `_src/override` first and `_src/core` second. This lets the team keep a reusable base app and replace selected modules for a brand or market.
- **React Navigation:** the app separates auth flow, main app stack, and bottom tabs.
- **Apollo Client:** GraphQL requests use Apollo Client, custom query/mutation helpers, error links, retry links, and reactive variables.
- **Reactive state:** cart, user, snackbar, maintenance, wishlist, reward points, shipping, payment, coupon, and many other app states are stored with `makeVar`.
- **Module registry:** `swift.config.js` controls screen names, enable switches, and nested feature flags.
- **Firebase:** analytics, crashlytics, performance, messaging, Firestore force update, and Remote Config are present.
- **Marketing attribution:** Adjust, Facebook, TikTok, and a CDP SDK are initialized during app launch.
- **Storage wrapper:** AsyncStorage is wrapped behind a small helper so token, cart id, user type, FCM token, and theme can be reused.
- **Native capability integrations:** camera scanning, maps, push notification, image picking, video, webview, QR, and device info appear in the dependency set.

## Special Functional Features

- **Override-first customization:** a brand-specific file can replace a core file without changing imports. This is the most valuable architectural pattern to study.
- **Startup orchestration:** app launch initializes SDKs, Firebase Performance trace, user state, cart id, FCM token, Crashlytics user id, remote config, and force-update listeners.
- **Route-aware analytics:** navigation state changes log screen transitions and update status-bar behavior.
- **Scanner routing:** barcode scans can open product detail. QR scans are checked against Guardian URLs, resolved through URL resolver logic, and routed to native screens.
- **Deep-link router:** links map to product, category, brand, CMS, membership, gamification, offline activity, registration, and Guardian Run flows.
- **Commerce state sync:** cart item, price, coupon, gift card, store credit, reward point, shipping, billing, and payment state are split into reactive variables.
- **Session-expiry handling:** GraphQL error links can catch customer-not-found/session errors, clear auth, show a snackbar, and reset navigation.
- **Remote controls:** Firestore and Remote Config can drive force update and feature behavior.

## How This Learning App Maps Back

- `_src/core` and `_src/override` become `src/core` and `src/override`.
- `swift.config.js` becomes `src/core/config/modules.js` plus `src/override/config/modules.js`.
- Apollo reactive vars are reproduced in `src/core/services/cache.js`.
- GraphQL calls are replaced by deterministic mock services in `src/core/services/mockGraphql.js`.
- Scanner and deep-link behavior are taught through `src/core/helpers/deepLink.js` and the Scanner Simulator screen.
- Cart, coupon, and totals logic are kept pure in `src/core/helpers/cartLogic.js` so the learning project has fast tests.

## What Was Intentionally Omitted

Real Firebase credentials, production GraphQL endpoints, private CDP packages, real checkout/payment, native camera scanning, push certificates, Maps configuration, and store deployment settings are omitted. Those are important in production but distracting for a focused learning project.
