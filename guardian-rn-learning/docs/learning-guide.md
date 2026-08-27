# Guardian RN Learning Guide

## Study Path

1. **Start with aliasing**

   Read `aliases.json`, `babel.config.js`, `src/core/features/home/HomeScreen.js`, and `src/override/features/home/HomeScreen.js`. The app imports `@app/features/home/HomeScreen`, but the override version wins.

2. **Read module config**

   Compare `src/core/config/modules.js` and `src/override/config/modules.js`. This mirrors the source project's `swift.config.js` pattern.

3. **Understand global state**

   Read `src/core/services/cache.js`. Notice how reactive variables avoid passing cart and user state through every screen.

4. **Follow initialization**

   Read `App.js` and `src/core/hooks/useAppInitialize.js`. This is the learning version of the source app startup flow.

5. **Trace navigation**

   Read `src/core/navigation/AppNavigator.js`, `AppStack.js`, `AuthStack.js`, and `AppTabs.js`. The app switches between auth, maintenance, and main app states.

6. **Study pure business logic**

   Read `src/core/helpers/cartLogic.js` and `src/core/helpers/deepLink.js`, then run:

   ```bash
   yarn test --runInBand
   ```

7. **Walk the features**

   Use the screens in this order: Auth Landing, Home, Catalog, Product Detail, Cart, Coupon Wallet, Scanner Simulator, Account.

## Exercises

- Add a new coupon type called `minimumSpend` that only applies above a subtotal threshold.
- Add a new module switch that disables Scanner and shows a snackbar when tapped.
- Add a new deep-link type such as `guardian://event/health-check`.
- Persist selected product history in AsyncStorage.
- Replace another core screen with an override version and document what changed.
- Add a mock GraphQL error and handle it like a session-expiry event.

## Useful Commands

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
yarn test --runInBand
yarn start
yarn ios
yarn android
```

## Mental Model

Think of the original project as three layers:

- **Platform layer:** React Native, native iOS/Android projects, Firebase, device APIs.
- **App framework layer:** navigation, Apollo, storage, module registry, global state, shared components.
- **Brand/business layer:** Guardian-specific modules, styling, promotions, coupons, scanner rules, account pages.

This learning app focuses on the second and third layers because they carry the most reusable engineering lessons.
