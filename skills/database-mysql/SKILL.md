---
name: database-mysql
description: Use when user provides MySQL connection credentials or asks about databases. Automatically checks ./database-memory/ for existing documentation first. Supports JDBC URLs, direct parameters, and environment variables.
---

# MySQL 数据库连接与查询

## Overview

通过 PyMySQL 连接 MySQL，执行查询和探索数据库结构。

**Skill 工作流程：**
1. 🔍 **优先查记忆** - 用户提问时，先从 `./database-memory/` 读取已有的 MD 文档
2. 🔌 **连接数据库** - 解析连接信息，建立 MySQL 连接
3. 🗂️ **探索结构** - 列出库、表、字段信息
4. 🔎 **执行查询** - 运行自定义 SQL，格式化输出

**Skill 的职责（抽象、可复用）：**
- 解析连接信息（JDBC URL / 直接参数）
- 列出库、表、字段
- 执行 SQL 查询，格式化输出
- **优先读取本地记忆**（`./database-memory/`）

**不属于 Skill 的职责（用户私有）：**
- 本地 MD 记忆文件（用户自主维护）
- 查询历史日志
- 业务知识积累

## 工作流程

```
用户提问 (如何查某个 Token？)
    ↓
🔍 检查 ./database-memory/ 中的记忆文档
    ├─ 找到 → 直接返回相关 MD 内容
    └─ 未找到 → 连接数据库查询
    ↓
🔌 建立 MySQL 连接
    ↓
🗂️ 执行查询 / 探索结构
    ↓
📝 返回结果 + 询问用户是否保存
    ↓
✅ 用户确认 → 去重检查 → 写入记忆
```

## 连接信息解析

| 输入格式 | 处理方式 |
|---------|---------|
| 只有 host | 检查 `./database-memory/{host}.md` 找凭据 |
| `jdbc:mysql://host:port/db` | 提取 host / port / database |
| `host:port` + user + password | 直接使用 |
| 没有 database | 列出所有库后再指定 |

## 使用场景

### 场景 1：查询已知的库（本地有记忆）

**用户问**: "怎么查某个 Token？"

**Skill 流程**:
1. 查找 `./database-memory/my_database/QUERIES.md` ← 有记忆！
2. 直接返回查询模板和说明
3. 无需连接数据库

```
用户：怎么查 Token？
Claude（Skill）：
  📚 找到本地记忆...
  
  从 ./database-memory/my_database/QUERIES.md：
  
  ### 1. 查询特定 ID 的 Token
  ```sql
  SELECT id, name, token_status, updated_at 
  FROM api_token 
  WHERE id = '?' LIMIT 10
  ```
  
  需要具体 id 才能执行。
```

### 场景 2：查询未知的库或表

**用户问**: "我想查 order_db 库有什么表"

**Skill 流程**:
1. 查找 `./database-memory/order_db/TABLES.md` ← 未找到
2. 连接数据库，扫描 `order_db`
3. 返回表列表
4. 建议用户将结果保存到 `./database-memory/order_db/TABLES.md`

### 场景 3：执行特定查询

**用户问**: "查一下某商户的 appid"

**Skill 流程**:
1. 查找 `./database-memory/` 看有没有类似查询的模板
2. 有 → 使用模板参数化，执行查询
3. 无 → 连接数据库，编写查询，执行

## 本地记忆文件管理

### 目录结构

```
./database-memory/
├── QA_SERVER.md             # QA 环境说明（可读写）
├── PROD_SERVER.md           # 线上环境说明（只读）
├── DB_INDEX.md              # 全库索引
│
├── my_database/             # 某库知识库
│   ├── INFO.md             # 库说明
│   ├── TABLES.md           # 表结构
│   └── QUERIES.md          # 常用查询
│
├── prod-my_database/        # 线上库知识库
│   ├── INFO.md
│   └── TABLES.md
│
└── {db-name}/              # 其他库
    ├── INFO.md
    ├── TABLES.md
    └── QUERIES.md
```

### 推荐的记忆内容

| 文件 | 内容 | 何时创建 |
|------|------|---------|
| `SERVER.md` | 服务器连接信息、权限说明 | 第一次连接 |
| `{db}/INFO.md` | 库用途、业务说明 | 初次探索库 |
| `{db}/TABLES.md` | 表列表、字段详情 | 扫描表结构 |
| `{db}/QUERIES.md` | 常用 SQL 模板、查询历史 | 发现高频查询 |

### 自动检索逻辑

Skill 会按以下顺序查找记忆：

1. 用户明确指定的文件 → 直接读取
2. `./database-memory/{db-name}/QUERIES.md` → 常用查询
3. `./database-memory/{db-name}/TABLES.md` → 表结构
4. `./database-memory/{db-name}/INFO.md` → 库说明
5. `./database-memory/{server-name}.md` → 服务器信息
6. `./database-memory/DB_INDEX.md` → 全库索引

如果都找不到 → 连接数据库实时查询

### 查询结果保存记忆

