"""AstrBot commands backed by the MeetYourMeta weapon-list API."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import AsyncGenerator
from urllib.request import Request, urlopen

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register


@register("astrbot_plugin_cod_meta", "Developer", "COD各代配枪与梯队榜查询", "1.2.0")
class CodMetaPlugin(Star):
    CACHE_TTL_SECONDS = 6 * 60 * 60
    DEFAULT_VERSION = "22"
    VERSION_NAMES = {
        "22": "黑色行动7（BO7）",
        "21": "黑色行动6（BO6）", "20": "现代战争III（MWIII）",
        "19": "现代战争II（MWII）", "bf6": "战地6", "wz2": "战区2（WZ2）",
    }
    ALIASES = {
        "cod22": "22", "bo7": "22", "cod21": "21", "bo6": "21",
        "cod20": "20", "mwiii": "20", "mw3": "20",
        "cod19": "19", "mwii": "19", "mw2": "19", "战地6": "bf6",
        "战地": "bf6", "bf6": "bf6", "wz2": "wz2", "战区2": "wz2",
    }
    TIERS = {f"t{i}" for i in range(5)} | {"t0.5", "t1.5", "t2.5", "t3.5"}
    PARTS = {
        "muzzle": "枪口", "barrel": "枪管", "laser": "镭射", "optic": "瞄具",
        "stock": "枪托", "underbarrel": "下挂", "magazine": "弹匣",
        "rearGrip": "后握把", "comb": "枪梳", "stockPad": "枪托垫",
        "fireMods": "射击改装",
    }
    API_URLS = {
        "22": "https://www.meetyourmeta.com/wzguides/v1/apis/bo7/gunsmith/weapon_list",
        "21": "https://www.meetyourmeta.com/wzguides/v1/apis/bo6_gunsmith/weapon_list",
        "20": "https://www.meetyourmeta.com/wzguides/v1/apis/mwiii_gunsmith/weapon_list",
        "19": "https://www.meetyourmeta.com/wzguides/v1/apis/mwii_gunsmith/list?page=1&size=1000",
        "bf6": "https://www.meetyourmeta.com/wzguides/v1/apis/bf6/gunsmith/weapon_list",
        "wz2": "https://www.meetyourmeta.com/wzguides/v1/apis/wz2_gunsmith/weapon_list",
    }
    UNSUPPORTED = {
        "cod23", "mwiv", "mw4", "dmz", "wz3", "战区3",
        "三角洲", "delta",
    }

    def __init__(self, context: Context):
        super().__init__(context)
        self._cache: dict[str, dict] = {}
        self._cache_lock = asyncio.Lock()
        self._cache_dir = Path(__file__).resolve().parent / "cache"

    @classmethod
    def _version(cls, token: str) -> str | None:
        value = token.lower()
        if value in cls.VERSION_NAMES:
            return value
        return cls.ALIASES.get(value)

    async def _fetch(self, version: str, mode: str = "MULTIPLAY") -> dict:
        cache_key = f"{version}:{mode if version == 'bf6' else ''}"
        safe_key = cache_key.replace(":", "_")
        cache_path = self._cache_dir / f"{safe_key}.json"
        async with self._cache_lock:
            record = self._cache.get(cache_key)
            if record is None:
                try:
                    raw = await asyncio.to_thread(cache_path.read_text, encoding="utf-8")
                    candidate = json.loads(raw)
                    if isinstance(candidate.get("data"), dict):
                        record = candidate
                        self._cache[cache_key] = record
                except (OSError, ValueError, AttributeError):
                    record = None

            if record and time.time() - record.get("fetched_at", 0) < self.CACHE_TTL_SECONDS:
                return record["data"]

            url = self.API_URLS[version]
            if version == "bf6":
                url += f"?mode={mode}"

            def get_json() -> dict:
                request = Request(url, headers={"Accept": "application/json", "Referer": "https://meetyourmeta.com/"})
                with urlopen(request, timeout=20) as response:
                    return json.loads(response.read().decode("utf-8"))

            try:
                result = await asyncio.to_thread(get_json)
                if result.get("code") != "A00001" or not isinstance(result.get("data"), dict):
                    raise ValueError("站点 API 返回了无法识别的数据。")
                payload = result["data"]
                if version == "19" and not isinstance(payload.get("list"), list):
                    raise ValueError("MWII API 响应中缺少 data.list。")
                fresh = {"fetched_at": time.time(), "data": payload}
                self._cache_dir.mkdir(parents=True, exist_ok=True)
                temp_path = cache_path.with_suffix(".tmp")
                await asyncio.to_thread(
                    temp_path.write_text,
                    json.dumps(fresh, ensure_ascii=False),
                    encoding="utf-8",
                )
                await asyncio.to_thread(temp_path.replace, cache_path)
                self._cache[cache_key] = fresh
                return payload
            except Exception:
                if record:
                    logger.warning("API refresh failed; using stale cache for %s", cache_key)
                    return record["data"]
                raise

    @staticmethod
    def _plain_name(value: str) -> str:
        return re.sub(r"<[^>]*>", "", value or "").strip()

    async def _tier_text(self, version: str, tier: str, mode: str = "MULTIPLAY") -> str:
        data = await self._fetch(version, mode)
        if version == "19":
            builds = [build for build in data["list"]
                      if (build.get("rankStr") or "").casefold() == tier.casefold()]
            if not builds:
                raise ValueError(f"【{self.VERSION_NAMES[version]}】没有 {tier.upper()} 梯队数据。")
            return f"【{self.VERSION_NAMES[version]} · {tier.upper()}】\n" + "、".join(
                build.get("name", "") for build in builds if build.get("name"))
        weapons = data.get(tier, [])
        if not weapons:
            raise ValueError(f"【{self.VERSION_NAMES[version]}】没有 {tier.upper()} 梯队数据。")
        names = [weapon.get("name", "") for weapon in weapons if weapon.get("name")]
        return f"【{self.VERSION_NAMES[version]} · {tier.upper()}】\n" + "、".join(names)

    async def _gun_text(self, version: str, name: str, mode: str = "MULTIPLAY") -> str:
        data = await self._fetch(version, mode)
        weapons = [weapon for key, values in data.items()
                   if isinstance(values, list) and key.lower().startswith("t")
                   for weapon in values if isinstance(weapon, dict)]
        weapons += [weapon for weapon in data.get("unranked", []) if isinstance(weapon, dict)]
        if version == "19":
            weapons += [build for build in data.get("list", []) if isinstance(build, dict)]
        weapon = next((item for item in weapons if name.casefold() in
                       (item.get("name", "") + " " + item.get("nameEng", "")).casefold()), None)
        if not weapon:
            raise ValueError(f"在【{self.VERSION_NAMES[version]}】中没有找到枪械：{name}")
        builds = weapon.get("gunsmithList") or []
        if not builds:
            raise ValueError(f"{weapon.get('name')} 暂无已收录的配装。")
        lines = [f"【{self.VERSION_NAMES[version]}】{weapon.get('name')} 配装"]
        for index, build in enumerate(builds, 1):
            title = self._plain_name(build.get("name", "")).strip()
            lines.append(f"\n方案{index}{': ' + title if title else ''}（{build.get('rangeStr', '')}）")
            for key, label in self.PARTS.items():
                part = build.get(key)
                if isinstance(part, dict) and part.get("name"):
                    suffix = "（可选）" if part.get("optional") is True else ""
                    lines.append(f"{label}：{part['name']}{suffix}")
            if build.get("code"):
                lines.append(f"配装码：{build['code']}")
            if build.get("comment"):
                lines.append(f"备注：{build['comment']}")
        return "\n".join(lines)

    async def _handle(self, event: AstrMessageEvent, forced_version: str | None = None) -> AsyncGenerator[MessageChain, None]:
        args = event.message_str.strip().split()
        if args and args[0].lower().lstrip("/") in {"cod", "cod22", "cod21", "cod20", "cod19", "bf6", "wz2", "战地6"}:
            args = args[1:]
        if args and args[0].lower() in self.UNSUPPORTED:
            yield event.plain_result("该版本/模式目前尚未接入 MeetYourMeta API，暂不支持查询。")
            return
        version = forced_version or self.DEFAULT_VERSION
        if forced_version is None and args and (mapped := self._version(args[0])):
            version = mapped
            args = args[1:]
        mode = "MULTIPLAY"
        if version == "bf6" and args and args[0].lower() in {"redsec", "大逃杀", "吃鸡"}:
            mode = "REDSEC"
            args = args[1:]
        mode_label = "大逃杀" if mode == "REDSEC" else "本体"
        tier = args[0].lower() if args else "t0"
        try:
            if tier in self.TIERS:
                text = await self._tier_text(version, tier, mode)
                if version == "bf6":
                    text = text.replace("【战地6 ·", f"【战地6 {mode_label} ·", 1)
            elif tier in {"榜单", "总榜", "梯队", "强度榜"}:
                data = await self._fetch(version, mode)
                tier_keys = sorted((key for key, val in data.items()
                                    if re.fullmatch(r"t\d+(?:\.\d+)?", key) and isinstance(val, list)),
                                   key=lambda key: float(key[1:]))
                text = "【" + self.VERSION_NAMES[version] + " 梯队武器】\n" + "\n".join(
                    f"{key.upper()}：" + "、".join(item.get("name", "") for item in data[key])
                    for key in tier_keys
                )
            else:
                gun = " ".join(args)
                text = await self._gun_text(version, gun, mode)
            yield event.plain_result(f"{text}\n\n数据来源：MeetYourMeta")
        except ValueError as exc:
            yield event.plain_result(str(exc))
        except Exception as exc:
            logger.exception("COD meta API query failed: %s", exc)
            yield event.plain_result(f"查询失败：API 请求异常（{type(exc).__name__}）。")

    @filter.command("cod")
    async def cod(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event):
            yield result

    @filter.command("cod22")
    async def cod22(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "22"):
            yield result

    @filter.command("cod21")
    async def cod21(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "21"):
            yield result

    @filter.command("cod20")
    async def cod20(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "20"):
            yield result

    @filter.command("cod19")
    async def cod19(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "19"):
            yield result

    @filter.command("bf6")
    async def bf6(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "bf6"):
            yield result

    @filter.command("战地6")
    async def battlefield6(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "bf6"):
            yield result

    @filter.command("wz2")
    async def wz2(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        async for result in self._handle(event, "wz2"):
            yield result
