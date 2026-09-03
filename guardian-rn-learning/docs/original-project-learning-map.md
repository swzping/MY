# 原项目技术模块学习指南

这份文档说明 `/Users/edy/Documents/fix/app-guardian` 的主要技术模块，在当前学习项目中如何被简化、保留和体现。

当前学习项目的目标不是复制完整生产 App，而是把原项目中最值得学习的架构、导航、状态管理和电商业务流程抽出来，做成一个可以独立运行、容易阅读、容易改造的 React Native 学习项目。

## 1. Core / Override 分层架构

### 原项目体现

原项目通过 `_src/core` 和 `_src/override` 组织代码。核心能力放在 `core`，品牌或业务定制放在 `override`。业务代码统一从 `@app/...` 引入，具体命中文件由 alias 决定。

这个模式适合多品牌、多市场或多业务线 App：公共逻辑不重复写，差异化页面可以单独覆盖。

### 新项目体现

对应文件：

- `aliases.json`
- `babel.config.js`
- `src/core`
- `src/override`
- `src/core/features/home/HomeScreen.js`
- `src/override/features/home/HomeScreen.js`

新项目保留了 override-first 的学习重点：当代码 import `@app/features/home/HomeScreen` 时，会优先解析 `src/override/features/home/HomeScreen.js`，找不到时再回退到 `src/core/features/home/HomeScreen.js`。

### 学习重点

- 为什么大型 App 不应该把品牌差异散落在核心代码里。
- 如何用 alias 实现“同一个 import，不同项目命中不同实现”。
- 如何判断一个功能应该放在 `core` 还是 `override`。

建议练习：再新增一个 `src/override/features/account/AccountScreen.js`，观察不改导航代码也能替换账号页。

## 2. 模块注册表

### 原项目体现

原项目使用 `swift.config.js` 管理页面模块、路由名称、启用状态和部分功能开关。

这类配置能让页面注册、导航跳转和业务开关更集中，避免路由名称散落在各个文件中。

### 新项目体现

对应文件：

- `src/core/config/modules.js`
- `src/override/config/modules.js`

`core` 定义基础模块，例如 Home、Catalog、Cart、Scanner、Account、CMS、Campaign。`override` 在此基础上覆盖部分 label，例如把 Home 改为 Guardian Lab，把 Scanner 改为 Scan Lab。

### 学习重点

- 页面名称不直接写死在业务页面中。
- 品牌定制可以只覆盖配置，不一定重写完整页面。
- 导航、深链、扫码跳转都可以共用模块注册表。

建议练习：给 Scanner 增加一个 `enable: false` 状态，并在点击时弹出 snackbar，而不是进入页面。

## 3. React Navigation 导航体系

### 原项目体现

原项目拆分了登录流程、主 App 栈、底部 Tab 和各种详情页面。底部 Tab 使用原项目自定义图标、颜色、购物车 badge 和标签样式。

### 新项目体现

对应文件：

- `src/core/navigation/AppNavigator.js`
- `src/core/navigation/AuthStack.js`
- `src/core/navigation/AppStack.js`
- `src/core/navigation/AppTabs.js`
- `src/core/components/TabBarIcon.js`

新项目保留了三层结构：

- `AppNavigator`：根据登录态、维护模式决定显示 Auth、Main App 或 Maintenance。
- `AuthStack`：登录前页面。
- `AppStack`：登录后的主栈，包含 Tab、商品详情、优惠券、CMS、活动页。
- `AppTabs`：底部五个主入口，模拟原项目 Home、Category、Cart、Store/Scanner、Account 的结构。

### 学习重点

- 登录态如何影响根导航。
- Tab 页面和详情页面为什么要分层。
- 购物车数量如何体现在底部 Tab badge。
- UI 样式如何在学习项目中复刻原项目风格，但不直接耦合原项目资源。

建议阅读顺序：`AppNavigator.js` -> `AppStack.js` -> `AppTabs.js`。

## 4. Apollo Reactive Variables 全局状态

### 原项目体现

原项目大量使用 Apollo `makeVar` 管理全局状态，包括用户、购物车、优惠券、维护模式、snackbar、积分、支付和配送等。

这种方式适合 React Native App 中的轻量全局状态：页面可以通过 `useReactiveVar` 订阅变化，不需要层层传 props。

### 新项目体现

