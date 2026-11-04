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
        "old_name": "{name} (old – can be deleted)",
        "logbook": "replaced by {new}",
        "moves": "Moves to the new device (keeps entity ID, name and history):",
        "dropped": "Removed, no match on the new device:",
        "own": "New, keep their own entity ID:",
        "users": "Automations and scripts that use the old device itself (updated – check device triggers if the new "
        "device uses another integration):",
        "nothing": "Nothing to move.",
    },
    "da": {
        "old_name": "{name} (gammel – kan slettes)",
        "logbook": "udskiftet med {new}",
        "moves": "Flyttes til den nye enhed (beholder entity-id, navn og historik):",
        "dropped": "Fjernes, ingen match på den nye enhed:",
        "own": "Nye, beholder deres eget entity-id:",
        "users": "Automatiseringer og scripts, der bruger selve den gamle enhed (opdateres – tjek enhedstriggere, hvis "
        "den nye enhed bruger en anden integration):",
        "nothing": "Der er intet at flytte.",
    },
    "de": {
        "old_name": "{name} (alt – kann gelöscht werden)",
        "logbook": "ersetzt durch {new}",
        "moves": "Wird auf das neue Gerät übertragen (behält Entitäts-ID, Namen und Verlauf):",
        "dropped": "Wird entfernt, kein Gegenstück auf dem neuen Gerät:",
        "own": "Neu, behalten ihre eigene Entitäts-ID:",
        "users": "Automationen und Skripte, die das alte Gerät selbst verwenden (werden angepasst – prüfe "
        "Geräte-Auslöser, wenn das neue Gerät eine andere Integration nutzt):",
        "nothing": "Nichts zu übertragen.",
    },
    "sv": {
        "old_name": "{name} (gammal – kan tas bort)",
        "logbook": "ersatt av {new}",
        "moves": "Flyttas till den nya enheten (behåller entitets-ID, namn och historik):",
        "dropped": "Tas bort, ingen motsvarighet på den nya enheten:",
        "own": "Nya, behåller sitt eget entitets-ID:",
        "users": "Automationer och skript som använder själva den gamla enheten (uppdateras – kontrollera "
        "enhetsutlösare om den nya enheten använder en annan integration):",
        "nothing": "Inget att flytta.",
    },
    "nl": {
        "old_name": "{name} (oud – kan verwijderd worden)",
        "logbook": "vervangen door {new}",
        "moves": "Gaat naar het nieuwe apparaat (behoudt entiteit-ID, naam en geschiedenis):",
        "dropped": "Wordt verwijderd, geen tegenhanger op het nieuwe apparaat:",
        "own": "Nieuw, houden hun eigen entiteit-ID:",
        "users": "Automatiseringen en scripts die het oude apparaat zelf gebruiken (worden bijgewerkt – controleer "
        "apparaattriggers als het nieuwe apparaat een andere integratie gebruikt):",
        "nothing": "Niets om over te zetten.",
    },
}
