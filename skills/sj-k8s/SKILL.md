---
name: sj-k8s
description: |
  KubeSphere K8s 集群管理工具，通过 sj-k8s CLI 查看 Pod、日志、Deployment 状态等。
  触发：用户提到"pod"、"容器"、"日志"、"k8s"、"集群"、"部署状态"、"namespace"；
  "看下 xxx 服务的状态"、"xxx 挂了吗"、"xxx 的日志"、"重启了几次"；
  "deployment"、"pod log"、"container"、"节点"；
  或出现 test-internal-control、e-commerce 等 namespace 名称时触发。
  不触发：Jenkins 构建部署（使用 sj-cicd skill）；K8s 概念性讨论不需要查询集群。
---

# KubeSphere K8s 集群管理

通过 `sj-k8s` CLI 操作 KubeSphere 管理的 K8s 集群。所有命令输出结构化 JSON。

## 前置检查

每次操作前确认：

```bash
# 1. CLI 是否可用
which sj-k8s || pip install -e ~/Development/projects/self/yw-k8s-cli

# 2. 认证是否有效（token 会自动缓存，通常无需重复登录）
sj-k8s auth
```

认证失败时，引导用户检查 `~/.k8s-cli` 配置文件：
```
KS_URL=https://cloud.ywwl.com
KS_USER=用户名
KS_PASSWORD=密码
```

## 集群信息

这是一个多集群环境，有 3 个集群：

| 集群名 | 所属 Workspace | 用途 |
|--------|---------------|------|
| `dev-local` | dev-ds | 开发测试环境 |
| `dev` | e-commerce-test2 | 电商测试环境 |
| `dianshang-prod` | e-commerce-prod | 电商生产环境 |

**重要**：大部分命令需要通过 `-c <集群名>` 指定集群。用户提到"测试环境"通常指 `dev-local`，"生产环境"指 `dianshang-prod`。

## 命令速查

| 命令 | 用途 | 示例 |
|------|------|------|
| `sj-k8s clusters` | 列出所有集群 | `sj-k8s clusters` |
| `sj-k8s ws` | 列出工作空间 | `sj-k8s ws` |
| `sj-k8s -c CLUSTER ns` | 列出 namespace | `sj-k8s -c dev-local ns` |
| `sj-k8s -c CLUSTER pods NS` | 列出 pods | `sj-k8s -c dev-local pods test-internal-control` |
| `sj-k8s -c CLUSTER deploys NS` | 列出 deployments | `sj-k8s -c dev-local deploys test-internal-control` |
| `sj-k8s -c CLUSTER status NS DEPLOY` | Deployment 状态 | `sj-k8s -c dev-local status test-internal-control starlight-base` |
| `sj-k8s -c CLUSTER describe NS POD` | Pod 详情 | `sj-k8s -c dev-local describe test-internal-control starlight-base-xxx` |
| `sj-k8s -c CLUSTER logs NS POD` | Pod 日志 | `sj-k8s -c dev-local logs test-internal-control starlight-base-xxx -n 50` |
| `sj-k8s auth` | 验证认证（强制重新登录）| `sj-k8s auth` |

### logs 命令参数

- `-n N` / `--tail N`：显示最后 N 行（默认 100）
- `-f` / `--follow`：实时跟踪日志流
- `--container NAME`：多容器 Pod 时指定容器

## 核心工作流

### 工作流 1: 查看服务状态

用户问"xxx 服务怎么样"、"xxx 正常吗"时：

1. **确定集群和 namespace** — 根据上下文推断，不确定时先 `sj-k8s clusters` 再问用户
2. **查看 Deployment 状态** — `sj-k8s -c CLUSTER status NS DEPLOY`
3. **如果异常，查看 Pod 列表** — `sj-k8s -c CLUSTER pods NS`（关注 phase、ready、restarts）
4. **有问题的 Pod 查详情** — `sj-k8s -c CLUSTER describe NS POD`
5. **向用户汇报**：副本数、就绪状态、重启次数、镜像版本

### 工作流 2: 查看日志

1. **先获取 Pod 名** — `sj-k8s -c CLUSTER pods NS` 找到具体 pod 名称
2. **查看日志** — `sj-k8s -c CLUSTER logs NS POD -n 50`
3. **分析日志** — 关注 ERROR、Exception、OOM 等关键信息
4. 如需持续观察 — 加 `-f` 跟踪实时日志

### 工作流 3: 排查故障

用户反馈"xxx 挂了"、"xxx 报错"时：

1. `sj-k8s -c CLUSTER pods NS` — 检查 phase 是否为 Running、restarts 是否异常
2. `sj-k8s -c CLUSTER describe NS POD` — 查看容器状态（CrashLoopBackOff、OOMKilled 等）
3. `sj-k8s -c CLUSTER logs NS POD -n 200` — 获取足够多的日志分析错误
4. 向用户提供故障原因和建议

### 工作流 4: 总览某个 namespace

```bash
# 查看所有 deployment
sj-k8s -c dev-local deploys test-internal-control

# 查看所有 pod
sj-k8s -c dev-local pods test-internal-control
```

## 决策树

```
用户请求
├─ 提到具体服务/deployment 名
│  ├─ "状态/正常吗/ready" → 工作流 1（查看状态）
│  ├─ "日志/log/报错" → 工作流 2（查看日志）
│  ├─ "挂了/崩了/异常/重启" → 工作流 3（排查故障）
│  └─ "镜像/版本" → sj-k8s status 查看 images 字段
├─ 提到 namespace 但未指定服务
│  ├─ "有哪些服务/pod" → sj-k8s pods 或 deploys
│  └─ "总体情况" → 工作流 4（总览）
├─ 未提到具体信息
│  ├─ "集群/有哪些环境" → sj-k8s clusters
│  ├─ "namespace/项目" → sj-k8s ns
│  └─ 模糊描述 → 先 clusters/ns 帮用户定位
└─ 讨论性问题 → 直接回答，不调用命令
```

## 错误处理

- **认证失败**: Token 会自动缓存和刷新，通常无需干预。若持续失败引导用户检查 `~/.k8s-cli`
- **Multiple clusters**: 提示用户指定 `-c <集群名>`，或根据上下文推断
- **Pod 不存在**: 先 `pods` 命令列出可用 pod，找到正确名称
- **权限不足 (403)**: 当前账号可能没有该 namespace 的访问权限
- **CLI 未安装**: `pip install -e ~/Development/projects/self/yw-k8s-cli`
