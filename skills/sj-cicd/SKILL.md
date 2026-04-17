---
name: sj-cicd
description: |
  Jenkins CI/CD 操作工具，通过 sj-cicd CLI 管理构建与部署。
  触发：用户提到"部署"、"发布"、"构建"、"deploy"、"build"、"trigger" + 项目名；
  "构建状态"、"构建日志"、"构建历史"、"build status"、"build log"；
  "停止构建"、"取消构建"、"stop build"、"abort build"；
  "列出 Jenkins 任务"、"list Jenkins jobs"、"Jenkins 上有哪些项目"；
  或出现 DEV-WEB-*、DEV-e-commerce-*、TEST_DEV-WEB-* 等任务名前缀时触发。
  不触发：GitHub Release 发布流程（使用 release skill）；与 Jenkins 无关的 CI/CD 讨论。
---

# Jenkins CI/CD 操作

通过 `sj-cicd` CLI 工具操作 Jenkins。所有命令输出结构化 JSON。

## 前置检查

每次操作前确认：

```bash
# 1. CLI 是否可用
which sj-cicd || pip install sanjiu-jenkins-cli

# 2. 认证是否有效
sj-cicd auth
```

认证失败时，引导用户：
- 创建 API Token: `<JENKINS_URL>/me/configure` → API Token → Add new Token
- 配置到 `~/.jenkins-cli` 或环境变量 `JENKINS_URL` / `JENKINS_USER` / `JENKINS_TOKEN`

## 命令速查

| 命令 | 用途 | 示例 |
|------|------|------|
| `sj-cicd list [FILTER]` | 列出任务（正则过滤）| `sj-cicd list DEV-WEB` |
| `sj-cicd info JOB` | 查看任务参数 | `sj-cicd info DEV-WEB-xiaoy-zhibo-wx` |
| `sj-cicd build JOB [PARAMS...]` | 触发构建 | `sj-cicd build JOB ENV=test BranchName=master` |
| `sj-cicd status JOB [NUMBER]` | 构建状态 | `sj-cicd status JOB` (默认最近一次) |
| `sj-cicd history JOB [-n N]` | 构建历史 | `sj-cicd history JOB -n 5` |
| `sj-cicd log JOB NUMBER [--follow]` | 构建日志 | `sj-cicd log JOB 42 --follow` |
| `sj-cicd stop JOB NUMBER` | 停止构建 | `sj-cicd stop JOB 42` |
| `sj-cicd auth` | 验证认证 | `sj-cicd auth` |

## 核心工作流

### 工作流 1: 触发构建并监控（部署/发布）

这是最常见的操作，**必须按顺序执行**：

1. **获取任务参数** — `sj-cicd info <job>`
2. **展示参数给用户确认** — 列出所有参数的 choices/默认值，让用户选择
3. **用户确认后触发** — `sj-cicd build <job> KEY1=val1 KEY2=val2 --wait --follow-log`
   - `--wait`: 等待构建完成（默认）
   - `--follow-log`: 实时流式输出日志
   - `--no-wait`: 仅触发不等待
4. **报告结果** — 成功/失败 + 耗时

**关键规则**: 触发构建前 **必须** 先 `info` 展示参数，与用户确认后才执行。这是不可逆操作。

### 工作流 2: 查看构建状态/历史

```bash
# 最近一次构建
sj-cicd status <job>

# 最近 N 次构建
sj-cicd history <job> -n 5
```

### 工作流 3: 排查构建失败

1. `sj-cicd history <job>` — 找到失败的构建号
2. `sj-cicd log <job> <number>` — 获取完整日志
3. 分析日志中的错误信息，向用户解释原因和建议

### 工作流 4: 停止构建

1. `sj-cicd status <job>` — 确认 `building: true`
2. 与用户确认是否停止（不可逆）
3. `sj-cicd stop <job> <number>`
4. 再次 `status` 确认已停止

## 决策树

```
用户请求
├─ 提到具体任务名
│  ├─ "部署/发布/构建/build/deploy" → 工作流 1（触发构建）
│  ├─ "状态/结果/status" → 工作流 2（查看状态）
│  ├─ "日志/log/报错/失败" → 工作流 3（排查失败）
│  ├─ "停止/取消/stop/abort" → 工作流 4（停止构建）
│  └─ "参数/详情/info" → sj-cicd info
├─ 未提到具体任务名
│  ├─ "列出/list/有哪些" → sj-cicd list
│  ├─ "搜索/查找 xxx" → sj-cicd list <filter>
│  └─ 模糊描述 → 先 sj-cicd list 帮用户定位任务名
└─ 讨论性问题 → 直接回答，不调用命令
```

## 任务命名规范

Jenkins 任务通常按环境和项目类型命名，常见前缀模式：

| 前缀模式 | 含义 |
|----------|------|
| `DEV-*` | 开发环境项目 |
| `TEST-*` | 测试环境项目 |
| `PROD-*` | 生产环境项目 |
| 中文名（如 `cdn刷新`）| 特殊工具类任务 |

用户提到项目名但未使用完整前缀时，用 `sj-cicd list <关键词>` 模糊匹配。

## 错误处理

- **认证失败 (401/403)**: 引导用户检查 `~/.jenkins-cli` 或到 `/me/configure` 重新生成 Token
- **任务不存在 (404)**: 用 `sj-cicd list` 搜索相似名称
- **队列超时**: 提示执行器可能繁忙，建议查看 Jenkins 面板
- **CLI 未安装**: `pip install sanjiu-jenkins-cli`
