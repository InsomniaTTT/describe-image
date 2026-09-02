# describe-image — ZCode 无视觉模型的"眼睛" skill

当 ZCode 里跑的是**没有视觉能力的模型**(如 GLM-5.2、纯文本 LLM)时,这个 skill 会把图片发给一个有视觉的模型(Gemini 2.5 Flash / 智谱 GLM-4.5V / 硅基流动 Qwen2.5-VL),拿回文字描述,再让当前模型基于描述继续回答。

```
用户发图 → agent 调用本 skill → 视觉模型 API 返回文字描述 → agent 基于描述回答
```

仓库结构就是 skill 结构,克隆到 skills 目录即完成安装。

## 一键安装(新电脑)

前置:装好 [ZCode](https://zcode.ai) 和 Git,有一个下表任意视觉模型的 API key。

**Git Bash(macOS / Linux / Windows):**
```bash
git clone https://github.com/<你的GitHub用户名>/describe-image.git ~/.zcode/skills/describe-image
```

**Windows PowerShell:**
```powershell
git clone https://github.com/<你的GitHub用户名>/describe-image.git "$HOME\.zcode\skills\describe-image"
```

或者:先把本仓库克隆到任意位置,再运行仓库里的安装脚本,它会自动复制到位:
```bash
bash install.sh
```

安装后**重启 ZCode** 让 skill 被发现。

## 配置视觉模型 API key(必需,任选一个)

| 环境变量 | 模型 | 免费申请地址 |
|---|---|---|
| `GEMINI_API_KEY` | Gemini 2.5 Flash(默认,效果最好) | https://aistudio.google.com/apikey |
| `ZHIPU_API_KEY` | GLM-4.5V(复用现有智谱 key) | https://open.bigmodel.cn/usercenter/apikeys |
| `SILICONFLOW_API_KEY` | Qwen2.5-VL-72B | https://cloud.siliconflow.cn/account/ak |

设了哪个 key 就自动用哪个(优先级 Gemini > Zhipu > SiliconFlow);也可用环境变量 `DESCRIBE_IMAGE_PROVIDER=gemini|zhipu|siliconflow` 强制指定。

**持久化设置:**

- Windows:`setx GEMINI_API_KEY "你的key"`(对新开的终端生效),或"系统属性 → 环境变量"里添加
- macOS / Linux / Git Bash:在 `~/.bashrc`(或 `~/.zshrc`)里加 `export GEMINI_API_KEY="你的key"`

设置后重启 ZCode。

## 使用

- 对着无视觉模型直接发图提问,agent 会自动触发本 skill;
- 或显式调用:`/describe-image`;
- 也可以直接跑脚本测试:`bash scripts/describe_image.sh <图片路径> "描述一下这张图"`

## 更新

skill 目录本身就是 git 仓库,更新只需:
```bash
cd ~/.zcode/skills/describe-image && git pull
```

## 依赖

- Python 3(启动器会自动探测 `python3` / `python` / `py`,并跳过 Windows 上 Microsoft Store 的 `python3` 假桩)
- 无需 `jq` / `curl`(纯 Python 标准库实现)

## 发布 / 同步回 GitHub

本机改完 skill 后,运行仓库里的发布脚本(需已装 GitHub CLI 并 `gh auth login`):
```bash
bash publish.sh
```
首次运行会创建 GitHub 仓库并推送;之后每次运行直接推送最新改动。

## 文件说明

```
SKILL.md                    skill 触发说明和使用流程(ZCode 读这个)
scripts/describe_image.sh   启动器:找 Python,转发参数
scripts/describe_image.py   核心:base64 → JSON → 调视觉 API → 解析返回
install.sh                  其他电脑上的安装/更新脚本
publish.sh                  一键发布到 GitHub(gh CLI)
```