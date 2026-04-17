# Xuanpu Skills Hub

> Curated AI Skills from Xuanpu repo developers - Make AI Assistants More Powerful

A collection of AI Skills built by Xuanpu repo developers for AI coding assistants that support the Skills mechanism (Claude Code, OpenCode, etc.). Can also be wired in as a custom Skills Hub for Xuanpu.

## Skills

| Skill | Description | Use Cases |
|-------|-------------|-----------|
| [context-offload](./skills/context-offload/) | Context Offloading - Write long outputs to files, save context space | Code generation, documentation, reports |
| [sj-k8s](./skills/sj-k8s/) | Manage KubeSphere K8s clusters via the `sj-k8s` CLI (pods, logs, deployments) | Inspect container state, debug service issues, diagnose deploys |
| [sj-cicd](./skills/sj-cicd/) | Drive Jenkins CI/CD via the `sj-cicd` CLI (build, deploy, logs) | Trigger builds, check status/logs, abort builds |

## Core Concept: Context Offloading

### The Problem

The LLM context window is a **scarce resource**. When AI generates long outputs:

- **Token Waste**: A single code generation can consume 2000-5000 tokens
- **Lost in the Middle**: Research shows LLM attention significantly drops for middle portions of context
- **Multi-turn Degradation**: As conversations grow, early important information gets "pushed out" of effective attention range
- **Cost Increase**: Longer context = higher API costs

### The Solution

**Context Offloading** "offloads" long outputs to the filesystem, keeping only concise summaries in context:

```
Traditional:
┌─────────────────────────────────────┐
│ User question (100 tokens)          │
│ AI long response (3000 tokens) ← Takes up space │
│ User follow-up (50 tokens)          │
│ AI response quality degrades...     │
└─────────────────────────────────────┘

With Context Offloading:
┌─────────────────────────────────────┐
│ User question (100 tokens)          │
│ AI summary (100 tokens) + file ref  │  ← Saves 2900 tokens
│ User follow-up (50 tokens)          │
│ AI high-quality response ✓          │
└─────────────────────────────────────┘
```

### Expected Benefits

| Metric | Improvement | Notes |
|--------|-------------|-------|
| **Token Savings** | 1500-3000/output | Tokens saved per long output offload |
| **Context Utilization** | +30-50% | More space for critical information |
| **Lost-in-Middle Probability** | -40% | Based on context length vs attention decay research |
| **Multi-turn Quality** | +20-30% | Keeps context lean, reduces information loss |
| **API Cost** | -20-40% | Reduces unnecessary token consumption |

## Installation

### Claude Code

```bash
# Clone to skills directory
git clone https://github.com/slicenferqin/xuanpu-skills-hub.git
cp -r xuanpu-skills-hub/skills/context-offload ~/.claude/skills/

# Or clone single skill
mkdir -p ~/.claude/skills && cd ~/.claude/skills
git clone --depth 1 --filter=blob:none --sparse https://github.com/slicenferqin/xuanpu-skills-hub.git temp
cd temp && git sparse-checkout set skills/context-offload
cp -r skills/context-offload ../ && cd .. && rm -rf temp
```

### OpenCode

```bash
# Clone to skills directory
cp -r xuanpu-skills-hub/skills/context-offload ~/.config/opencode/skills/
```

## Contributing

PRs welcome for new Skills!

### Skill Development Guide

1. Each Skill is a standalone directory containing `SKILL.md`
2. `SKILL.md` requires YAML frontmatter (`name` and `description`)
3. Keep Skills concise to minimize context usage
4. Provide clear trigger conditions and usage examples

## References

- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) - Research on context length vs attention decay
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [OpenCode Plugins Documentation](https://opencode.ai/docs/plugins/)

## License

MIT
