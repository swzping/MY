# Guardian RN Learning

这是一个轻量级 React Native CLI 风格学习项目，提炼自 `/Users/edy/Documents/fix/app-guardian` 的架构和核心功能思路。

它保留原项目最值得学习的工程点，同时用 mock 数据替代生产环境服务：

- `src/core` 与 `src/override` 分层架构。
- `@app` alias 优先解析 override 文件，再回退到 core 文件。
- React Navigation 登录栈、主应用栈和底部 Tab。
- 使用 Apollo reactive variables 管理全局 App 状态。
- Mock GraphQL 服务层。
- 登录态、商品目录、商品详情、购物车、优惠券钱包、扫码模拟、深链跳转和维护模式。

## 常用命令

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
yarn install --ignore-scripts
yarn test --runInBand
yarn start
```

如果本机 iOS 或 Android 开发环境已经配置好，可以使用 React Native CLI 运行原生 App：

```bash
yarn ios
yarn android
```

## 关键文件

- `aliases.json`：复刻原项目的 override-first alias 思路。
- `src/core/config/modules.js`：基础模块注册表。
- `src/override/config/modules.js`：品牌/业务定制层的模块覆盖。
- `src/core/services/cache.js`：Apollo reactive variables 全局状态。
- `src/core/services/mockGraphql.js`：类似 GraphQL 的 mock API。
- `src/core/helpers/deepLink.js`：深链与扫码解析逻辑。
- `src/core/helpers/cartLogic.js`：购物车和优惠券的纯业务逻辑。
- `src/override/features/home/HomeScreen.js`：可见的 override 覆盖示例。

## 建议体验顺序

1. 使用 mock 用户登录。
2. 打开 Catalog，把商品加入购物车。
3. 在 Coupon Wallet 中应用 `WELCOME10` 或 `SAVE5`。
4. 在 Scanner Simulator 中输入 `8991002100012`。
5. 体验 Scanner Simulator 中的深链示例。
6. 在 Account 页面进入和退出 Maintenance Mode。
