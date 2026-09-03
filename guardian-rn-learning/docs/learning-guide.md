# Guardian RN 学习指南

这份文档给出当前学习项目的阅读顺序、练习方向和常用命令。建议先按顺序阅读，再动手改一个小功能。

## 学习路径

1. **先理解 alias 覆盖机制**

   阅读 `aliases.json`、`babel.config.js`、`src/core/features/home/HomeScreen.js` 和 `src/override/features/home/HomeScreen.js`。

   项目里虽然统一引入 `@app/features/home/HomeScreen`，但实际会优先命中 `src/override` 里的首页。这就是原项目 override-first 架构的简化版。

2. **阅读模块配置**

   对比 `src/core/config/modules.js` 和 `src/override/config/modules.js`。

   这对应原项目里的 `swift.config.js` 思路：用配置集中管理页面名称、模块开关和业务定制。

3. **理解全局状态**

   阅读 `src/core/services/cache.js`。

   这里用 Apollo reactive variables 管理登录态、购物车、优惠券、维护模式和 snackbar。页面通过 `useReactiveVar` 订阅状态变化，不需要层层传 props。

4. **跟一遍启动流程**

   阅读 `App.js` 和 `src/core/hooks/useAppInitialize.js`。

   这是原项目启动编排的学习版：真实项目会初始化 Firebase、埋点、Remote Config、用户信息等；学习项目用 mock 状态模拟这个过程。

5. **追踪导航结构**

   阅读 `src/core/navigation/AppNavigator.js`、`AppStack.js`、`AuthStack.js` 和 `AppTabs.js`。

   重点看 App 如何在登录页、维护页和主 App 之间切换，以及底部 Tab 如何挂载首页、商品、购物车、扫码和账号页面。

6. **学习纯业务逻辑**

   阅读 `src/core/helpers/cartLogic.js` 和 `src/core/helpers/deepLink.js`，然后运行测试：

   ```bash
   yarn test --runInBand
   ```

   购物车价格计算、优惠券折扣、扫码和深链解析都适合写成纯函数，这样更容易测试和维护。

7. **按业务链路体验页面**

   推荐体验顺序：

   1. 登录页。
   2. 首页。
   3. 商品列表。
   4. 商品详情。
   5. 购物车。
   6. 优惠券钱包。
   7. 扫码模拟器。
   8. 账号页。

## 练习题

- 新增一种优惠券类型，例如 `minimumSpend`，只在小计达到指定金额后生效。
- 新增一个模块开关，让 Scanner 关闭时不进入页面，而是弹出 snackbar。
- 新增一种 deep link，例如 `guardian://event/health-check`。
- 用 AsyncStorage 保存最近浏览过的商品。
- 再写一个 override 页面，例如覆盖账号页，并记录和 core 页面的区别。
- 在 mock GraphQL 服务里模拟接口错误，并按会话过期的方式处理。

## 常用命令

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
yarn test --runInBand
yarn start
yarn ios
yarn android
```

## 理解模型

可以把原项目理解成三层：

- **平台层**：React Native、iOS/Android 原生工程、Firebase、设备能力。
- **App 框架层**：导航、Apollo、存储、模块注册表、全局状态、公共组件。
- **品牌业务层**：Guardian 定制页面、主题样式、促销、优惠券、扫码规则、账号体系。

当前学习项目重点学习第二层和第三层，因为它们最能复用到其他业务 App 中。
