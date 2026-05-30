from __future__ import annotations


MESSAGES = {
    "zh-CN": {
        "invalid_json": "无效的 JSON 请求体",
        "unsupported_protocol_mode": "暂不支持的上游协议模式",
    },
    "en": {
        "invalid_json": "Invalid JSON request body",
        "unsupported_protocol_mode": "Unsupported upstream protocol mode",
    },
}


def translate(language: str, key: str) -> str:
    if language in MESSAGES and key in MESSAGES[language]:
        return MESSAGES[language][key]
    if key in MESSAGES["en"]:
        return MESSAGES["en"][key]
    return key

