"""AI analysis of news and potential crypto-market impact."""

from html import escape, unescape
from html.parser import HTMLParser

from openai import OpenAI

from app.config import settings
from app.news import NewsItem


MODEL = "gpt-5.6-luna"


def analyze_news(news_items: list[NewsItem]) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    if not news_items:
        return "За последние сутки подходящих новостей не найдено."

    client = OpenAI(api_key=settings.openai_api_key)

    news_text = "\n".join(
        f"{i}. [{item.source}] {item.title}\n{item.url}"
        for i, item in enumerate(news_items, start=1)
    )

    prompt = f"""Ты аналитик мировых новостей и их потенциального влияния на крипторынок.

Проанализируй новости ниже и подготовь Telegram-дайджест на русском языке.

Задачи:
1. Выбери 5 наиболее значимых событий.
2. Для каждого дай краткое описание.
3. Отдельно укажи потенциальное влияние на BTC, ETH и крипторынок в целом.
4. Укажи прямые факторы: ставки и центробанки, инфляция, макроэкономика,
   регулирование, геополитика, ETF и криптоиндустрия.
5. В конце дай блок «Что отслеживать».
6. Не давай торговых рекомендаций и не утверждай направление рынка как факт.
7. Чётко отделяй известные факты от оценки и неопределённости.
8. Сохраняй ссылки на источники.

Формат оформления (строго):
- Верни только HTML, поддерживаемый Telegram: <b>, <i>, <a href="URL">.
- Не используй Markdown, HTML-заголовки, HTML-списки или блоки кода.
- Начни с «🌍 <b>МИРОВЫЕ НОВОСТИ | CRYPTO</b>», следующей строкой «🗓 Дайджест за последние 24 часа».
- Затем «📌 <b>ГЛАВНОЕ</b>» с кратким резюме из 2–3 предложений.
- Затем до пяти событий, каждое с номером 01–05, жирным заголовком, кратким описанием,
  строкой «📊 Влияние: ...» и ссылкой «🔗 <a href="точный URL из новостей">Источник</a>».
- Отделяй события пустой строкой и разделителем «━━━━━━━━━━».
- Затем раздел «₿ <b>КРИПТОРЫНОК</b>» с отдельными строками BTC, ETH и рынка в целом.
- Заверши «🔎 <b>ЧТО ОТСЛЕЖИВАТЬ</b>» с 2–3 пунктами и пометкой
  «⚠️ Аналитическая информация, не инвестиционная рекомендация».
- Не выдумывай факты, цены, даты и URL. Если новостей меньше пяти, покажи имеющиеся.
- Экранируй HTML-символы &, <, > в обычном тексте; используй только корректные HTML-теги.
- Пиши компактно, ориентир 2200–3200 символов для мобильного чтения.

Новости:
{news_text}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    result = response.output_text.strip()
    # Always include verified publisher URLs directly from RSS.
    source_lines = ["", "🔗 <b>ПЕРВОИСТОЧНИКИ</b>"]
    for number, item in enumerate(news_items[:5], 1):
        url = escape(item.url, quote=True)
        title = escape(item.title[:75])
        source_lines.append(
            f'📎 {number:02d} · <a href="{url}">{title}</a>'
        )
    return result + "\\n".join(source_lines)


class _PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(unescape("&" + name + ";"))


def telegram_digest_parts(digest: str) -> list[tuple[str, str | None]]:
    """Keep HTML formatting for short posts; safely fall back to plain text for long posts.

    Telegram's message limit is 4096 characters after parsing. Keeping a margin
    avoids breaking HTML tags and links across messages.
    """
    digest = digest.strip()
    if len(digest) <= 3800:
        return [(digest, "HTML")]
    parser = _PlainTextParser()
    parser.feed(digest)
    plain = unescape("".join(parser.parts))
    return [(plain[i:i + 3800], None) for i in range(0, len(plain), 3800)]
