# My Skills

> AI 技能集合 - 让 AI 助手更强大

这是一个开源的 AI 技能（Skills）集合，适用于支持 Skills 机制的 AI 编程助手，如 Claude Code、OpenCode 等。

## 技能列表

| 技能 | 描述 | 适用场景 |
|------|------|----------|
| [context-offload](./skills/context-offload/) | 上下文卸载 - 将长输出写入文件，节省上下文空间 | 代码生成、文档编写、报告生成 |

## 核心概念：上下文卸载 (Context Offloading)

### 问题背景

LLM 的上下文窗口是**稀缺资源**。当 AI 生成长输出时：

- **Token 浪费**：一次代码生成可能消耗 2000-5000 tokens
- **中间迷失 (Lost in the Middle)**：研究表明，LLM 对上下文中间部分的注意力显著下降
- **多轮对话退化**：随着对话增长，早期重要信息被"挤出"有效注意力范围
- **成本增加**：更长的上下文 = 更高的 API 费用

### 解决方案

**上下文卸载**将长输出"卸载"到文件系统，上下文只保留精简摘要：

```
传统方式：
┌─────────────────────────────────────┐
│ 用户问题 (100 tokens)               │
│ AI 长回复 (3000 tokens) ← 占用大量空间 │
│ 用户追问 (50 tokens)                │
│ AI 回复质量下降...                   │
└─────────────────────────────────────┘

上下文卸载：
┌─────────────────────────────────────┐
│ 用户问题 (100 tokens)               │
│ AI 摘要 (100 tokens) + 文件引用      │  ← 节省 2900 tokens
│ 用户追问 (50 tokens)                │
│ AI 高质量回复 ✓                      │
└─────────────────────────────────────┘
```

### 预估收益

| 指标 | 改善幅度 | 说明 |
|------|----------|------|
| **Token 节省** | 1500-3000/次 | 每次长输出卸载节省的 tokens |
| **上下文利用率** | +30-50% | 更多空间用于关键信息 |
| **中间迷失概率** | -40% | 基于上下文长度与注意力衰减研究 |
| **多轮对话质量** | +20-30% | 保持上下文精简，减少信息丢失 |
| **API 成本** | -20-40% | 减少不必要的 token 消耗 |

## 安装

### Claude Code

```bash
# 克隆到 skills 目录
git clone https://github.com/slicenferqin/my-skills.git
cp -r my-skills/skills/context-offload ~/.claude/skills/

# 或直接克隆单个 skill
mkdir -p ~/.claude/skills && cd ~/.claude/skills
git clone --depth 1 --filter=blob:none --sparse https://github.com/slicenferqin/my-skills.git temp
cd temp && git sparse-checkout set skills/context-offload
cp -r skills/context-offload ../ && cd .. && rm -rf temp
```

### OpenCode

```bash
# 克隆到 skills 目录
cp -r my-skills/skills/context-offload ~/.config/opencode/skills/
```

## 贡献

欢迎提交 PR 贡献新的 Skills！

### Skill 开发指南

1. 每个 Skill 是一个独立目录，包含 `SKILL.md`
2. `SKILL.md` 需要 YAML frontmatter（`name` 和 `description`）
3. 保持 Skill 精简，避免占用过多上下文
4. 提供清晰的触发条件和使用示例

## 参考资料

- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) - 上下文长度与注意力衰减研究
- [Claude Code Skills 文档](https://docs.anthropic.com/en/docs/claude-code/skills)
- [OpenCode Plugins 文档](https://opencode.ai/docs/plugins/)

## License

MIT
