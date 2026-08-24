# Source Project Notes

This lab is inspired by the Guardian Magento PWA project.

Mapped concepts:

- Magento PWA Studio / Venia shell -> `src/app`
- PWA Buildpack targets -> `src/buildpack`
- Peregrine talons -> `src/talons`
- Magento GraphQL -> `src/graphql`
- OAuth refresh link -> `src/lib/authSession.js`
- Online/offline PWA behavior -> `src/lib/pwa.js` and `useNetworkStatus`
- Midtrans/payment registration -> `paymentRegistry`
- Rewards, store credit, coupons -> `RewardsPage`
- Apoteker and medical pages -> `HealthPage`
- Offline event booking -> `OfflineEventsPage`
- PageBuilder banners, ads, tracking -> `PageBuilderDemo`, `ads.js`, and `useTracking`

The lab intentionally uses mock data and original teaching code. It does not copy the production storefront.
