"""Constants for Replace Device."""

from __future__ import annotations

DOMAIN = "replace_device"
SUBENTRY_REPLACE = "replace"
CONF_OLD = "old_device"
CONF_NEW = "new_device"
CONF_REMOVE_OLD = "remove_old"
NO_MATCH = "none"

# A device whose entities have all been unavailable this long counts as dead.
DEAD_AFTER = 3600
# Wait for a newly added device to get its entities before looking for a dead twin.
SUGGEST_DELAY = 120
# After a replacement: does the new device send values?
CHECK_AFTER = 600

# Zigbee2MQTT's default MQTT base topic.
Z2M_BASE_TOPIC = "zigbee2mqtt"

# The files the automation and script editors write.
AUTOMATIONS_FILE = "automations.yaml"
SCRIPTS_FILE = "scripts.yaml"
SCENES_FILE = "scenes.yaml"
CONF_AI = "ai_task"

# Texts written from code (logbook), in the user's language.
TEXTS = {
    "en": {
        "logbook": "replaced by {new}",
        "moves": "Moves to the new device (keeps entity ID, name and history):",
        "dropped": "Removed, no match on the new device:",
        "own": "New, keep their own entity ID:",
        "users": "Automations and scripts that use the old device itself (updated – check device triggers if the new "
        "device uses another integration):",
        "nothing": "Nothing to move.",
    },
    "da": {
        "logbook": "udskiftet med {new}",
        "moves": "Flyttes til den nye enhed (beholder entity-id, navn og historik):",
        "dropped": "Fjernes, ingen match på den nye enhed:",
        "own": "Nye, beholder deres eget entity-id:",
        "users": "Automatiseringer og scripts, der bruger selve den gamle enhed (opdateres – tjek enhedstriggere, hvis "
        "den nye enhed bruger en anden integration):",
        "nothing": "Der er intet at flytte.",
    },
}
