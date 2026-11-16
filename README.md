# CycleHUD 法务页（GitHub Pages 源）

App Store 要求的两样东西的落地页：**隐私政策 URL** 与**支持 URL**。本目录是一个**独立的 git 仓库**，不属于 App 主仓库（主仓库的 `.gitignore` 已忽略 `legal/`），因为它要单独推到 GitHub 并由 Pages 托管。

## 为什么独立成仓

- GitHub Pages 按仓库托管静态站：Pages 的发布单元是仓库，不是目录。
- 法务页的更新节奏与 App 发版无关（改文案、改生效日期都不该触发一次 App 构建）。
- 页面一旦上线就是审核与用户都在用的对外地址，URL 必须稳定；独立仓库让「App 主仓重构」不会顺带改掉这个地址。

## 目录与约定

```
index.html                 语言选择（唯一入口，提交给 ASC 的是它下面各语言的子页）
.nojekyll                  关掉 Jekyll 处理，静态文件按原样发布
zh-Hans/  zh-Hant/  en/  ja/
  privacy-policy.html      四种语言的隐私政策
  support.html             四种语言的支持页
```

**四条硬约定**（改页面时逐条对一遍，否则会出现「中文页说 A、英文页说 B」这种审核最爱抓的漏洞）：

1. **四种语言的正文必须同构**：同样的章节数、同样的结论。翻译可以换语气，不能换事实。
2. **改动收集范围或联网行为时**，先改文案，再改页面顶部的「生效日期」，四条语言同步改。
3. **页面自包含**：不引外部字体、脚本、统计、CDN。法务页要在任何网络条件下都能读，而且不能自己变成一个新的数据收集点。
4. **联系方式只有一个**（`rankor@sina.com`），四条语言一致，且必须与 App Store Connect 里填写的一致。

## 部署（本地已就绪，手工推送）

本仓库已 `git init` 并做过首次提交，**没有远端**。上线分三步：

1. 在 GitHub 新建空仓库，建议名 `cyclehud-legal`（公开必须是公开仓，Pages 才能免费用）。
2. 加远端并推送：

   ```sh
   cd /Users/niebo/projs-swift/m2/legal
   git remote add origin git@github.com:<账号>/cyclehud-legal.git
   git push -u origin main
   ```

3. 仓库 **Settings → Pages → Build and deployment**：Source 选 `Deploy from a branch`，Branch 选 `main`、目录选 `/ (root)`，保存。首次生效通常 1–2 分钟。

拿到的地址形如：

```
https://<账号>.github.io/cyclehud-legal/
```

该地址就是 **App Store Connect 的「隐私政策 URL」**，也是 App 内设置卡「隐私政策」那一行要指向的地址。

## 拿到 URL 之后：反填进 App（别手改）

不要手动编辑 `AppSupportInfo.swift`，用脚本改，它会校验锚点唯一并顺手跑发布守卫：

```sh
cd /Users/niebo/projs-swift/m2
python3 scripts/set_support_info.py \
  --email rankor@sina.com \
  --privacy-url https://<账号>.github.io/cyclehud-legal/zh-Hans/privacy-policy.html
```

脚本把两个值写进 `m2/Support/AppSupportInfo.swift`，然后调用 `scripts/check_release_config.py`；转绿即表示「值已填 + 形状合法 + 许可证全文齐备」。填完记得：

- App Store Connect 的隐私政策 URL 填**同一个**地址（审核会比对，不一致会被要求说明）。
- 真机点一次设置卡里的「隐私政策」与「支持邮箱」，确认外链能开、邮件能唤起——脚本验不了这一步。

**隐私政策 URL 建议指向具体语言的正文页**（如 `zh-Hans/privacy-policy.html`），而不是 `index.html`：审核员点进去应当直接看到条文，而不是再点一次语言选择。

## 更新流程

1. 改对应语言的 `privacy-policy.html` / `support.html`（四种语言一起改）。
2. 更新页面 `<p class="meta">` 里的生效日期。
3. 本地 `python3 -m http.server` 起一个静态服务，逐页点开检查四语言互链（相对路径 `../en/...` 写错时在本地就会 404，不要等上线才发现）。
4. 提交并推送；Pages 会自动重新发布。
5. 若变更涉及「收集了什么」或「是否联网」，同步检查 App 内的 `PrivacyInfo.xcprivacy` 与 `AppSupportInfo` 是否仍然一致——页面与包内声明冲突，属于审核可直接验证的不一致。
