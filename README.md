# COD 各代配枪与梯队查询（AstrBot）

本插件从 [MeetYourMeta](https://meetyourmeta.com) 获取武器梯队与配装数据。网站作者：SoraYjy(https://space.bilibili.com/19091214)。

这是社区制作的非官方 AstrBot 插件，通过 MeetYourMeta 提供的接口查询梯队武器和枪械配装，并以文本形式返回结果。插件无需启动浏览器或安装 Playwright。

如网站作者对数据使用、署名或项目发布有任何意见，请通过 GitHub 项目页面联系我，我会及时沟通并按要求处理。

## 当前支持

| 命令版本 | 游戏版本 | API 状态 |
| --- | --- | --- |
| `cod22` / `bo7` / `22` | 黑色行动7（BO7） | 已接入 |
| `cod21` / `bo6` / `21` | 黑色行动6（BO6） | 已接入 |
| `cod20` / `mwiii` / `mw3` / `20` | 现代战争III（MWIII） | 已接入 |
| `cod19` / `mwii` / `mw2` / `19` | 现代战争II（MWII） | 已接入 |
| `bf6` / `战地6` | 战地6本体（默认） | 已接入 |
| `bf6 redsec` / `战地6 大逃杀` | 战地6 REDSEC | 已接入 |
| `wz2` / `战区2` | 战区2 | 已接入 |

默认版本为 BO7。COD23、DMZ、战区3和三角洲目前尚未接入。

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
/战地6 t0
/战地6 redsec t0
/wz2 t0
```

梯队查询只返回对应梯队的武器名称。可用梯队以 API 当前返回的数据为准，例如 `t0`、`t0.5`、`t1`、`t1.5`、`t2`。

### 查询枪械配装

```text
/cod rk-9
/cod bo7 MXR-17
/cod cod21 XM4
/cod mwiii AMR9
/战地6 M123K
/战地6 redsec 枪械名
/wz2 ISO45
```

枪械名称支持中文名或英文名的部分匹配。若同一名称匹配到多个条目，当前版本会返回第一个匹配项。结果包含已收录方案的配件、配装码和备注；没有配装数据时会返回提示。

### 查询完整梯队榜

```text
/cod bo7 榜单
```

`榜单`、`总榜`、`梯队`、`强度榜`会按 API 返回的梯队顺序列出各梯队武器。

## 数据与故障说明

- 数据来自 MeetYourMeta API，API 更新后查询结果会随之变化。
- 插件在运行期间缓存每个版本首次取得的数据；重载插件后缓存清空。
- API 不可访问、响应格式变化或站点暂时故障时，插件会返回查询失败提示。请检查 AstrBot 主机的网络连接及插件日志。
- `requirements.txt` 不包含第三方依赖；无需执行 `playwright install`。

## 文件结构

```text
astrbot_plugin_cod_meta/
├── main.py
├── metadata.yaml
├── requirements.txt
└── README.md
```
