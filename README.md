# 使命召唤 & 战地 配枪与梯队榜查询插件（astrbot_plugin_cod_meta）

> 适配游戏：使命召唤（Call of Duty / COD，包括黑色行动7、黑色行动6、现代战争III、现代战争II、现代战争4、战区2、战区3、DMZ）及战地6（BF6）。

本插件从 [MeetYourMeta](https://meetyourmeta.com) 获取武器梯队与配装数据。网站作者：[SoraYjy 的 Bilibili 个人空间](https://space.bilibili.com/19091214)。

这是社区制作的 AstrBot 插件，通过 MeetYourMeta 提供的接口查询梯队武器和枪械配装，并以文本形式返回结果。插件无需启动浏览器或安装 Playwright。

本插件及获取的数据仅供非商业用途。展示数据时保留其原始内容，不删改数据字段或配装内容；每条查询结果末尾均标注「数据来源：MeetYourMeta」。

插件仅调用现有的武器列表类只读接口，不请求用户数据或其他接口。该接口没有公开的可用性或兼容性承诺，字段和结构可能随时调整；接口异常或响应结构变化时，插件会返回可读错误提示。缓存中的旧数据仅在刷新失败时用于维持查询。

如网站作者对数据使用、署名或项目发布有任何意见，请通过 GitHub 项目页面联系我，我会及时沟通并按要求处理。

## 当前支持

| 命令版本 | 游戏版本 | API 状态 |
| --- | --- | --- |
| `cod19` / `mwii` / `mw2` / `19` | 现代战争II（MWII） | 已接入 |
| `cod20` / `mwiii` / `mw3` / `20` | 现代战争III（MWIII） | 已接入 |
| `cod21` / `bo6` / `21` | 黑色行动6（BO6） | 已接入 |
| `cod22` / `bo7` / `22` | 黑色行动7（BO7） | 已接入 |
| `cod23` / `mwiv` / `mw4` / `23` | 现代战争4（COD23，本体 MP） | 已接入 |
| `bf6` / `战地6` | 战地6本体 | 已接入 |
| `bf6 redsec` / `战地6 大逃杀` | 战地6 REDSEC | 已接入 |
| `wz2` / `战区2` | 战区2 | 已接入 |
| `wz3` / `战区3` | 战区3（WZ） | 已接入 |
| `dmz` | DMZ 配装清单 | 已接入 |

默认版本为 COD23 本体（MP）。可在 AstrBot 插件配置中选择 `/cod` 的默认版本：COD19、COD20、COD21、COD22、COD23 本体、战地6本体、战地6 REDSEC、WZ2、WZ3 和 DMZ 均为独立选项。

## 安装

1. 将 `astrbot_plugin_cod_meta` 文件夹放入 AstrBot 的插件目录。
2. 确认目录中有 `main.py`、`metadata.yaml` 和 `requirements.txt`。
3. 在 AstrBot 插件管理中加载或重载插件。

插件只使用 Python 标准库和 AstrBot API，不需要额外安装 Python 包。运行环境需要能够访问 `www.meetyourmeta.com`。

## 使用方法

```text
/cod [版本] [梯队或枪械名]
```

### 查询梯队武器

```text
/cod t0
/cod bo7 t1
/cod cod22 t0.5
/cod 21 t2
/cod 23 t0
/战地6 t0
/战地6 redsec t0
/wz2 t0
/wz3 t0
/dmz t0
```

梯队查询只返回对应梯队的武器名称。`t0` 是宽松榜单入口，会列出该版本实际存在的 T0、T0.5 和 T1 梯队；其他梯队参数按指定档位查询。可用梯队以 API 当前返回的数据为准，例如 `t0.5`、`t1`、`t1.5`、`t2`。

### 查询枪械配装

```text
/cod rk-9
/cod bo7 MXR-17
/cod cod21 XM4
/cod mwiii AMR9
/cod23 奥里斯8.6
/战地6 M123K
/战地6 redsec 枪械名
/wz2 ISO45
/wz3 枪械名
/dmz ISO45
```

在 AstrBot WebUI 的插件设置中，可以通过“`/cod` 默认查询版本”下拉框选择 `/cod t0` 或 `/cod 枪名` 默认使用的游戏/模式。`/cod 23 ...`、`/cod23 ...`、`/wz2 ...`、`/wz3 ...` 和 `/dmz ...` 也可显式指定对应版本，不受默认值影响。

枪械名称支持中文名或英文名的部分匹配。若同一名称匹配到多个条目，当前版本会返回第一个匹配项。结果包含已收录方案的配件、配装码和备注；没有配装数据时会返回提示。

### 查询完整梯队榜

```text
/cod bo7 榜单
```

`榜单`、`总榜`、`梯队`、`强度榜`会按 API 返回的梯队顺序列出各梯队武器。

## 数据与故障说明

- 数据来自 MeetYourMeta API。
- 每个版本和模式分别持久缓存 API 响应。缓存未满 6 小时时直接读取本地数据；超过 6 小时后，下一次相关查询才请求新数据并更新缓存。机器人重启后缓存仍保留。
- 并发查询通过异步锁合并，避免缓存过期时同时发出重复请求。
- 刷新失败时若有旧缓存，会继续使用旧数据；没有可用缓存时会返回查询失败提示。请检查 AstrBot 主机网络和插件日志。
- 缓存文件保存在 AstrBot 数据目录 `data/plugin_data/astrbot_plugin_cod_meta/`，便于数据迁移与审计；不要将缓存文件提交到 GitHub。
- `requirements.txt` 不包含第三方依赖；无需执行 `playwright install`。

## 文件结构

```text
astrbot_plugin_cod_meta/
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── requirements.txt
├── .gitignore
└── README.md
```
