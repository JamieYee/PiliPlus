# PiliPlus iOS 自动构建

本仓库仅保存用于构建和签名 PiliPlus iOS 安装包的 GitHub Actions 工作流。

构建时会从 [bggRGjQaUbCoE/PiliPlus](https://github.com/bggRGjQaUbCoE/PiliPlus) 临时拉取指定版本的源码，源码不会复制到本仓库的当前文件中。

## 构建方式

- 手动运行时，可以构建上游的任意分支、Tag 或 Commit。
- 修改 `main` 分支上的 iOS workflow 时，会自动执行一次只上传 Artifact、不发布 Release 的验证构建。
- 每天北京时间 04:23 检查上游最新的正式 Release Tag。只有你的仓库中不存在该 Tag 对应的 Release 时，才会 checkout 该 Tag、执行签名构建并创建同名 Release；上游普通的 `main` 提交不会触发定时打包。
- 每次成功构建都会上传签名后的 IPA Artifact，并保留 30 天。
- 手动运行时，开启 `publish_release` 会同时创建 GitHub Release；关闭时只上传 Artifact。
- 定时构建直接使用上游 Tag 作为本仓库的 Release Tag。手动构建未填写 Release Tag 时，会按 `ios-v<上游版本>-<上游提交>` 自动生成。
- 定时构建的 Release 标题和 IPA 文件名均使用上游 Tag，例如 `PiliPlus iOS 2.1.2.3` 和 `PiliPlus_iOS_2.1.2.3.ipa`。

## Actions 配置

请在 **Settings → Secrets and variables → Actions** 中配置以下内容。

### Repository secrets

- `IOS_CERT_P12_BASE64`：经过 Base64 编码的 Apple 签名证书（`.p12`）。
- `IOS_CERT_PASSWORD`：`.p12` 文件的密码。
- `IOS_PROVISIONING_PROFILE_BASE64`：经过 Base64 编码的 provisioning profile（`.mobileprovision`）。

### Repository variables

- `IOS_BUNDLE_ID`：provisioning profile 所覆盖的 Bundle ID。使用精确且非通配符的 profile 时可以留空，工作流会自动读取。
- `IOS_EXPORT_METHOD`：可填写 `app-store-connect`、`release-testing`、`enterprise`、`debugging` 或 `validation`；留空时默认使用 `release-testing`。

工作流不会输出证书、密码或 provisioning profile 的内容。签名文件只会临时写入 GitHub 托管的构建机器，并在构建结束后删除。

## 手动构建

打开 **Actions → Build signed iOS IPA → Run workflow**：

1. 在 `upstream_ref` 中填写要构建的上游分支、Tag 或 Commit，默认是 `main`。
2. 开启 `publish_release` 时，构建成功后会创建 Release 并附加 IPA；关闭时只生成可在本次运行页面下载的 Artifact。
3. `release_tag` 可以留空，由工作流根据上游版本和 Commit 自动生成。

PiliPlus 应用本身由上游仓库维护。本仓库只负责个人 iOS 签名构建和 IPA 发布，应用功能问题请前往上游仓库反馈。

## OTA 在线安装与更新

GitHub Pages 会提供一个适用于 Ad Hoc 签名的 OTA 安装页：

<https://jamieyee.github.io/PiliPlus-iOS-Build/>

- 签名构建工作流成功结束后，OTA 工作流会读取本仓库最新 Release 中的 IPA。
- 工作流会直接从 IPA 的 `Info.plist` 提取真实的 Bundle ID、应用版本和构建号，并生成 `manifest.plist`，不会把上游 Tag 错当成应用内部版本。
- 请在已登记 UDID 的 iPhone 或 iPad 上使用 Safari 打开安装页，然后点击“在此 iPhone / iPad 上安装”。
- 更新时可再次点击安装。只有 Bundle ID 和签名团队保持一致、provisioning profile 仍有效且新 IPA 的构建号更高时，系统才能覆盖安装并保留应用数据。
- GitHub Release 中的 IPA 仍然保留，OTA 页面只是提供更方便的系统安装入口。
