# 三式占卜 Skill（奇门遁甲 / 大六壬）

两个可直接被 AI Agent（Operit / OpenClaw 类平台）加载的**占卜 Skill 包**，每个 Skill 由一份 `SKILL.md`（能力说明与调用约定）、一组 `references/`（断法资料）和一套 `scripts/`（可执行排盘引擎 + 回归测试）组成。

| Skill | 目录 | 引擎 | 测试 |
|---|---|---|---|
| 奇门遁甲 | `qimen-dunjia/` | `scripts/qimen.py`（时家奇门，转盘/飞盘、置闰/拆补/茅山定局） | 21 项 |
| 大六壬 | `da-liu-ren/` | `scripts/liuren.py`（月将加时、四课三传、九宗门、天将神煞） | 14 项 |
| 共享历法库 | `_shared/sanzhi/` | 干支、节气、五行、农历、传统天气模块 | — |

## 快速开始

```bash
pip install lunar_python pytest

# 奇门遁甲排盘（不填时间则用当前时刻）
python3 qimen-dunjia/scripts/qimen.py -q "这笔投资能成吗" -y 2026 -m 4 -d 19 -H 16

# 大六壬起课
python3 da-liu-ren/scripts/liuren.py -q "这桩婚事能成吗" -y 2026 -m 4 -d 19 -H 16

# 追加 --json 获得结构化输出
```

大六壬另附 `jinkoujue.py`（金口诀四位起课）与 `bifa_fu.py`（毕法赋断语自动匹配）。

## 回归测试

```bash
pytest                      # 34 项，约 8 秒
pytest -m slow              # 额外跑 2880 盘面穷举回归（3~5 分钟）
```

`pytest.ini` 已把穷举型测试标记为 `slow` 并默认跳过，避免 CI 超时。

## 文献依据与已知局限

**据源**（各 `scripts/*.py` 与 `SKILL.md` 已逐项注明）：

- 奇门遁甲：《烟波钓叟歌》《御定奇门宝鉴》《奇门遁甲秘笈大全》《奇门法窍》（飞盘系）
- 大六壬：《六壬大全》《毕法赋》《大六壬指南》《六壬粹言》《大六壬金口诀》

**必须如实说明的三点**：

1. **`references/` 下的部分案例库不是典籍原文。** `qimen-dunjia/references/anli-jingdian.md`、`da-liu-ren/references/an-li.md` 等文件中的"案例"是**结构化示例（schema 演示）**，用于向模型展示断语的组织形式，其条文不是从任何一部古籍中抄录的，引用时应视为教学示例而非文献证据。
2. **流派差异未穷尽。** 奇门有置闰/拆补/茅山之争与转盘/飞盘之别（引擎已参数化），六壬有《大全》首传法与诸家异说；`SKILL.md` 中列出"文献版本异说"表，遇到分歧时的处理是**并存标注**而非断言唯一正解。
3. **不构成任何决策建议。** 项目仅供传统术数学习、算法实现与软件工程研究。

## 安装到 Operit / 同类平台

把 `qimen-dunjia/`、`da-liu-ren/`、`_shared/` 三个目录放到平台的 skills 根目录（Operit 默认 `/sdcard/Download/Operit/skills/`）即可。脚本通过相对自身位置定位 `_shared/`，无需改路径。

## 目录结构

```
.
├── _shared/sanzhi/           # 三式共享历法库
├── da-liu-ren/
│   ├── SKILL.md
│   ├── references/           # 课体、三传、天将、神煞、九宗门、毕法赋、金口诀…
│   └── scripts/              # liuren.py / jinkoujue.py / bifa_fu.py / tests/
└── qimen-dunjia/
    ├── SKILL.md
    ├── references/           # 九宫、八门、九星、八神、三奇六仪、格局、应期破局…
    └── scripts/              # qimen.py / qimen_zhiyun.py / tests/
```

## 致谢与许可

- 大六壬部分基于开源项目 [dglijin-oss/liuren-skill](https://github.com/dglijin-oss/liuren-skill)（MIT License, Copyright (c) 2026 天工长老）改编整理，核心算法与判定链已按上列典籍重写。
- 本项目以 **MIT License** 发布，见 `LICENSE`。
