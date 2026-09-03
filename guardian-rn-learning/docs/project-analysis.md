# app-guardian 技术总结

这份文档总结原项目 `/Users/edy/Documents/fix/app-guardian` 的主要技术点和特色功能，并说明当前学习项目为什么只保留其中一部分。

## 项目类型

`app-guardian` 是一个 React Native 移动电商 App，面向 iOS 和 Android。它不是纯 Web 项目，也不是 Expo 快速原型项目，而是带有原生 iOS/Android 工程的 React Native CLI 项目。

这种项目通常适合中大型移动业务，因为它既能写跨平台 React Native 页面，也能接入相机、推送、地图、Firebase、支付等原生能力。

## 主要技术点

- **React Native 与 React**：原项目是现代 React Native 代码库，包含完整 iOS/Android 原生工程。
- **Core / Override 架构**：通过 `_src/core` 和 `_src/override` 分层，让公共能力和品牌定制分离。
- **Alias 优先级解析**：`@app` 优先指向 override，再回退到 core，实现“同一个 import，按项目命中不同实现”。
- **React Navigation**：拆分登录流程、主应用栈、底部 Tab 和详情页面。
- **Apollo Client**：用于 GraphQL 请求、缓存、错误链路、重试和本地状态。
- **Reactive Variables**：用 `makeVar` 管理购物车、用户、优惠券、维护模式、snackbar、积分、配送、支付等状态。
- **模块注册表**：通过 `swift.config.js` 管理页面名称、模块开关和功能配置。
- **Firebase 能力**：包含 analytics、crashlytics、performance、messaging、Firestore force update 和 Remote Config。
- **营销归因 SDK**：启动时会初始化 Adjust、Facebook、TikTok、CDP 等营销相关能力。
- **存储封装**：对 AsyncStorage 做统一包装，保存 token、cart id、用户类型、FCM token、主题等信息。
- **原生能力集成**：项目依赖中能看到相机扫码、地图、推送、图片选择、视频、WebView、二维码、设备信息等能力。

## 特色功能

- **Override-first 定制能力**：品牌定制文件可以替换 core 文件，而业务 import 不需要变化。这是原项目最值得学习的架构点。
- **启动编排**：App 启动时会初始化 SDK、Firebase Performance trace、用户状态、购物车 ID、FCM token、Crashlytics 用户标识、远程配置和强制更新监听。
- **路由感知埋点**：导航状态变化时记录页面访问，同时调整状态栏等页面表现。
- **扫码路由**：条码可以打开商品详情，二维码会先判断 Guardian 链接，再经过 URL 解析逻辑路由到原生页面。
- **深链路由**：链接可以映射到商品、分类、品牌、CMS、会员、游戏化、线下活动、注册和 Guardian Run 等业务。
- **电商状态同步**：购物车商品、价格、优惠券、礼品卡、店铺积分、会员积分、配送、账单和支付状态被拆成多个 reactive variables。
- **会话过期处理**：GraphQL 错误链路可以捕获 customer-not-found 或 session 错误，清理登录状态，展示 snackbar，并重置导航。
- **远程控制**：Firestore 和 Remote Config 可以驱动强制更新、维护模式和部分功能开关。

## 当前学习项目如何对应

当前学习项目位于：

```text
/Users/edy/Documents/MY/guardian-rn-learning
```

对应关系如下：

- 原项目 `_src/core` 和 `_src/override`，在新项目中对应 `src/core` 和 `src/override`。
- 原项目 `swift.config.js`，在新项目中拆成 `src/core/config/modules.js` 和 `src/override/config/modules.js`。
- 原项目 Apollo reactive variables，在新项目中对应 `src/core/services/cache.js`。
- 原项目 GraphQL 请求，在新项目中用 `src/core/services/mockGraphql.js` 模拟。
- 原项目扫码和深链，在新项目中对应 `src/core/helpers/deepLink.js` 和 Scanner Simulator 页面。
- 原项目购物车、优惠券和价格计算，在新项目中对应 `src/core/helpers/cartLogic.js`。
- 原项目底部 Tab 和品牌样式，在新项目中对应 `src/core/navigation/AppTabs.js`、`src/core/components/TabBarIcon.js` 和 `src/override/styles/theme.js`。

## 为什么学习项目做了简化

原项目里有很多生产环境能力，例如真实接口、Firebase、推送、营销归因、支付、地图、证书签名和发布配置。它们很重要，但学习成本高，而且需要真实账号、密钥或后端环境。

所以当前学习项目采用了“保留架构，简化依赖”的方式：

- 用 mock 数据替代真实 GraphQL 服务。
- 用 Scanner Simulator 替代真实相机扫码。
- 用 reactive variables 模拟登录、购物车、优惠券和维护模式。
- 用本地样式组件模拟原项目视觉，不直接绑定原项目 SVG 和私有组件。
- 用 Jest 测试保护购物车、深链和首页视图模型。

这样做的好处是：你可以先理解一个真实移动电商 App 的工程结构和业务流，再逐步补真实 SDK 和后端能力。

## 建议重点学习的部分

1. `core / override` 分层。
2. alias 优先解析。
3. 模块注册表。
4. 登录栈、主栈、底部 Tab 的导航组织。
5. Apollo reactive variables 状态管理。
6. mock service 与页面解耦。
7. 购物车与优惠券纯函数。
8. 扫码和 deep link 解析。
9. 首页、商品列表、购物车和账号页的页面结构。
10. 用测试保护核心业务规则。

## 暂未纳入学习项目的内容

以下内容当前没有搬入学习项目：

- 真实 Firebase 配置。
- 真实 GraphQL endpoint。
- 私有 CDP 或营销归因 SDK。
- 真实支付和订单提交。
- 真实相机扫码。
- FCM 推送证书。
- 地图定位配置。
- 复杂 WebView 混合页面。
- App Store / Google Play 发布配置。

这些能力可以作为后续进阶任务逐步补充，不适合一开始混进学习项目里。