**触发条件**：查询执行成功后，询问用户是否保存，用户确认即写入。

**去重规则**：写入前必须先读取目标文件，检查是否已有相同内容：

| 文件类型 | 去重判断标准 | 匹配则跳过 |
|---------|------------|-----------|
| `QUERIES.md` | SQL 模板相同（忽略参数值和空格差异） | 不重复追加 |
| `TABLES.md` | 表名相同 | 更新已有表的字段信息，而非追加 |
| `INFO.md` | 整文件已存在 | 仅在内容有变化时更新 |

**写入流程**：

```
查询成功 → 询问 "是否保存到记忆？"
    ↓
用户确认 → 读取目标文件（如 QUERIES.md）
    ↓
检查去重：
    ├─ 已有相同 SQL 模板 → 提示 "该查询已存在于记忆中"，跳过
    ├─ 已有相同表名（TABLES.md）→ 原地更新该表的字段信息
    └─ 无重复 → 追加到文件末尾
    ↓
文件不存在 → 创建目录和文件，写入内容
```

**示例 — QUERIES.md 去重**：

记忆中已有：
```sql
-- 查询 Token 状态
SELECT id, name, token_status FROM api_token WHERE id = '?'
```

用户新查询：
```sql
SELECT id, name, token_status FROM api_token WHERE id = '12345'
```

→ SQL 模板相同（仅参数不同），判定为重复，**不追加**。

## 标准操作

### 1. 列出所有数据库

```bash
python3 ~/.claude/skills/database-mysql/mysql_info.py \
  --host HOST --port PORT --user USER --password PASS
```

输出：MySQL 版本、所有库列表、系统/用户库分类

### 2. 查看某库的表结构

```bash
python3 ~/.claude/skills/database-mysql/mysql_info.py \
  --host HOST --port PORT --user USER --password PASS \
  --database mydb
```

输出：表列表、字段数、行数、引擎、注释  
加 `--no-rows` 跳过行数统计（大表加速用）

### 3. 执行自定义 SQL

```bash
python3 ~/.claude/skills/database-mysql/mysql_info.py \
  --host HOST --port PORT --user USER --password PASS \
  --database mydb \
  --sql "SELECT * FROM table WHERE id = 1 LIMIT 10"
```

### 4. 模糊搜索表名

```bash
python3 ~/.claude/skills/database-mysql/mysql_info.py \
  --host HOST --port PORT --user USER --password PASS \
  --database mydb \
  --sql "SHOW TABLES LIKE '%keyword%'"
```

## 安全原则

- 🔐 密码仅通过参数传入，不写入任何文件
- 📖 本地记忆中可存储服务器信息，但**不存储密码**
- 🚫 默认只读，写操作需用户明确确认
- 📊 大表查询加 `LIMIT`，避免意外全表扫描
- 🔒 线上库（只读）和测试库（读写）分开管理

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `Access denied` | 用户名/密码错误 | 确认凭据 |
| `Can't connect` | host/port 不通 | 检查网络/防火墙 |
| `Unknown database` | 库名错误 | 先不指定 database，列出所有库 |
| `ModuleNotFoundError: pymysql` | 未安装 | `pip3 install PyMySQL` |

## 示例

### 示例 1: 查询测试库的 Token（使用本地记忆）

```
用户: 怎么查 Token？
Claude:
  📚 检查本地记忆...
  找到: ./database-memory/my_database/QUERIES.md
  
  ### 1. 查询特定 ID 的 Token
  ```sql
  SELECT id, name, token_status, updated_at 
  FROM api_token 
  WHERE id = 'your-id'
  ```
  **结果**: 某商户 (有效)
```

### 示例 2: 查询线上库（有访问权限说明）

```
用户: 我想看线上库的投放表
Claude:
  📚 检查本地记忆...
  找到: ./database-memory/PROD_SERVER.md
  
  ⚠️ 这是线上生产库（只读权限）
  
  连接: your-prod-server.example.com:3306
  用户: readonly_user
  库: my_database (N 张表)
  
  [显示权限说明和使用注意]
```

### 示例 3: 新表探索（无本地记忆）

```
用户: order_db 库有多少张表？
Claude:
  📚 检查本地记忆...
  未找到 ./database-memory/order_db/ 记忆
  
  📡 连接数据库查询中...
  [执行查询]
  
  结果: 15 张表
  
  💾 是否将表结构保存到记忆？

用户: 好的
Claude:
  📝 检查 ./database-memory/order_db/TABLES.md... 文件不存在
  ✅ 已创建并写入 15 张表结构
```

### 示例 4: 保存时去重

```
用户: 查一下 user 表的 token 状态
Claude:
  [执行查询，返回结果]
  
  💾 是否保存该查询到记忆？

用户: 保存
Claude:
  📝 检查 ./database-memory/order_db/QUERIES.md...
  ⚠️ 已有相同 SQL 模板: "SELECT ... FROM api_token WHERE ..."
  跳过写入，该查询已存在于记忆中。
```
