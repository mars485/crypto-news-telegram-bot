"""Send a separate illustrated Telegram post for each selected article."""

import logging
from html import escape
from telegram.error import TelegramError

from app.edition import Edition

logger = logging.getLogger(__name__)


async def publish_edition(bot, chat_id: int, edition: Edition) -> None:
    if not edition.stories:
        await bot.send_message(chat_id, edition.conclusion)
        return
    for number, story in enumerate(edition.stories, 1):
        article = story.article
        title = escape(article.title)
        summary = escape(story.summary)
        impact = escape(story.impact)
        source = escape(article.source)
        url = escape(article.url, quote=True)
        caption = (
            f"{story.emoji} <b>{number:02d} · {title}</b>\n\n"
            f"📰 {summary}\n\n"
            f"📊 <b>ВЛИЯНИЕ НА КРИПТОРЫНОК</b>\n{impact}\n\n"
            f'🔗 <a href="{url}">Читать источник · {source}</a>'
        )
        # Telegram photo captions allow at most 1024 chars after HTML parsing.
        if article.image_url:
            try:
                if len(title + summary + impact + source) < 800:
                    await bot.send_photo(
                        chat_id=chat_id, photo=article.image_url,
                        caption=caption, parse_mode="HTML",
                    )
                else:
                    await bot.send_photo(chat_id=chat_id, photo=article.image_url)
                    await bot.send_message(
                        chat_id=chat_id, text=caption,
                        parse_mode="HTML", disable_web_page_preview=True,
                    )
                continue
            except TelegramError:
                logger.warning("Article photo unavailable: %s", article.source, exc_info=True)
        # No publisher photo: show Telegram's article preview when available.
        await bot.send_message(
            chat_id=chat_id, text=caption, parse_mode="HTML",
            disable_web_page_preview=False,
        )

    await bot.send_message(
        chat_id=chat_id,
        text="📌 <b>ИТОГ ДНЯ</b> 🌍📈\n\n"
             + escape(edition.conclusion)
             + "\n\n⚠️ <i>Аналитическая информация, не инвестиционная рекомендация.</i>",
        parse_mode="HTML",
    )
