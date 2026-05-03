# Job Tracker — 校招岗位自动追踪

> A Claude Code skill for automated campus recruitment job discovery, personalized filtering, and IM push notifications.

## What It Does

- Searches 2026 campus recruitment positions across multiple sources
- Filters by location, education level, role type, and company priority
- Writes structured results to a Feishu/Lark Bitable
- Pushes digest summaries to Feishu IM
- Learns from your feedback to improve future recommendations
- Runs on autopilot via Cron (e.g. every Monday & Thursday)

## Quick Start

### 1. Prerequisites

- Claude Code with Feishu MCP tools configured
- A Feishu/Lark app with `bitable:app` and `im:message:send` permissions
- A Bitable table with the required schema (see below)

### 2. Install

```bash
# Copy the skill to your Claude Code skills directory
cp -r job-tracker ~/.claude/skills/job-tracker
```

### 3. Configure

```bash
# Copy the example profile and fill in your details
cp profile.example.md profile.md
# Edit profile.md with your target cities, companies, roles, and table config
```

### 4. Set Up Bitable

Create a Feishu Bitable with these fields:

| Field | Type | Options |
|-------|------|---------|
| 公司名称 | Text | — |
| 岗位名称 | Text | — |
| 工作地点 | SingleSelect | Your target cities |
| 岗位类型 | SingleSelect | Your target role categories |
| 薪资范围 | Text | — |
| 学历要求 | SingleSelect | 本科及以上, 硕士及以上, etc. |
| 核心技能要求 | Text | — |
| 匹配度 | SingleSelect | 高, 中, 低 |
| 投递链接 | URL | — |
| 截止日期 | DateTime | — |
| 信息来源 | Text | — |

### 5. Run

```
搜岗位
```

Or set up Cron for automated runs — see SKILL.md for details.

## Key Design Principles

- **Core + Explore**: ~80% results match your exact preferences; ~20% broaden your horizons (adjacent cities, related roles)
- **Feedback loop**: Rate each batch and the system adapts to your taste
- **Personal config stays local**: `profile.md` is gitignored — your company lists, cities, and API tokens never leak

## File Structure

```
job-tracker/
├── SKILL.md            # Full skill logic and workflow
├── README.md           # This file — setup guide
├── profile.example.md  # Template config (safe to publish)
├── profile.md          # Your personal config (gitignored)
└── .gitignore
```

## License

MIT
