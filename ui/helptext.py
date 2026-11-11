# Dream-VoiceTraining — voice analysis for training your speaking voice
# Copyright (C) 2026  Yakuda
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Inhalte des Nachschlagefensters.

Hier steht nur noch der Aufbau: welche Themen es gibt, in welchem Abschnitt
und in welcher Reihenfolge. Die Texte selbst liegen in den Sprachdateien
unter ``locales/`` (``help_sections`` und ``help_topics``); der Rumpf ist
einfaches HTML.
"""

from __future__ import annotations

from dataclasses import dataclass

from core import i18n

SECTIONS = ["basics", "pitch", "resonance", "quality", "workflow", "practice"]


class _SectionTitles:
    """Verhaelt sich wie das fruehere dict: SECTION_TITLES[section][lang]."""

    def __getitem__(self, section: str) -> dict:
        return i18n.HELP_SECTIONS[section]

    def get(self, section: str, default=None):
        return i18n.HELP_SECTIONS.get(section, default)


SECTION_TITLES = _SectionTitles()


@dataclass(frozen=True)
class Topic:
    key: str
    section: str

    def _part(self, part: str) -> dict:
        return i18n.HELP_TOPICS.get(self.key, {}).get(part, {})

    @property
    def title(self) -> dict:
        return self._part("title")

    @property
    def body(self) -> dict:
        return self._part("body")

    @property
    def keywords(self) -> dict:
        return self._part("keywords")

    def localised_title(self) -> str:
        return i18n.pick(self.title, self.key)

    def localised_body(self) -> str:
        return i18n.pick(self.body)

    def matches(self, needle: str) -> bool:
        needle = needle.strip().lower()
        if not needle:
            return True
        haystack = " ".join([
            self.localised_title(),
            self.localised_body(),
            self.keywords.get(i18n.LANG, ""),
            self.keywords.get(i18n.DEFAULT, ""),
        ]).lower()
        return needle in haystack


TOPICS: list[Topic] = [
    Topic("overview", "basics"),
    Topic("spectrogram", "basics"),
    Topic("f0", "pitch"),
    Topic("f0_ends", "pitch"),
    Topic("intonation", "pitch"),
    Topic("formants", "resonance"),
    Topic("f1", "resonance"),
    Topic("f2", "resonance"),
    Topic("f3", "resonance"),
    Topic("weight", "resonance"),
    Topic("hnr", "quality"),
    Topic("jitter_shimmer", "quality"),
    Topic("level", "quality"),
    Topic("types", "workflow"),
    Topic("advanced", "workflow"),
    Topic("profiles", "workflow"),
    Topic("settings", "workflow"),
    Topic("progress", "workflow"),
    Topic("getting_started", "practice"),
    Topic("safety", "practice"),
]

TOPIC_BY_KEY = {topic.key: topic for topic in TOPICS}


def topics_in(section: str) -> list[Topic]:
    return [topic for topic in TOPICS if topic.section == section]


def section_title(section: str) -> str:
    return i18n.pick(SECTION_TITLES.get(section), section)
