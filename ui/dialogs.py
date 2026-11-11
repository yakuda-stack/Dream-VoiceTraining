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

"""Sammelstelle: die Dialoge liegen in eigenen Modulen unter ui/.

Bestehender Code importiert weiter aus ui.dialogs; neue Stellen duerfen
direkt aus dem jeweiligen Modul importieren.
"""

from __future__ import annotations

import urllib.request  # noqa: F401  (Tests patchen dialogs.urllib)

from ui.dialog_common import (  # noqa: F401
    CUSTOM_LABEL,
    GUIDE_ROLES,
    GUIDE_Z,
    MEASURED_Z,
    add_formant_guides,
    ask_export_language,
    export_language,
    metric_value,
)
from ui.settings_dialog import (  # noqa: F401
    SettingsDialog,
)
from ui.session_detail import (  # noqa: F401
    SessionDetailDialog,
)
from ui.debug_dialog import (  # noqa: F401
    DebugDialog,
)
from ui.filter_dialog import (  # noqa: F401
    FilterDialog,
)
from ui.options_page import (  # noqa: F401
    OptionsPage,
    PART_ROLES,
    PART_TIPS,
    PartList,
    PartRow,
    badge_html,
    info_icon,
)
from ui.changelog import (  # noqa: F401
    ChangelogDialog,
    ChangelogLoader,
    HighlightsDialog,
)
from ui.info_page import (  # noqa: F401
    InfoPage,
)
from ui.profile_editor import (  # noqa: F401
    ProfileEditor,
)
from ui.design_editor import (  # noqa: F401
    ColorButton,
    DesignEditor,
    ThemeTile,
)
from ui.help_dialog import (  # noqa: F401
    HelpDialog,
)
from ui.spotlight import (  # noqa: F401
    GOLD,
    GOLD_TEXT,
    Spotlight,
)
from ui.links import (  # noqa: F401
    EMOJI_FONTS,
    PROJECT_LINKS,
    ProjectLink,
    doc_button,
    emoji_available,
    link_button,
    project_links_box,
)
from ui.intro import (  # noqa: F401
    IntroDialog,
    ShotView,
    _shot_spots,
)
from ui.microphone import (  # noqa: F401
    MicrophonePicker,
)
