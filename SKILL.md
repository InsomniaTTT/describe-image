---
name: describe-image
description: Get a text description of an image using a vision model when the current model has no vision capability (e.g. GLM-5.2, text-only LLMs). Use whenever the user shares an image, screenshot, photo, or picture and asks to analyze/describe/understand/extract-from it, or when you receive an image you cannot actually see. Routes the image to a vision API (Gemini 2.5 Flash / Zhipu GLM-4.5V / SiliconFlow Qwen2.5-VL) and returns the text description so you can continue answering. Also use proactively if a user seems to expect image understanding but you cannot process the pixels.
---

# Describe Image (vision bridge for text-only models)

You are a text-only model and cannot see image pixels. This skill bridges that gap: send the image to a vision-capable model via a REST API, get back a text description, then answer the user based on that description.

## When to use

- The user attaches an image, screenshot, or photo and asks anything about it.
- The user pastes/drops an image path and asks you to look at it.
- You receive an image in context but cannot actually parse it.
- The user explicitly invokes `/describe-image`.

Do **not** use this for images you can genuinely see and process — only when you lack vision.

## Prerequisites (one-time)

The helper script needs one vision API key in the environment. The user sets one of these env vars (any one):

| Env var | Provider | Free key |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini 2.5 Flash (default, best) | https://aistudio.google.com/apikey |
| `ZHIPU_API_KEY` | Zhipu GLM-4.5V (reuse existing Zhipu key) | https://open.bigmodel.cn/usercenter/apikeys |
| `SILICONFLOW_API_KEY` | SiliconFlow Qwen2.5-VL-72B | https://cloud.siliconflow.cn/account/ak |

Provider is auto-selected by which key is set (Gemini > Zhipu > SiliconFlow). Force a provider with `DESCRIBE_IMAGE_PROVIDER=gemini|zhipu|siliconflow`.

If no key is set, tell the user which env var to export and where to get a free key, then stop.

The helper needs **Python 3** on PATH (the launcher auto-detects `python3`/`python`/`py`; on Windows Git Bash it skips the fake Microsoft-Store `python3` stub). No `jq`/`curl` needed — Python's `urllib` + `json` handle everything.

## How to use

1. **Locate the image file.** If the user attached an image, find its path. If they only gave a description with no file, ask where the image is. If they gave a URL, download it first (`curl -sS -o /tmp/img.bin "<url>"`) then proceed.

2. **Run the helper script** with the image path and a prompt tailored to what the user wants:

```bash
bash ~/.zcode/skills/describe-image/scripts/describe_image.sh "<image_path>" "<prompt>"
```

Write the prompt to match the user's actual question, in the user's language. Good defaults:

- Generic "describe this": `Describe this image in detail: objects, text (OCR it), people, layout, colors, anything notable. Reply in <user's language>.`
- Diagram/code/screenshot: `This is a screenshot. OCR all visible text faithfully, describe the UI/layout, and report any code or numbers verbatim. Reply in <user's language>.`
- Chart: `Describe this chart: type, axes, data series, key values, and trends. Reply in <user's language>.`

3. **Read the returned text** — that is the vision model's description of the image.

4. **Answer the user** based on that description. Be transparent in your reply that you obtained the description via a vision model (one short sentence is enough), then give the substantive answer. Do not pretend you saw the image yourself.

## Tips

- If the script returns an error string, surface the error and suggest the likely fix (wrong key, no network, image too large).
- Large images may need downscaling first: `convert "$IMG" -resize 1024x1024\> /tmp/img_small.png` (ImageMagick) before calling the script.
- For multi-image comparison, call the script once per image, then synthesize.
- Keep the vision prompt specific to what the user asked — a vague "describe" prompt wastes tokens and detail.