#!/usr/bin/env python3
"""describe_image.py — get a text description of an image via a vision model.

Usage:  describe_image.py <image_path> [prompt]

Provider is auto-selected by which API key env var is set (priority):
  1. GEMINI_API_KEY       -> Google Gemini 2.5 Flash   (default, best free vision)
  2. ZHIPU_API_KEY        -> Zhipu GLM-4.5V            (reuse existing Zhipu key)
  3. SILICONFLOW_API_KEY  -> SiliconFlow Qwen2.5-VL-72B
  4. (fallback, no key needed) the vision-capable model configured in ZCode
     itself (~/.zcode/**/config.json), e.g. glm-5.3-flash:cloud
Override with DESCRIBE_IMAGE_PROVIDER=gemini|zhipu|siliconflow|zcode.

Free keys:
  Gemini:      https://aistudio.google.com/apikey
  Zhipu:       https://open.bigmodel.cn/usercenter/apikeys
  SiliconFlow: https://cloud.siliconflow.cn/account/ak
"""

import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error

DEFAULT_PROMPT = (
    "Describe this image in detail. Identify objects, text (OCR), people, "
    "layout, colors, and anything notable. Reply in the same language as the "
    "user's last message if possible."
)


def die(msg, code=2):
    sys.stderr.write(msg.rstrip("\n") + "\n")
    sys.exit(code)


def http_json(url, payload, headers=None, method="POST"):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        die(f"HTTP {e.code} from {url}:\n{body}", 4)
    except urllib.error.URLError as e:
        die(f"Network error: {e}", 5)


def pick_provider():
    forced = os.environ.get("DESCRIBE_IMAGE_PROVIDER", "").strip().lower()
    if forced:
        if forced not in ("gemini", "zhipu", "siliconflow", "zcode"):
            die(f"Unknown DESCRIBE_IMAGE_PROVIDER='{forced}'. "
                "Use gemini|zhipu|siliconflow|zcode.", 2)
        return forced
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("ZHIPU_API_KEY"):
        return "zhipu"
    if os.environ.get("SILICONFLOW_API_KEY"):
        return "siliconflow"
    if find_zcode_vision_provider():
        return "zcode"
    die("No vision API key found, and no enabled vision-capable model "
        "in ZCode config. Set one of:\n"
        "  GEMINI_API_KEY      (free: https://aistudio.google.com/apikey)\n"
        "  ZHIPU_API_KEY       (free: https://open.bigmodel.cn/usercenter/apikeys)\n"
        "  SILICONFLOW_API_KEY (free: https://cloud.siliconflow.cn/account/ak)", 3)


def guess_mime(path):
    m, _ = mimetypes.guess_type(path)
    return m or "image/jpeg"


def read_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def call_gemini(prompt, b64, mime):
    model = "gemini-2.5-flash"
    key = os.environ["GEMINI_API_KEY"]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mimeType": mime, "data": b64}},
            ]
        }]
    }
    r = http_json(url, payload)
    try:
        return r["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return r.get("error", {}).get("message", "Gemini: empty response")


def call_openai_compat(prompt, b64, mime, model, url, auth):
    """Zhipu and SiliconFlow both use OpenAI-style image_url data URIs."""
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ]
        }]
    }
    headers = {"Authorization": auth}
    r = http_json(url, payload, headers=headers)
    try:
        return r["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return r.get("error", {}).get("message", f"{model}: empty response")


def find_zcode_vision_provider():
    """Find an enabled vision-capable model configured in ZCode itself.

    Returns (base_url, api_key, model) or None. Prefers glm-5.3-flash:cloud.
    """
    zcode_home = os.path.expanduser("~/.zcode")
    best = None  # (base_url, api_key, model, score)
    for cfg_path in (os.path.join(zcode_home, "v2", "config.json"),
                     os.path.join(zcode_home, "cli", "config.json")):
        try:
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            continue
        for prov in (cfg.get("provider") or {}).values():
            if prov.get("enabled") is False:
                continue
            opts = prov.get("options") or {}
            key = opts.get("apiKey") or opts.get("api_key")
            base = opts.get("baseURL") or opts.get("base_url")
            if not (key and base):
                continue
            for model_name, model in (prov.get("models") or {}).items():
                if "image" not in ((model.get("modalities") or {}).get("input") or []):
                    continue
                if model_name == "glm-5.3-flash:cloud":
                    score = 100
                elif "flash" in model_name.lower():
                    score = 50
                else:
                    score = 10
                if best is None or score > best[3]:
                    best = (base, key, model_name, score)
    return best


def call_zcode_anthropic(prompt, b64, mime):
    """Call the ZCode-configured vision model via its Anthropic-compatible API."""
    base, key, model, _ = find_zcode_vision_provider()
    url = base.rstrip("/") + "/v1/messages"
    headers = {"x-api-key": key, "Authorization": f"Bearer {key}",
               "anthropic-version": "2023-06-01"}
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
        {"type": "text", "text": prompt},
    ]

    def text_of(r):
        return "\n".join(b["text"] for b in r.get("content") or []
                         if b.get("type") == "text" and b.get("text")).strip()

    try:
        # Disabling thinking avoids it eating the whole max_tokens budget
        out = text_of(http_json(url, {"model": model, "max_tokens": 4096,
                                      "thinking": {"type": "disabled"},
                                      "messages": [{"role": "user", "content": content}]},
                             headers=headers))
        if out:
            return out
    except SystemExit:
        pass  # HTTP 400: endpoint rejected the thinking param; retry without it
    return text_of(http_json(url, {"model": model, "max_tokens": 16384,
                                   "messages": [{"role": "user", "content": content}]},
                             headers=headers))


def main():
    if len(sys.argv) < 2:
        die("Usage: describe_image.py <image_path> [prompt]", 2)
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROMPT
    if not os.path.isfile(image_path):
        die(f"File not found: {image_path}", 2)

    provider = pick_provider()
    b64 = read_b64(image_path)
    mime = guess_mime(image_path)

    if provider == "gemini":
        out = call_gemini(prompt, b64, mime)
    elif provider == "zhipu":
        out = call_openai_compat(
            prompt, b64, mime, "glm-4.5v",
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            f"Bearer {os.environ['ZHIPU_API_KEY']}")
    elif provider == "zcode":
        out = call_zcode_anthropic(prompt, b64, mime)
    else:  # siliconflow
        out = call_openai_compat(
            prompt, b64, mime, "Qwen/Qwen2.5-VL-72B-Instruct",
            "https://api.siliconflow.cn/v1/chat/completions",
            f"Bearer {os.environ['SILICONFLOW_API_KEY']}")

    sys.stdout.write(out.strip() + "\n")


if __name__ == "__main__":
    main()