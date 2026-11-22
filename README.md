# CS2 Major Calendar

适用于 GitHub Pages 的静态 CS2 Major 日历。首页提供 Apple、Google 和 Outlook 三个订阅入口，并用访客设备的时区显示下一场比赛。日历含已知开赛时间和赛前 30 分钟提醒。

## 订阅链接（不用 GitHub Pages）

- Apple 日历：`webcal://raw.githubusercontent.com/ChihayaAnon9888/-Singapore-Major-Match-Calendar-/main/major.ics`
- Google / Outlook（从网址添加）：`https://raw.githubusercontent.com/ChihayaAnon9888/-Singapore-Major-Match-Calendar-/main/major.ics`
- 更新赛程：运行 `./update.sh`，会拉取最新赛程、重新生成 `major.ics` 并推送。

## 部署 GitHub Pages

1. 新建公开仓库，将本项目解压后的文件提交到仓库根目录的 `main` 分支。请保留隐藏的 `.github` 目录。
2. 在仓库的 **Settings → Pages → Build and deployment** 中，将 **Source** 设为 **GitHub Actions**。
3. 打开 **Actions → Sync Major schedule and deploy Pages**，运行一次 **Run workflow**。部署完成后，Pages 设置页会显示公开网址。
4. 将网站链接发给观众。订阅源位于公开网址下的 `major.ics`。直接打开这个地址也能取得一次性导入文件。

[GitHub Pages 发布说明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## 订阅和提醒

- **Apple** 打开 Apple Calendar 的订阅确认。iPhone 上可在该日历的设置中开启 **Event Alerts**。
- **Google** 打开 Google Calendar 的 **From URL** 页面，并尝试复制订阅地址。请在电脑网页中粘贴地址并确认。
- **Outlook** 打开 Outlook 日历，并尝试复制订阅地址。选择 **Add calendar → Subscribe from web** 后粘贴地址并确认。
- 日历里的时间以 UTC 储存，客户端按日历或设备时区转换。例如新加坡 Major 开幕场 `2026-11-24T04:00:00Z` 对应多伦多 11 月 23 日 23:00、中国 11 月 24 日 12:00。
- GitHub Actions 每 12 小时检查一次赛程。订阅客户端按自身的刷新频率接收改期，提醒取决于客户端和账号设置。下载文件是一次性导入。

[Apple 日历帮助](https://support.apple.com/en-mide/guide/iphone/-iph3d1110d4/ios) · [Google 日历帮助](https://support.google.com/calendar/answer/37100) · [Outlook 日历帮助](https://support.microsoft.com/en-gb/outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web?nochrome=true)

## 数据和更新

- 当前赛事为 **PGL Major Singapore 2026**。初始快照含 107 个赛程位置，其中 68 个有开赛时间。未公布时间的比赛会在有时间后进入订阅源。
- 自动同步使用 Liquipedia 的公开 MediaWiki Revisions API，一次获取四个阶段。订阅不需要网站账号或 API 密钥。GitHub Actions 用仓库 URL 作为 API 调用的联系信息。
- HLTV 用于赛事参考链接及人工录入的暂定时段。自动改期以 Liquipedia 的时间为准。赛事配置和暂定时段在 `data/major.json`。
- 普通推送和手动运行会同步赛程。定期运行在开赛前 14 天至结束后 2 天之间发布更新。接口失败会中止该次部署，已发布的日历继续可用。首次部署遇到接口故障时，可以手动勾选 `use_snapshot` 发布内置赛程。
- 换届时更新 `data/major.json` 的赛事及阶段配置，并重新生成 `data/schedule.json`。保留 `major.ics` 的发布地址，既有订阅就能继续读取更新后的赛程。

[Liquipedia API 条款](https://liquipedia.net/api-terms-of-use) · [HLTV 条款](https://www.hltv.org/terms) · [赛事官网](https://www.pglesports.com/cs2/pgl-major-singapore-2026/)

## 本地运行

需要 Python 3.11 或更新版本。使用已附带的快照即可离线构建。

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

访问 [本地预览](http://localhost:8000)。刷新赛程时，将下面的地址换成实际的公开仓库 URL。

```sh
python3 scripts/sync.py --contact-url https://github.com/OWNER/cs2-major-calendar
python3 scripts/build.py
```

项目代码采用 MIT 许可证。Liquipedia 贡献者提供的赛程数据及其改编以 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) 发布，具体页面来源见每场比赛的数据和日历事件。
