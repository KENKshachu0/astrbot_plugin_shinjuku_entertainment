from __future__ import annotations

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register("astrbot_plugin_shinjuku_entertainment", "li", "新宿 娱乐管理插件", "1.0.01")
class ShinjukuEntertainmentPlugin(Star):
    """新宿娱乐管理：群聊趣味/管理功能，当前提供关键词禁言彩蛋。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    def _enabled(self) -> bool:
        return bool(self.config.get("enabled", True))

    def _ban_seconds(self) -> int:
        try:
            return max(0, int(self.config.get("sleep_ban_seconds") or 0))
        except (TypeError, ValueError):
            return 0

    def _is_exact_sleep_message(self, event: AstrMessageEvent) -> bool:
        try:
            self_id = str(event.get_self_id())
        except Exception:
            self_id = None
        try:
            components = event.get_messages()
        except Exception:
            components = []
        texts: list[str] = []
        at_ids: list[str] = []
        for component in components:
            kind = f"{type(component).__name__} {getattr(component, 'type', '')}".lower()
            if "at" in kind or "mention" in kind:
                cid = None
                for attr in ("qq", "user_id", "target", "id"):
                    value = getattr(component, attr, None)
                    if value is not None:
                        cid = str(value)
                        break
                at_ids.append(cid or "")
                continue
            if "reply" in kind or "quote" in kind:
                continue
            text = getattr(component, "text", None)
            if text is None:
                return False
            texts.append(str(text))
        if "".join(texts).strip() != "精致睡眠":
            return False
        for cid in at_ids:
            if not cid or not self_id or cid != self_id:
                return False
        return True

    @filter.command("b50")
    async def b50_cmd(self, event: AstrMessageEvent):
        """占位指令：无反应"""
        event.stop_event()

    @filter.command("help")
    async def help_cmd(self, event: AstrMessageEvent):
        """占位指令：无反应"""
        event.stop_event()

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.regex(r"精致睡眠")
    async def deep_sleep_ban(self, event: AstrMessageEvent):
        """用户只发送「精致睡眠」（可同时艾特机器人）即被静默禁言 8 小时（时长可在设置中调整）"""
        if not self._enabled():
            return
        ban_seconds = self._ban_seconds()
        if ban_seconds <= 0:
            return
        if not self._is_exact_sleep_message(event):
            return
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        if not group_id or not user_id:
            return
        try:
            if str(user_id) == str(event.get_self_id()):
                return
        except Exception:
            pass
        try:
            set_ban = getattr(event.bot, "set_group_ban", None)
            if set_ban:
                await set_ban(
                    group_id=int(group_id),
                    user_id=int(user_id),
                    duration=ban_seconds,
                )
            else:
                await event.bot.call_action(
                    "set_group_ban",
                    group_id=int(group_id),
                    user_id=int(user_id),
                    duration=ban_seconds,
                )
        except Exception as exc:
            logger.error(f"精致睡眠禁言失败: {exc}")
            return
        event.stop_event()
