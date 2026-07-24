#!/usr/bin/env python3
"""Convert the reusable routing part of a Mihomo/Clash YAML to Shadowrocket."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import yaml


RULESET_MAP = {
    "reject": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising/Advertising.list",
    "icloud": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/iCloud/iCloud.list",
    "apple": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Apple/Apple.list",
    "google": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Google/Google.list",
    "proxy": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Global/Global.list",
    "direct": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/China/China.list",
    "private": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list",
    "gfw": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Global/Global.list",
    "tld-not-cn": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Global/Global.list",
    "telegramcidr": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
    "cncidr": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/China/China.list",
    "lancidr": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Lan/Lan.list",
}

GEOSITE_MAP = {
    "private": RULESET_MAP["private"],
    "category-ads-all": RULESET_MAP["reject"],
    "google": RULESET_MAP["google"],
    "telegram": RULESET_MAP["telegramcidr"],
    "twitter": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Twitter/Twitter.list",
    "facebook": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Facebook/Facebook.list",
    "github": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/GitHub/GitHub.list",
    "cn": RULESET_MAP["direct"],
    "geolocation-cn": RULESET_MAP["direct"],
    "geolocation-!cn": RULESET_MAP["proxy"],
}


def repair_mojibake(value: Any) -> Any:
    """Repair the UTF-8-as-Latin-1 text present in the source file."""
    if isinstance(value, str):
        for _ in range(2):
            try:
                fixed = value.encode("latin1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
            if fixed == value:
                break
            value = fixed
        return value
    if isinstance(value, list):
        return [repair_mojibake(item) for item in value]
    if isinstance(value, dict):
        return {
            repair_mojibake(key): repair_mojibake(item)
            for key, item in value.items()
        }
    return value


def build_groups(config: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    groups: list[str] = []
    names: dict[str, str] = {}
    for group in config.get("proxy-groups", []):
        name = str(group["name"])
        names[name] = name
        policies: list[str] = []
        for item in group.get("proxies", []):
            policy = str(item)
            # The source YAML deliberately contains no complete proxy definitions.
            if policy not in {"DIRECT", "REJECT"}:
                policy = "PROXY"
            if policy not in policies:
                policies.append(policy)
        if not policies:
            policies = ["PROXY", "DIRECT"]
        groups.append(f"{name} = select,{','.join(policies)}")
    return groups, names


def convert_rule(
    raw_rule: str,
    providers: dict[str, Any],
) -> str | None:
    parts = [part.strip() for part in raw_rule.split(",")]
    kind = parts[0].upper()

    if kind == "MATCH" and len(parts) >= 2:
        return f"FINAL,{parts[1]}"

    if kind == "GEOSITE" and len(parts) >= 3:
        url = GEOSITE_MAP.get(parts[1].lower())
        return f"RULE-SET,{url},{parts[2]}" if url else None

    if kind == "RULE-SET" and len(parts) >= 3:
        provider_name = parts[1]
        if provider_name == "applications":
            # Desktop PROCESS rules have no useful equivalent on iOS.
            return None
        url = RULESET_MAP.get(provider_name)
        if not url:
            provider = providers.get(provider_name, {})
            url = provider.get("url")
        return f"RULE-SET,{url},{','.join(parts[2:])}" if url else None

    supported = {
        "DOMAIN",
        "DOMAIN-SUFFIX",
        "DOMAIN-KEYWORD",
        "IP-CIDR",
        "IP-CIDR6",
        "GEOIP",
        "DST-PORT",
        "USER-AGENT",
        "URL-REGEX",
        "PROCESS-NAME",
    }
    return ",".join(parts) if kind in supported else None


def render(config: dict[str, Any], source_name: str) -> str:
    groups, _ = build_groups(config)
    providers = config.get("rule-providers", {})
    converted_rules = [
        converted
        for rule in config.get("rules", [])
        if (converted := convert_rule(str(rule), providers)) is not None
    ]
    # Several Clash providers collapse to the same Shadowrocket list.
    rules = list(dict.fromkeys(converted_rules))

    ipv6 = "true" if config.get("ipv6", False) else "false"
    prefer_ipv6 = "true" if config.get("prefer-ipv6", False) else "false"
    return "\n".join(
        [
            f"# Generated from {source_name} on {date.today().isoformat()}",
            "# 在 Shadowrocket 中添加节点或订阅后，PROXY 会代表可用代理节点。",
            "",
            "[General]",
            "update-url = https://raw.githubusercontent.com/zhang-hong-yang/proxy-config/main/shadowrocket/local-vps.conf",
            "bypass-system = true",
            "skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local,*.in-addr.arpa,*.ip6.arpa,captive.apple.com",
            "tun-excluded-routes = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.168.0.0/16",
            "dns-server = https://dns.alidns.com/dns-query,https://doh.pub/dns-query,223.5.5.5,119.29.29.29",
            "fallback-dns-server = https://dns.cloudflare.com/dns-query,https://dns.google/dns-query",
            f"ipv6 = {ipv6}",
            f"prefer-ipv6 = {prefer_ipv6}",
            "dns-direct-system = false",
            "icmp-auto-reply = true",
            "private-ip-answer = true",
            "udp-policy-not-supported-behaviour = REJECT",
            "hijack-dns = 8.8.8.8:53,8.8.4.4:53,1.1.1.1:53,1.0.0.1:53,223.5.5.5:53,119.29.29.29:53",
            "block-quic = all-proxy",
            "",
            "[Proxy]",
            "",
            "[Proxy Group]",
            *groups,
            "",
            "[Rule]",
            *rules,
            "",
            "[Host]",
            "*.in-addr.arpa = server:system",
            "*.ip6.arpa = server:system",
            "*.local = server:system",
            "localhost = 127.0.0.1",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Mihomo/Clash YAML file")
    parser.add_argument("output", type=Path, help="Shadowrocket .conf file")
    args = parser.parse_args()

    config = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    config = repair_mojibake(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(config, args.input.name), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
