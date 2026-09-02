# 使用文档

`describe-image` 是 ZCode 的一个 skill:当对话中的模型**没有视觉能力**(如 GLM-5.2、纯文本 LLM)时,它把图片转发给一个有视觉的模型,取回文字描述,再让当前模型基于描述继续回答。

```
你发图 ──▶ ZCode agent(无视觉模型)
              │ 调用 describe-image skill
              ▼
        视觉模型 API(Gemini / GLM-4.5V / Qwen-VL)
              │ 返回文字描述
              ▼
        agent 基于描述回答你(会注明"描述来自视觉模型")
```

---

## 1. 适用场景

- ZCode 里配置的是纯文本模型,你想发截图问 bug、发图表问数据、发照片问内容
- 模型声称"看不到图"或对图片没有反应
- 需要图片 OCR(从截图提取代码/报错/表格文字)
- 多张图对比(两次调用后综合)

**不适用于**:模型本身有视觉能力时——没必要绕这一道,直接看图更快更准。

## 2. 前置条件

| 依赖 | 说明 |
|---|---|
| ZCode | skill 需被 ZCode 发现 |
| Git | 安装/更新用 |
| Python 3 | 脚本运行时;启动器自动探测 `python3`/`python`/`py`,会跳过 Windows 上 Microsoft Store 的 `python3` 假桩 |
| 视觉模型 API key | 见第 4 节,任选一家,免费 |

不需要 `jq`、`curl`(纯 Python 标准库实现)。

## 3. 安装

**方式一:直接克隆到 skills 目录(推荐)**

Git Bash(macOS / Linux / Windows):
```bash
git clone https://github.com/InsomniaTTT/describe-image.git ~/.zcode/skills/describe-image
```

Windows PowerShell:
```powershell
git clone https://github.com/InsomniaTTT/describe-image.git "$HOME\.zcode\skills\describe-image"
```

**方式二:克隆到任意位置后用安装脚本**(会自动复制/更新到位):
```bash
git clone https://github.com/InsomniaTTT/describe-image.git
cd describe-image
bash install.sh
```

**方式三:不想用 Git** —— 在仓库页 Code → Download ZIP,解压后把 `describe-image` 文件夹放进 `~/.zcode/skills/`(Windows 即 `C:\Users\<你>\.zcode\skills\`)。

安装后**重启 ZCode**。

## 4. 配置视觉模型 key(必需,任选一家)

| 环境变量 | 模型 | 效果 | 免费申请 |
|---|---|---|---|
| `GEMINI_API_KEY` | Gemini 2.5 Flash | ⭐⭐⭐⭐⭐ | https://aistudio.google.com/apikey |
| `ZHIPU_API_KEY` | GLM-4.5V | ⭐⭐⭐⭐ | https://open.bigmodel.cn/usercenter/apikeys |
| `SILICONFLOW_API_KEY` | Qwen2.5-VL-72B | ⭐⭐⭐⭐ | https://cloud.siliconflow.cn/account/ak |

- 优先级:**Gemini > Zhipu > SiliconFlow**(设了哪个 key 自动用哪个)
- 强制指定:`DESCRIBE_IMAGE_PROVIDER=gemini|zhipu|siliconflow`
- 国内直连:智谱、硅基流动无需代理;Gemini 的 API 在部分网络环境需要代理

**持久化设置(设完重启 ZCode):**

| 平台 | 操作 |
|---|---|
| Windows(所有终端) | `setx GEMINI_API_KEY "你的key"`(对新开终端生效);或"系统属性 → 环境变量" |
| Windows(仅 Git Bash) | 在 `~/.bashrc` 加 `export GEMINI_API_KEY="你的key"` |
| macOS / Linux | 在 `~/.zshrc` 或 `~/.bashrc` 加 `export GEMINI_API_KEY="你的key"` 后 `source` 一下 |

> 🔒 key 只存在你本机的环境变量里,仓库文件里没有任何 key,skill 运行时现读现用。

## 5. 使用

**方式一:直接发图(最常用)**
对着无视觉模型的对话直接丢图提问,agent 检测到图片会自动触发 skill,回复中会注明描述来自视觉模型。

**方式二:显式调用**
```
/describe-image 帮我看看这张图里的报错是什么
```

**方式三:直接跑脚本(调试/独立使用)**
```bash
bash ~/.zcode/skills/describe-image/scripts/describe_image.sh 图片.png "描述这张图"
```

**让描述更贴合你的问题** —— prompt 决定返回质量,常见场景模板:

| 场景 | 推荐附加 prompt |
|---|---|
| 通用描述 | `详细描述这张图:物体、文字、人物、布局、颜色` |
| 截图/报错 | `这是程序截图。逐字 OCR 所有可见文本,完整保留代码和数字` |
| 图表 | `描述这张图表:类型、坐标轴、数据系列、关键数值和趋势` |
| UI/设计稿 | `描述界面布局、组件层级、配色和交互元素` |
| 多图对比 | 每张各调一次,再让 agent 综合 |

**大图处理**:几 MB 以上的图建议先缩小,减少上传时间和 token:
```bash
magick 大图.png -resize 1024x1024\> 小图.png   # 需 ImageMagick
```

## 6. 更新 / 卸载

```bash
# 更新
cd ~/.zcode/skills/describe-image && git pull

# 卸载(顺便可删掉设置的环境变量)
rm -rf ~/.zcode/skills/describe-image
```

## 7. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `No vision API key found` | 没设环境变量,见第 4 节;设完记得**重启 ZCode** |
| `HTTP 400/401 API key not valid` | key 填错了或已失效,去对应平台重新生成 |
| 网络超时 | Gemini 在部分网络需代理;或换用智谱/硅基流动 key |
| `no Python found` | 装 Python 3 并确保在 PATH;Windows 别只依赖 Store 的 `python3` 别名 |
| skill 没触发 | 确认装在 `~/.zcode/skills/describe-image/` 且重启过 ZCode;可显式 `/describe-image` |
| 描述里漏了细节 | 把问题写具体,让 agent 用更聚焦的 prompt 二次调用 |
| 图片带文字返回乱 | prompt 里明确要求"逐字 OCR,不要翻译不要总结" |

## 8. 项目结构

```
SKILL.md                    skill 触发说明(ZCode 读这个)
README.md                   项目简介 + 快速上手
USAGE.md                    本文档
scripts/describe_image.sh   启动器:找 Python,转发参数
scripts/describe_image.py   核心:读图 → base64 → 调 API → 解析返回
install.sh                  安装/更新脚本
publish.sh                  维护者:一键发布到 GitHub
```

## 9. 维护(仓库所有者)

改完 skill 后:
```bash
bash publish.sh          # 自动提交 + 推送
```
首次在新机器上维护:装 [GitHub CLI](https://cli.github.com/) → `gh auth login` → 克隆本仓库到 skills 目录。