---
name: mijia
description: |
  控制小米 / 米家智能家居设备：通过 mijiaAPI CLI（已用 uv tool 全局安装）调云端 API 完成开关、亮度、色温、颜色、场景、耗材查询、统计数据等。
  三档操作策略（按省力程度从高到低）：
  1. `--run "..."` 自然语言走小爱音箱（最省事，需家里有小爱）
  2. `set/get --dev_name "X" --prop_name Y` 直控属性（精准，可脚本化）
  3. `--run_scene "X"` 触发预设场景

  何时触发：用户说"开 / 关 / 打开 / 关闭 X 灯 / 插座 / 空调"、"调亮度 / 色温 / 颜色"、"列出我的设备 / 家庭"、"执行 / 跑 X 场景"、"看下耗材 / 滤芯 / 用电量"、"控制米家 / 小米 / Yeelight / 小爱设备"。

  不触发：HomeKit / Apple Home（不是米家协议）；非账号绑定的本地直连（如 miio LAN、ESPHome、Tasmota）；询问"米家是什么"的纯科普问题。
---

# mijia · 米家设备控制

## 首次使用（用户做一次）

CLI 已通过 `uv tool install mijiaAPI` 装好（在 PATH 里，版本 3.0.5+）。还差一步扫码登录：

```bash
mijiaAPI --list_homes
```

终端会打印 QR 码，用米家 APP 扫描完成认证。认证落到 `~/.config/mijia-api/auth.json`，后续自动复用。

**未登录时不要替用户跑这步** —— QR 需要手机扫，agent 看不到也帮不上。直接告诉用户去跑这条命令。

## 三档操作策略（从轻到重，按需降档）

### 档 1：有小爱音箱 → 走 `--run`（最省力）

把用户的自然语言原样透传，让小爱解析。**不需要先列设备、不需要查属性、不需要想 piid**。

```bash
mijiaAPI --run "打开卧室台灯，亮度调到 30"
mijiaAPI --run "关闭所有灯"
mijiaAPI --quiet --run "客厅空调调到 26 度"               # --quiet：小爱不语音回复
mijiaAPI --wifispeaker_name "卧室小爱" --run "..."        # 指定哪台小爱执行
```

**用户没说有没有小爱时可以直接试**，失败立刻退到档 2，**不要重试档 1**。

### 档 2：直接控属性（精准、可脚本化）

**标准三步流程，看不懂设备时一定要走完**：

1. `mijiaAPI -l` —— 列设备，拿 `dev_name`（米家 APP 里的名字）和 `model`（如 `yeelink.light.lamp4`）
2. `mijiaAPI --get_device_info <model>` —— 查这个 model 支持哪些 `prop_name`，记下类型/范围
3. `mijiaAPI get/set --dev_name "<名字>" --prop_name <属性> [--value <值>]`

**首选 `--dev_name`，避免用 `--did`**。`--did` 要先 grep 才能拿到，浪费一轮调用；`--dev_name` 是人能记住的名字，直接用。

```bash
# get
mijiaAPI get --dev_name "客厅台灯" --prop_name brightness
mijiaAPI get --dev_name "客厅台灯" --prop_name on

# set
mijiaAPI set --dev_name "客厅台灯" --prop_name on --value True
mijiaAPI set --dev_name "客厅台灯" --prop_name brightness --value 60
mijiaAPI set --dev_name "客厅台灯" --prop_name color-temperature --value 4000
```

**值类型注意**：

| 属性类型 | 怎么传 | 备注 |
|---|---|---|
| bool | `True` / `False` | 首字母大写（Python 风） |
| int / 百分比 | 直接数字 `60` | 范围按设备规格，**不要瞎猜** |
| 色温 | 整数开尔文 `4000` / `6500` | 范围由 `--get_device_info` 给出 |
| 颜色 RGB | 整数（0xRRGGBB 转十进制） | 红=16711680、绿=65280、蓝=255 |

值越界会报错。**先 `--get_device_info` 看 max/min，再 `set`**。

### 档 3：场景 / 耗材 / 家庭

```bash
mijiaAPI --list_scenes                          # 列场景
mijiaAPI --run_scene "回家" "睡眠模式"          # 跑一个或多个场景
mijiaAPI --list_consumable_items                # 耗材（滤芯、灯泡寿命等）
mijiaAPI --list_homes                           # 家庭列表
```

## 常见错误对照

| 报错 | 原因 | 修法 |
|---|---|---|
| `LoginError` / 401 | 认证过期 | `rm ~/.config/mijia-api/auth.json && mijiaAPI --list_homes` 重扫码 |
| `DeviceNotFoundError` | 名字拼错、不在当前账号、设备离线 | `mijiaAPI -l` 核对 dev_name（区分大小写、空格） |
| `MultipleDevicesFoundError` | 同名多设备（如两个"台灯"） | 改用 `--did` 唯一指定，或在米家 APP 改名 |
| `DeviceSetError` 越界 | 值超 max/min | `mijiaAPI --get_device_info <model>` 查范围 |
| `ValueError: 属性名不支持` | prop_name 拼错或不存在 | `--get_device_info` 看真实属性名（如 `color-temperature` vs `ct`） |
| `--run` 无反应 | 没小爱音箱 / 音箱名错 | 立即退档 2 直控，**不要重试档 1** |

## 不要做

- 不要自动跑 `--list_homes` 试探登录 —— 没登录会卡在 QR 码，agent 死等
- 不要替用户瞎猜 brightness / 色温的"合理"默认值 —— 不同设备 max 不同，要么先 `get` 当前值，要么问用户
- 不要 `pip install mijiaAPI` 重装 —— 已用 `uv tool install` 装在 `~/.local/share/uv/tools/`，重装会冲突
- 不要把档 1 失败当成"设备不存在" —— 多半是没小爱音箱，退档 2 直控

## 调试技巧

```bash
MIJIA_LOG_LEVEL=DEBUG mijiaAPI -l               # 看完整 HTTP 调用过程
mijiaAPI --get_device_info yeelink.light.lamp4  # 看 model 全量规格
```

## 参考

- 上游 SDK：https://github.com/Do1e/mijia-api
- 设备规格在线查询：https://home.miot-spec.com/
