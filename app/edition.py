"""Structured per-article analysis. Article IDs and source URLs remain RSS-owned."""

import json
from dataclasses import dataclass
from openai import OpenAI
from app.ai import MODEL
from app.config import settings
from app.news import NewsItem


@dataclass(frozen=True)
class Story:
    article: NewsItem
    title_ru: str
    summary: str
    impact: str
    emoji: str


@dataclass(frozen=True)
class Edition:
    stories: list[Story]
    conclusion: str


def build_edition(news: list[NewsItem]) -> Edition:
    if not news:
        return Edition([], "За последние сутки подходящих новостей не найдено.")
    # Prefer articles with publisher-supplied illustrations so each post has its own image.
    illustrated = [(i, item) for i, item in enumerate(news) if item.image_url]
    candidates = illustrated if illustrated else list(enumerate(news))
    candidates = candidates[:15]
    entries = "\n".join(f"{i}: [{item.source}] {item.title}" for i, item in candidates)
    response = OpenAI(api_key=settings.openai_api_key, timeout=90).responses.create(
        model=MODEL,
        input=(
            "Ты редактор новостного Telegram-канала о мировой экономике и криптовалютах. "
            "Верни ТОЛЬКО JSON без Markdown: "
            '{"stories":[{"id":0,"title_ru":"...","summary":"...","impact":"...","emoji":"🌍"}],'
            '"conclusion":"..."} . '
            "Выбери до 5 самых значимых РАЗНЫХ новостей только из списка ниже. "
             "id — строго номер из списка. title_ru: точный, лаконичный перевод заголовка на русский язык без новых фактов. summary: 2-3 предложения по-русски, "
            "только факты, подтверждаемые заголовком; не додумывай подробности. "
            "impact: 1-2 предложения об условном влиянии на BTC/ETH/рынок с неопределённостью. "
            "emoji: 1-2 подходящих эмодзи. conclusion: 3-5 предложений, "
            "общий итог, риски и что отслеживать; без торговых рекомендаций. "
            "Не включай ссылки или HTML в JSON.\n\nНОВОСТИ:\n" + entries
        ),
    )
    raw = response.output_text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    data = json.loads(raw)
    allowed = dict(candidates)
    seen = set()
    stories = []
    for entry in data.get("stories", []):
        index = entry.get("id")
        if type(index) is not int or index not in allowed or index in seen:
            continue
        seen.add(index)
        stories.append(Story(
            article=allowed[index],
            title_ru=str(entry.get('title_ru', '')).strip()[:180] or allowed[index].title,
            summary=str(entry.get("summary", "")).strip()[:1300],
            impact=str(entry.get("impact", "")).strip()[:600],
            emoji=str(entry.get("emoji", "📰")).strip()[:8],
        ))
        if len(stories) == 5:
            break
    if not stories:
        raise ValueError("AI returned no valid stories")
    return Edition(stories, str(data.get("conclusion", "")).strip()[:1800])
