# Guardian RN Learning Design

## Goal

Create a lightweight React Native learning project at `/Users/edy/Documents/MY/guardian-rn-learning` that teaches the main engineering ideas and special features from `/Users/edy/Documents/fix/app-guardian` without copying private app configuration or production business integrations.

The project should be suitable for learning and experimentation: easy to read, small enough to modify, and close enough to the original React Native app structure that lessons transfer back to the source project.

## Source Project Summary

The original project is a React Native 0.79 mobile commerce app. Its most important technical characteristics are:

- React Native CLI mobile app with iOS and Android projects.
- `@app` alias resolves to `_src/override` first, then `_src/core`, allowing a base framework to be customized by a brand-specific layer.
- React Navigation stack and bottom-tab routing with login/main-app switching.
- Apollo Client for GraphQL, including custom query/mutation hooks and reactive variables for global app state.
- Feature modules are controlled by `swift.config.js` module switches.
- Firebase integrations cover analytics, crash reporting, performance tracing, messaging, Firestore force update, and Remote Config.
- App initialization gathers user state, cart id, address, wishlist, reward points, FCM token, and crash user id.
- Scanner feature reads QR/barcodes, resolves product or web URLs, and routes users into native screens.
- Deep links map product/category/brand/CMS/activity paths to app screens.
- Commerce features include product listing/detail, cart, checkout, coupons, points, store credit, wishlist, notifications, and store locator.
- Marketing and attribution include Adjust, Facebook, TikTok, and a CDP SDK.

## Learning Project Scope

The learning app will be a small React Native CLI project named `GuardianLearningApp`. It will demonstrate:

- Core/override architecture.
- Alias-based imports.
- Module registry and module enable switches.
- Auth stack versus main app stack.
- Bottom tabs for Home, Catalog, Cart, Scanner, and Account.
- Apollo reactive variables for login state, cart count, maintenance mode, snackbar, selected coupon, and current product.
- Mock GraphQL service layer with query/mutation-like helpers.
- App initialization hook that loads persisted state and mock remote config.
- Product list and product detail screens.
- Cart add/remove/quantity flow.
- Coupon wallet and coupon application flow.
- Scanner simulator screen that accepts typed QR/barcode input instead of requiring a physical camera.
- Deep link simulator/parser that routes product, category, brand, CMS, and campaign links.
- Maintenance mode toggle to show how remote config can alter navigation.
- Documentation explaining how each learning feature maps back to the original project.

The project will not include real Firebase credentials, private SDK packages, production GraphQL endpoints, native camera scanning, real checkout, payment, Maps, or production attribution SDK calls.

## Architecture

Directory layout:

```text
guardian-rn-learning/
  App.js
  index.js
  package.json
  babel.config.js
  metro.config.js
  aliases.json
  app.json
  src/
    core/
      components/
      config/
      data/
      helpers/
      hooks/
      navigation/
      services/
      features/
    override/
      components/
      config/
      features/
      styles/
  docs/
    project-analysis.md
    learning-guide.md
```

The alias `@app/*` will point to `src/override/*` first and then `src/core/*`, mirroring the source project. Shared behavior goes in `core`; brand-specific screens, theme, and copy go in `override`.

## Screens And Flows

Screens:

- Auth Landing: guest/login switch, writes mock token into storage and reactive state.
- Home: banners, module toggles, remote config summary, shortcut links.
- Catalog: mock product list with category/brand filters.
- Product Detail: product information, add-to-cart action, wishlist toggle placeholder.
- Cart: cart items, quantity controls, coupon entry, totals.
- Coupon Wallet: available coupons and apply/remove behavior.
- Scanner Simulator: input examples for product barcode and Guardian URLs.
- Account: user state, reward points, logout, maintenance toggle.
- Maintenance: full-screen maintenance state when module config says the app is blocked.

Data flow:

- `App.js` initializes app SDK stubs, wraps navigation with Apollo Provider, and starts launch timing.
- `useAppInitialize` reads mock storage, mock remote config, and saved cart state.
- `services/cache.js` stores app state in Apollo reactive variables.
- Screen actions call mock service functions, then update reactive variables.
- Navigation helpers centralize route switching and link resolution.

## Error Handling

The learning project will include visible, simple failure states:

- Disabled module navigation shows a snackbar.
- Unknown barcode or unsupported deep link shows a snackbar.
- Invalid coupon shows inline feedback.
- Mock auth expiration can clear token and return to auth flow.

## Testing And Verification

Minimum verification:

- `yarn install` or dependency check if packages are already present.
- Jest tests for URL/deep-link parsing, cart reducer behavior, and coupon validation.
- Static import smoke check through Babel/Jest.
- Start Metro if dependencies are installed successfully.

Because React Native native builds can depend on local Xcode/Android setup, successful Metro startup and passing Jest tests are the baseline completion criteria.

## Acceptance Criteria

- `/Users/edy/Documents/MY/guardian-rn-learning` exists.
- The project includes a readable React Native CLI-style structure.
- Documentation summarizes the original project's technical points and special features.
- The learning app implements the scoped screens and flows with mock data.
- The `core/override` pattern is visible and documented.
- Tests cover the most important pure logic.
- Commands to run the app and tests are documented.
