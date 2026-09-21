"""AI analysis of news and potential crypto-market impact."""

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

Новости:
{news_text}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    return response.output_text.strip()
