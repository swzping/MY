# Guardian RN Learning

A small React Native CLI-style learning project extracted from the architecture and feature ideas of `/Users/edy/Documents/fix/app-guardian`.

It keeps the original project's learning value while replacing production services with mock data:

- `src/core` and `src/override` architecture.
- `@app` alias that resolves override files before core files.
- React Navigation auth stack, app stack, and bottom tabs.
- Apollo reactive variables for app state.
- Mock GraphQL service layer.
- Login state, catalog, product detail, cart, coupon wallet, scanner simulator, deep links, and maintenance mode.

## Commands

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
yarn install --ignore-scripts
yarn test --runInBand
yarn start
```

For a native run, use the React Native CLI commands after the local iOS or Android toolchain is ready:

```bash
yarn ios
yarn android
```

## Key Files

- `aliases.json`: override-first alias pattern copied from the source project's idea.
- `src/core/config/modules.js`: base module registry.
- `src/override/config/modules.js`: brand-level module override.
- `src/core/services/cache.js`: Apollo reactive variables.
- `src/core/services/mockGraphql.js`: mock GraphQL-like API.
- `src/core/helpers/deepLink.js`: deep-link and scanner logic.
- `src/core/helpers/cartLogic.js`: cart and coupon pure logic.
- `src/override/features/home/HomeScreen.js`: visible override example.

## What To Try

1. Sign in with the mock user.
2. Open Catalog and add a product to cart.
3. Apply `WELCOME10` or `SAVE5` in Coupon Wallet.
4. Use Scanner Simulator with `8991002100012`.
5. Try deep-link examples from Scanner Simulator.
6. Enter and leave Maintenance Mode from Account.
