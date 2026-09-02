"""Nachschlagewerk: Vollständigkeit, Suche, HTML."""

import re

import helptext
import i18n
import targets


def test_alle_themen_in_beiden_sprachen():
    for topic in helptext.TOPICS:
        for lang in ("en", "de"):
            assert topic.title.get(lang, "").strip(), f"{topic.key} Titel {lang}"
            assert len(topic.body.get(lang, "")) > 200, f"{topic.key} Text {lang}"


def test_jedes_thema_gehoert_zu_einem_abschnitt():
    for topic in helptext.TOPICS:
        assert topic.section in helptext.SECTIONS, topic.key
    for section in helptext.SECTIONS:
        assert helptext.topics_in(section), section
        for lang in ("en", "de"):
            assert helptext.SECTION_TITLES[section][lang].strip(), section


def test_schluessel_sind_eindeutig():
    keys = [t.key for t in helptext.TOPICS]
    assert len(keys) == len(set(keys))


def test_html_ist_ausgeglichen():
    for topic in helptext.TOPICS:
        for lang in ("en", "de"):
            body = topic.body[lang]
            for tag in ("p", "ul", "li", "b", "i", "code"):
                assert body.count(f"<{tag}>") == body.count(f"</{tag}>"), \
                    f"{topic.key}/{lang}: <{tag}>"


def test_jeder_kennwert_wird_irgendwo_erklaert():
    """Wer eine Zahl sieht, soll dazu etwas nachlesen können."""
    for lang in ("en", "de"):
        i18n.set_language(lang)
        text = " ".join(t.localised_body() + t.localised_title()
                        for t in helptext.TOPICS).lower()
        for needle in ("f0", "f1", "f2", "f3", "h1", "h2", "hnr",
                       "jitter", "shimmer"):
            assert needle in text, f"{needle} fehlt in {lang}"
    i18n.set_language("en")


def test_suche_findet_und_verwirft():
    i18n.set_language("en")
    assert any(t.matches("larynx") for t in helptext.TOPICS)
    assert not any(t.matches("zzzz") for t in helptext.TOPICS)
    # Leere Suche zeigt alles.
    assert all(t.matches("") for t in helptext.TOPICS)
    assert all(t.matches("   ") for t in helptext.TOPICS)


def test_suche_arbeitet_in_der_aktiven_sprache():
    i18n.set_language("de")
    assert any(t.matches("Kehlkopf") for t in helptext.TOPICS)
    assert any(t.matches("KEHLKOPF") for t in helptext.TOPICS)
    i18n.set_language("en")


def test_kein_thema_verspricht_eine_diagnose():
    """Der Text darf Jitter und Shimmer nicht als Gesundheitsurteil verkaufen."""
    topic = helptext.TOPIC_BY_KEY["jitter_shimmer"]
    for lang in ("en", "de"):
        i18n.set_language(lang)
        body = topic.localised_body().lower()
        assert "diagnos" in body
        assert "vowel" in body or "vokal" in body
    i18n.set_language("en")


def test_texte_enthalten_keine_platzhalter():
    for topic in helptext.TOPICS:
        for lang in ("en", "de"):
            body = topic.body[lang]
            assert "TODO" not in body and "XXX" not in body, topic.key
            assert not re.search(r"\{\w+\}", body), f"{topic.key}: Platzhalter"
