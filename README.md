# CS2 Major Calendar

PGL Major Singapore 2026 的比赛日历。订阅以后，比赛会出现在你的日历里，时间会按你所在的时区自动换算，改期也会跟着同步。

## 订阅链接

| 日历 | 链接 |
| --- | --- |
| Apple 日历（iPhone / Mac） | `webcal://raw.githubusercontent.com/ChihayaAnon9888/-Singapore-Major-Match-Calendar-/main/major.ics` |
| Google 日历 / Outlook | `https://raw.githubusercontent.com/ChihayaAnon9888/-Singapore-Major-Match-Calendar-/main/major.ics` |

## 操作流程

### Apple 日历（iPhone / iPad / Mac）

1. 复制上面的 `webcal://` 链接，粘贴到 Safari 的地址栏里打开。
2. 在弹出的窗口里点 **订阅**，然后点 **添加**。
3. 想收到赛前提醒的话，在该日历的设置里打开 **活动提醒**（Event Alerts）。日历自带赛前 30 分钟的提醒。
4. 建议把刷新频率改成 **每小时**：Mac 上右键这个日历 → **获取信息** → **自动刷新**。

也可以手动添加：iPhone 上进入 **设置 → 日历 → 账户 → 添加账户 → 其他 → 添加已订阅的日历**，然后粘贴链接。

### Google 日历

只能在**电脑网页**上订阅，手机 App 里没有这个选项。在电脑上订阅之后，手机会自动同步。

1. 打开 [calendar.google.com](https://calendar.google.com)。
2. 点左侧 **其他日历** 旁边的 **＋** → **通过网址添加**（From URL）。
3. 粘贴上面的 `https://` 链接，点 **添加日历**。
4. **设置提醒**：Google 不会读取订阅日历里自带的提醒，需要自己加。点该日历旁边的 **⋮** → **设置和共享** → **活动通知**，添加"30 分钟前"。
5. 在 iPhone 自带的日历里看 Google 日历：用手机打开 [calendar.google.com/calendar/syncselect](https://calendar.google.com/calendar/syncselect)，勾选这个日历后保存。

> Google 大约每 8–24 小时刷新一次订阅日历，临时改期可能会延迟显示。

### Outlook

1. 打开 [Outlook 日历](https://outlook.live.com/calendar/)。
2. 点 **添加日历** → **从 Web 订阅**。
3. 粘贴上面的 `https://` 链接，填一个日历名称，然后点 **导入**。

### 注意事项

- 日历里的时间以 UTC 储存，打开时会按你的时区显示。例如开幕战 `2026-11-24 04:00 UTC` 对应北京时间 11 月 24 日 12:00。
- 还没公布开赛时间的比赛不会出现在日历里，公布时间后会自动补上。
- 请用**订阅**的方式添加，不要下载 `.ics` 文件导入。下载导入只是一次性的，之后改期不会同步。

## 维护者：更新赛程

```sh
./update.sh
```

这条命令会从 Liquipedia 拉取最新赛程，重新生成 `major.ics` 并推送到 GitHub。赛程没有变化时不会推送。比赛期间建议每天运行一两次。

## 部署 GitHub Pages（可选）

仓库里还带了一个静态网页版，由 `.github/workflows/pages.yml` 构建。要启用的话：在 **Settings → Pages** 中把 Source 设为 **GitHub Actions**，然后在 Actions 里运行 **Sync Major schedule and deploy Pages**。这一步需要账户能正常使用 GitHub Actions。

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