对应文件：

- `src/core/services/cache.js`
- `src/core/navigation/AppNavigator.js`
- `src/core/navigation/AppTabs.js`
- `src/core/components/SnackbarHost.js`
- `src/core/features/cart/CartScreen.js`
- `src/core/features/account/AccountScreen.js`

新项目保留了关键状态：

- `rxUserToken`：登录状态。
- `rxAppLoading`：启动加载状态。
- `rxAppMaintenance`：维护模式。
- `rxRemoteConfig`：远程配置模拟。
- `rxCartItems` / `rxCartQty`：购物车数据和数量。
- `rxSelectedCoupon`：已选优惠券。
- `rxAppSnackbar`：全局提示。

### 学习重点

- `makeVar` 如何定义状态。
- `useReactiveVar` 如何让页面响应状态变化。
- `syncCartState` 如何把购物车列表同步成购物车数量。
- 为什么购物车 badge 不需要从页面 props 一层层传递。

建议练习：新增一个 `rxWishlistItems`，让首页或商品列表可以收藏商品。

## 5. Mock GraphQL 服务层

### 原项目体现

原项目使用 Apollo Client 请求真实 GraphQL 服务，并包含错误处理、重试、鉴权、会话过期处理等生产逻辑。

### 新项目体现

对应文件：

- `src/core/services/mockGraphql.js`
- `src/core/data/mockData.js`
- `src/core/features/catalog/CatalogScreen.js`
- `src/core/features/product/ProductDetailScreen.js`
- `src/core/features/coupons/CouponWalletScreen.js`

新项目没有连接真实后端，而是用 mock service 模拟 GraphQL 查询。页面仍然按“调用服务 -> 等待数据 -> 渲染 UI”的方式写。

### 学习重点

- 前端页面如何和服务层解耦。
- 没有真实后端时如何搭建可运行的业务流程。
- 为什么 mock 数据应该集中管理，而不是散落在页面里。

建议练习：在 `mockGraphql.js` 里模拟一次接口失败，然后在页面中显示 snackbar。

## 6. 电商业务流程

### 原项目体现

原项目是移动电商 App，包含首页、分类、商品详情、购物车、优惠券、会员、活动、CMS 和账号等模块。

### 新项目体现

对应文件：

- `src/override/features/home/HomeScreen.js`
- `src/core/features/catalog/CatalogScreen.js`
- `src/core/features/product/ProductDetailScreen.js`
- `src/core/features/cart/CartScreen.js`
- `src/core/features/coupons/CouponWalletScreen.js`
- `src/core/components/ProductCard.js`
- `src/core/components/LoyaltySummaryCard.js`
- `src/core/helpers/cartLogic.js`

新项目保留了一条完整的简化购物链路：

1. 首页查看会员信息和推荐商品。
2. Catalog 浏览商品。
3. 商品详情查看价格、库存和描述。
4. 加入购物车后更新全局购物车数量。
5. Cart 页面计算小计、折扣和总价。
6. Coupon Wallet 页面选择优惠券。

### 学习重点

- 页面组件、业务逻辑、mock 数据如何分离。
- 商品卡片如何复用在首页和列表页。
- 购物车计算为什么放在 helper 中，并用测试保护。

建议练习：新增一种优惠券规则，例如满 50 减 8。

## 7. 扫码与深链路由

### 原项目体现

原项目中扫码可以识别商品条码，也可以解析 Guardian URL，并把链接路由到商品、分类、CMS、活动、会员等页面。

### 新项目体现

对应文件：

- `src/core/features/scanner/ScannerScreen.js`
- `src/core/helpers/deepLink.js`
- `src/core/helpers/navigation.js`
- `__tests__/deepLink.test.js`

新项目用 Scanner Simulator 替代真实摄像头扫码。输入条码或 deep link 后，项目会解析内容并跳转到对应页面。

### 学习重点

- 扫码结果不应该直接写死跳转逻辑。
- 先解析成结构化 route，再交给 navigation 处理。
- 深链规则适合写成纯函数并配测试。

建议练习：新增一个 `guardian://category/skincare` 深链类型，并跳转到 Catalog。

## 8. 启动初始化与远程控制

### 原项目体现

原项目启动时会初始化 Firebase、埋点、Remote Config、Crashlytics、FCM、用户状态、购物车 ID、强制更新和维护模式等。

