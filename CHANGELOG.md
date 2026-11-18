# Changelog – Replace Device

Newest first. Each version lists what changed since the one before.

## Unreleased

- Support: version from Home Assistant's loader, no blocking read in the event loop

## 1.12.0 – 2026-11-16

- Store and update links open right inside Home Assistant
- Error reports: a translated message shown on purpose (a refusal) is not reported as an error
- On/off carried over, switch to light, safer takeover, undo only own changes, wider YAML scan, meter jumps taken out

## 1.11.0 – 2026-11-14

- How it is set up goes with the daily question (no names unless 'Share my setup' is on)

## 1.10.0 – 2026-11-14

- Update card (new version, your error fixed) and the version in the daily question

## 1.9.0 – 2026-11-14

- Rename groups too (light groups and other Group helpers, ZHA groups) - name, entity id and everything that uses it

## 1.8.1 – 2026-11-14

- Files under a new address for every version, so a browser never mixes old and new files

## 1.8.0 – 2026-11-14

- Suggestions of the other apps (fits your home, from the same developer)

## 1.7.3 – 2026-11-14

- Errors from Home Assistant restarting or the network (502, timeout, no connection) are not reported

## 1.7.2 – 2026-11-14

- Help sends again (the websocket field 'id' clashed with the message's own)

## 1.7.1 – 2026-11-14

- Tests: statistics read only after the recorder has committed (was flaky)
- Steadier tests

## 1.7.0 – 2026-11-14

- Test: wait until the statistics are written
- Statistics tab in German, Swedish and Dutch
- Help - get help, answers from the developer, errors sent anonymously

## 1.6.1 – 2026-11-07

- Statistics - confirmation in the panel (works in the app), measurements are filled in gaps, nothing to move -> delete the orphaned statistics

## 1.6.0 – 2026-11-07

- Orphaned statistics - find long-term statistics from deleted entities and give them to a new one (renamed, or merged in front with counters that continue) (issue #1)

## 1.5.2 – 2026-11-07

- Links to affected automations/scripts/scenes/dashboards (new tab), search field to pick an entity yourself, 'Replaced' is now called 'History' with button and link after moving (issue #2)

## 1.5.1 – 2026-11-07

- Panel is fetched again after an update (file time in the URL)
- Dead references: better matches - the card's own name and room, every word with the same number (bulb 3 -> bulb 3), never a battery or signal entity for the device itself
- Broken links: scan only when asked and compare in a thread (Home Assistant stays fast)
- Clearer wording - it's the link that is old, not the device
- A match from another room than the card's is never sure
- Broken links: sure only from facts (renames in the history, Replace Device's own moves, the exact same name and kind) - name guesses are 'maybe'. Leftovers: devices and entities that are surely gone (integration removed, not in Zigbee2MQTT/ZHA, add-on uninstalled, no longer provided), with the reason
- Zha and hassio in after_dependencies (leftovers look them up)
- Leftovers: 'no longer provided' is only 'maybe gone' (a switched-off Chromecast looks the same), never in Select all
- 'Give back the old id' also restores the device's old name and the other entities renamed with it (e.g. when an app renames a plug)

## 1.5.0 – 2026-11-06

- Dead references - find entity IDs automations, scripts, scenes and dashboards still use, with the best replacement
- Move (with undo), remove the forgotten entity or ignore

## 1.4.1 – 2026-11-05

- An entity-ID repair removes itself when the ID is back (e.g. after pairing again), and waits a minute before it appears

## 1.4.0 – 2026-11-05

- Entity IDs that change by themselves – a repair offers to use the new ID everywhere or give the old ID back

## 1.3.2 – 2026-11-05

- New screenshots (Test first, Rename)
- Rename intro text and '1 line' (no release)

## 1.3.1 – 2026-11-05

- Each file folds out with the lines to change
- Also code outside Home Assistant (pyscript, Node-RED …)

## 1.3.0 – 2026-11-05

- Own YAML files are never written – Test first shows every line to change by hand
- Helpers can still be ticked (own options flow)

## 1.2.1 – 2026-11-05

- Backups of changed files are deleted after 30 days, with the undo history

## 1.2.0 – 2026-11-05

- Tick files and helpers in Test first to have them changed (files backed up, helpers via their own options flow)

## 1.1.0 – 2026-11-05

- HACS review – packages, other integrations and hand-written YAML are only listed
- New device history is kept
- Escaped icons

## 1.0.1 – 2026-11-04

- Images without beta badge
- Back arrow in the top bar (no release)

## 1.0.0 – 2026-11-04

- Rename/Clean up: also custom_sentences/
- Replace Device 1.0.0: no longer beta

## 0.18.2 – 2026-11-04

- Replace Device 0.18.2: Clean up entity ids fixes everywhere (YAML templates, helpers, energy) like Rename

## 0.18.1 – 2026-11-04

- Manifest: energy i after_dependencies (hassfest)
- Replace Device 0.18.1: an old device that stays gets the name (old - can be deleted), history always folded

## 0.18.0 – 2026-11-04

- Replace Device 0.18.0: Rename a device (everywhere), history with Needs action / Done

## 0.17.0 – 2026-11-04

- Replace Device 0.17.0: new entities get ids from the device's name, Clean up entity ids under Fix

## 0.16.3 – 2026-11-04

- Replace Device 0.16.3: AI timeout 40 s, unused entities folded in dry run, no blocking file reads

## 0.16.2 – 2026-11-04

- Replace Device 0.16.2: clear dry run with names, used in and buttons in plain language

## 0.16.1 – 2026-11-04

- Replace Device 0.16.1: show that it is preparing when a new device is chosen

## 0.16.0 – 2026-11-04

- Replace Device 0.16.0: button triggers in scripts and packages, YAML dashboards, AI is asked once

## 0.15.0 – 2026-11-04

- Replace Device 0.15.0: Test first (dry run)

## 0.14.0 – 2026-11-03

- Replace Device 0.14.0: German, Swedish and Dutch

## 0.13.4 – 2026-11-03

- CI: try HACS validation with brands check
- Replace Device 0.13.4: ready for HACS (all checks without exceptions)

## 0.13.3 – 2026-11-03

- GitHub Actions: hassfest, HACS validation and tests on every change
- Manifest: mqtt and lovelace as after_dependencies (hassfest)
- Run checks again after repo description
- Replace Device 0.13.3: eget ikon (brand/icon.png)

## 0.13.2 – 2026-11-03

- Replace Device 0.13.2: Hue, Z-Wave JS and Shelly

## 0.13.1 – 2026-11-03

- Replace Device 0.13.1: channels are paired in order

## 0.13.0 – 2026-11-03

- Replace Device 0.13.0: bedre brug af AI

## 0.12.2 – 2026-11-03

- Replace Device 0.12.2: beta badge and issue template

## 0.12.1 – 2026-11-03

- Replace Device 0.12.1: warn when the new entity does not store statistics

## 0.12.0 – 2026-11-03

- Replace Device 0.12.0: remember names from a device without entities
- Advar om knaptryk

## 0.11.0 – 2026-11-03

- Replace Device 0.11.0: match across languages, uncertain pairs are marked

## 0.10.0 – 2026-11-03

- Replace Device 0.10.0: buttons are safely translated to Zigbee2MQTT

## 0.9.1 – 2026-11-03

- Replace Device 0.9.1: ZHA-enheder fjernes rigtigt
- Rester vises

## 0.9.0 – 2026-11-03

- Replace Device 0.9.0: 'No contact' instead of 'Dead devices'

## 0.8.0 – 2026-11-03

- Replace Device 0.8.0: Ret i stedet for Fortryd

## 0.7.0 – 2026-11-03

- Replace Device 0.7.0: gentag efter fortryd

## 0.6.1 – 2026-11-03

- Replace Device 0.6.1: find code outside HA that mentions the old device

## 0.6.0 – 2026-11-03

- Replace Device 0.6.0: blueprints, zha_event and Zigbee2MQTT topics

## 0.5.2 – 2026-11-03

- Replace Device 0.5.2: find Zigbee2MQTT's base topic pr. enhed

## 0.5.1 – 2026-11-03

- Replace Device 0.5.1: fejl fundet ved dyb gennemgang

## 0.5.0 – 2026-11-03

- Replace Device 0.5.0: check before moving, dashboards, other integrations and groups

## 0.4.0 – 2026-11-03

- Replace Device 0.4.0: button triggers, AI help, undo all and packages

## 0.3.2 – 2026-11-03

- Replace Device 0.3.2: explain why To is empty in Move many

## 0.3.1 – 2026-11-03

- Replace Device 0.3.1: kun relevante integrationer i Flyt mange

## 0.3.0 – 2026-11-03

- Replace Device 0.3.0: search, move many devices and names in Zigbee2MQTT

## 0.2.0 – 2026-11-03

- Replace Device 0.2.0: own panel, dead devices and undo

## 0.1.0 – 2026-11-03

- Replace Device 0.1.0: new device takes over a dead device's names, ids and history
