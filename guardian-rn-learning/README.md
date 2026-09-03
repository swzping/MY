# Guardian RN Learning

这是一个轻量级 React Native CLI 风格学习项目，提炼自 `/Users/edy/Documents/fix/app-guardian` 的架构和核心功能思路。

它保留原项目最值得学习的工程点，同时用 mock 数据替代生产环境服务：

- `src/core` 与 `src/override` 分层架构。
- `@app` alias 优先解析 override 文件，再回退到 core 文件。
- React Navigation 登录栈、主应用栈和底部 Tab。
- 使用 Apollo reactive variables 管理全局 App 状态。
- Mock GraphQL 服务层。
- 登录态、商品目录、商品详情、购物车、优惠券钱包、扫码模拟、深链跳转和维护模式。

## 安装与运行流程

### 1. 进入项目目录

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
```

### 2. 安装依赖

这个学习项目是 React Native CLI 项目。第一次运行前先安装 JS 依赖：

```bash
yarn install --ignore-scripts
```

这里使用 `--ignore-scripts` 是为了跳过依赖包里的自动脚本，安装更可控。

### 3. 安装 iOS Pods

如果要运行 iOS，需要先安装 CocoaPods 依赖：

```bash
yarn pods
```

这个命令实际执行的是：

```bash
cd ios
LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 pod install
```

如果你看到 Ruby/Bundler 版本错误，可以先不要使用 `bundle install`，直接执行上面的 `pod install`。本机已验证 `pod 1.16.2` 可以安装成功。

### 4. 先跑测试

```bash
yarn test --runInBand
```

正常结果应该看到：

```text
Test Suites: 2 passed, 2 total
Tests:       7 passed, 7 total
```

### 5. 启动 Metro

React Native 需要先启动 Metro dev server。建议单独开一个终端窗口运行：

```bash
yarn start
```

看到类似下面的信息，说明 Metro 已经启动：

```text
Welcome to React Native v0.79
Dev server ready
```

### 6. 运行 iOS App

保持 Metro 终端不要关闭，再打开第二个终端进入同一个项目目录。

默认命令会启动 `iPhone 16` 模拟器，避免误选真机导致签名错误：

```bash
yarn ios
```

如果你的机器没有 `iPhone 16` 模拟器，可以先查看可用模拟器：

```bash
xcrun simctl list devices available
```

然后手动指定一个存在的模拟器，例如：

```bash
yarn react-native run-ios --simulator "iPhone 15 Plus"
```

如果你确实想跑到真机，需要先在 Xcode 里配置 Apple Development Team，然后执行：

```bash
yarn ios:device
```

### 7. 运行 Android App

如果本机已经配置好 Android Studio、Android SDK 和模拟器，可以运行：

```bash
yarn android
```

### 8. 如果只是学习代码

如果你暂时不想配置 iOS/Android 原生环境，可以先只做这些步骤：

```bash
cd /Users/edy/Documents/MY/guardian-rn-learning
yarn install --ignore-scripts
yarn test --runInBand
```

然后按下面的“关键文件”和“建议体验顺序”阅读源码。真正上模拟器运行时，再补齐本机 React Native 原生环境。

### 常见问题

- `react-native start` 提示缺少 CLI：确认 `package.json` 里有 `@react-native-community/cli`，然后重新执行 `yarn install --ignore-scripts`。
- `yarn ios` 提示找不到 `Pods-GuardianLearningApp.debug.xcconfig`：先运行 `yarn pods`。
- `yarn ios:device` 提示需要 development team：这是跑真机需要签名。打开 `ios/GuardianLearningApp.xcworkspace`，在 Signing & Capabilities 里选择你的 Apple Team。
- `yarn ios` 找不到 `iPhone 16`：用 `xcrun simctl list devices available` 找一个你本机存在的模拟器，再手动指定 `--simulator`。
- `yarn android` 失败：通常是 Android SDK、模拟器或 Gradle 原生工程配置问题。这个学习项目重点是理解原项目架构，不包含完整生产 Android 配置。
- 只想验证逻辑是否正常：运行 `yarn test --runInBand` 即可。

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