### 新项目体现

对应文件：

- `App.js`
- `src/core/hooks/useAppInitialize.js`
- `src/core/services/cache.js`
- `src/core/features/maintenance/MaintenanceScreen.js`

新项目保留了启动流程的结构，但去掉真实 SDK。`useAppInitialize` 模拟 App 启动，初始化 mock 用户、积分、远程配置和 loading 状态。

### 学习重点

- App 启动逻辑应该集中到 hook 或 service，而不是写散在页面里。
- 维护模式、强制更新、远程开关都可以通过全局状态控制根导航。
- 学习项目可以用 mock 初始化理解生产 App 的启动编排。

建议练习：给 `rxRemoteConfig` 增加一个 `forceUpdate: true` 场景，并做一个 Force Update 页面。

## 9. UI 与原样式适配

### 原项目体现

原项目有品牌色、底部 Tab 图标、toolbar、购物车 badge、商品卡片、会员信息卡等视觉元素。

### 新项目体现

对应文件：

- `src/override/styles/theme.js`
- `src/core/components/LearningToolbar.js`
- `src/core/components/TabBarIcon.js`
- `src/core/components/ProductCard.js`
- `src/core/components/LoyaltySummaryCard.js`
- `src/override/features/home/HomeScreen.js`

新项目尽量复刻原项目的视觉方向，但使用本地轻量组件实现，避免直接依赖原项目 SVG、图片和私有组件。

已经体现的样式点：

- 顶部绿色 toolbar。
- 搜索框、收藏、通知、购物车入口。
- 商品列表卡片。
- 会员信息区。
- 底部 Tab 五入口。
- 偏黄色选中态。
- 购物车 badge。

### 学习重点

- 如何在不复制生产资源的情况下学习原项目 UI 结构。
- 如何把样式集中在组件中，避免页面过度臃肿。
- 如何逐步把粗糙 mock UI 调整成更接近真实 App。

建议练习：把 `ProductCard` 改造成更像原项目商品卡，包括促销标签、原价、会员价和库存状态。

## 10. 测试与可维护性

### 原项目体现

生产项目中最容易出问题的是纯业务规则，例如购物车价格、优惠券、深链解析、会话状态和接口错误处理。

### 新项目体现

对应文件：

- `__tests__/cartLogic.test.js`
- `__tests__/deepLink.test.js`
- `__tests__/homeViewModel.test.js`
- `src/core/helpers/cartLogic.js`
- `src/core/helpers/deepLink.js`
- `src/core/helpers/homeViewModel.js`

新项目把关键业务逻辑抽成纯函数，并用 Jest 测试保护。

### 学习重点

- UI 可以先轻测，核心业务逻辑要重点测。
- 深链、优惠券、价格计算非常适合写单元测试。
- 学习项目里先建立测试习惯，比一开始追求完整生产环境更重要。

运行测试：

```bash
yarn test --runInBand
```

## 推荐学习路线

1. 阅读 `README.md`，完成安装和运行。
2. 阅读 `src/core/config/modules.js` 和 `src/override/config/modules.js`。
3. 阅读 `src/core/navigation/AppNavigator.js`、`AppStack.js`、`AppTabs.js`。
4. 阅读 `src/core/services/cache.js`，理解全局状态。
5. 阅读 `src/core/services/mockGraphql.js` 和 `src/core/data/mockData.js`。
6. 从首页开始体验商品浏览、详情、购物车、优惠券。
7. 阅读 `src/core/helpers/cartLogic.js` 与对应测试。
8. 阅读 `src/core/helpers/deepLink.js` 与对应测试。
9. 尝试做一个小练习：新增收藏、满减券或 category 深链。

## 原项目中暂未搬进学习项目的内容

这些内容生产项目很重要，但学习成本较高，所以当前版本先不引入：

- 真实 GraphQL endpoint。
- Firebase Analytics、Crashlytics、Performance、Remote Config。
- FCM 推送。
- Adjust、Facebook、TikTok、CDP 等营销归因 SDK。
- 真实相机扫码。
- 真实支付、配送、订单提交。
- 地图定位。
- WebView 复杂混合页面。
- 生产环境证书、签名、发布配置。

后续如果要继续学习，可以按“先 mock，再接真实 SDK”的方式逐步补充。
