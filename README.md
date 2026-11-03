# Replace Device

**A sensor died? Pair the new one – it takes over the old one's name, entity IDs and history. Your automations and dashboards keep working.**

![Replace Device](docs/hero.png)

[English](#english) · [Dansk](#dansk)

## English

When a device breaks and you buy a new one, Home Assistant sees a stranger: new entity IDs, no history, and every automation, script and dashboard still points at the dead one. Replace Device moves everything over in one go.

<p><img src="docs/panel-home.png" alt="Dead devices with a suggested replacement" width="300"> <img src="docs/panel-match.png" alt="Old and new device side by side" width="520"></p>

### What moves over

| | |
| --- | --- |
| **Entity IDs** | The new entities get the old IDs, so automations, scripts, scenes, dashboards and templates keep working. |
| **History and statistics** | Graphs and long-term statistics continue. Energy totals too – a new meter starting at 0 kWh is handled as a reset. |
| **Your settings** | Names, icons, areas, labels, categories, voice aliases, display precision and unit settings. |
| **The device** | The new device gets the old one's name and area. |
| **Device triggers and actions** | Automations and scripts that point at the old device by ID are updated. |

A note is added to the logbook, and if the new device sends no values after 10 minutes, you get a repair. Changed your mind? **Undo** gives the new device its own names back (for 30 days).

### It notices by itself

Pair a new device of the same make and model while an old one has been dead for an hour, and a repair shows up: **"New Aqara WSDCGQ11LM found – replace Kitchen?"**. Tap **Fix**, check the preview, done.

### Move many devices at once

Moving from **ZHA to Zigbee2MQTT** (or any integration to another)? Pair the devices in the new integration, then tap **Move many devices** in the panel and pick *from* and *to*. Every device found in both is paired by what doesn't change: the **Zigbee address** (IEEE), the **serial number** (Matter) or the **MAC address** (Wi-Fi). Names don't matter. Untick the ones to leave, and move them all with one tap.

Moving to Zigbee2MQTT, it can also give each device its Home Assistant name in Zigbee2MQTT, without Zigbee2MQTT changing the entity IDs.

<p><img src="docs/panel-migrate.png" alt="Move many devices from ZHA to Zigbee2MQTT" width="300"></p>

### Use it for

- A dead sensor replaced with a new one
- Another brand doing the same job (an IKEA bulb instead of a Hue one)
- **Moving from ZHA to Zigbee2MQTT** (or back), one device at a time
- A re-flashed ESPHome device with a new name

### Installation

1. **HACS** → ⋮ → **Custom repositories** → `https://github.com/Clahen86/ha-replace-device`, type **Integration** → **Add**.
2. Search for **Replace Device** → **Download**, and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Replace Device → Submit.**

### How to replace a device

1. Pair the new device as you normally would.
2. Open **Replace device** in the sidebar. Dead devices are listed, with a likely replacement when one is found – tap **Replace with …**. Or tap **Replace a device**, search for the old one, then the new one. The same physical device or the same model is shown first.
3. The old and the new device are shown side by side. Each old entity has its match picked (temperature to temperature, battery to battery). Change one if it's wrong, or pick "— removed".
4. See what moves, what's removed and which automations use the old device, then tap **Replace now**.

The same is available without the panel: **Settings → Devices & services → Replace Device → Replace a device**.

### Good to know

- The old device is removed, so its names are free. If its integration doesn't allow that (a device that is still connected), you're told to remove it there.
- If the old device is still in your Zigbee network, remove it there too, so it doesn't come back.
- Device triggers from another integration (ZHA → Zigbee2MQTT) can have different trigger types. The preview lists those automations so you can check them.
- Only `automations.yaml` and `scripts.yaml` (the files the editors write) are updated. YAML you wrote yourself in other files keeps working through the entity IDs, but device IDs there are not changed.
- Everything is local. Nothing leaves your Home Assistant.

## Dansk

Når en enhed går i stykker, og du køber en ny, ser Home Assistant en fremmed. Den får nye entity-id'er og ingen historik, og alle automatiseringer, scripts og dashboards peger stadig på den døde. Udskift enhed flytter det hele over i ét hug.

### Det flyttes over

- **Entity-id'er:** De nye entiteter får de gamle id'er, så automatiseringer, scripts, scener, dashboards og skabeloner virker videre.
- **Historik og statistik:** Grafer og langtidsstatistik fortsætter. Det gælder også energi. En ny måler, der starter på 0 kWh, bliver regnet som en nulstilling.
- **Dine indstillinger:** Navne, ikoner, områder, etiketter, kategorier, stemme-aliasser, antal decimaler og enheder.
- **Enheden:** Den nye enhed får den gamles navn og område.
- **Enhedstriggere og -handlinger:** Automatiseringer og scripts, der peger på den gamle enhed via id, bliver opdateret.

Der kommer en note i logbogen. Sender den nye enhed ingen værdier efter 10 minutter, får du en reparation. Fortryder du, giver **Fortryd** den nye enhed dens egne navne tilbage (i 30 dage).

### Den opdager det selv

Parrer du en ny enhed af samme mærke og model, mens en gammel har været død i en time, kommer der en reparation: **"Ny Aqara WSDCGQ11LM fundet – skal den erstatte Køkken?"**. Tryk **Ret**, se forhåndsvisningen, og så er det klaret.

### Flyt mange enheder på én gang

Skal du flytte fra **ZHA til Zigbee2MQTT** eller mellem to andre integrationer? Par først enhederne i den nye integration. Tryk så **Flyt mange enheder** i panelet, og vælg *fra* og *til*. Alle enheder, der findes begge steder, bliver parret på det, der ikke ændrer sig: **Zigbee-adressen** (IEEE), **serienummeret** (Matter) eller **MAC-adressen** (Wi-Fi). Navnene er ligegyldige. Fjern fluebenet ved dem, der skal blive, og flyt resten med ét tryk.

Flytter du til Zigbee2MQTT, kan den også give hver enhed dens Home Assistant-navn i Zigbee2MQTT, uden at Zigbee2MQTT ændrer entity-id'erne.

### Installation

1. **HACS** → ⋮ → **Brugerdefinerede repositories** → `https://github.com/Clahen86/ha-replace-device`, type **Integration** → **Tilføj**.
2. Søg efter **Replace Device** → **Download**, og genstart Home Assistant.
3. **Indstillinger → Enheder og tjenester → Tilføj integration → Udskift enhed → Send.**

### Sådan udskifter du en enhed

1. Par den nye enhed, som du plejer.
2. Åbn **Udskift enhed** i sidemenuen. Her ser du de døde enheder, og har den fundet en sandsynlig afløser, står den der. Tryk **Udskift med …**. Du kan også trykke **Udskift en enhed**, søge den gamle frem og derefter den nye. Den samme fysiske enhed eller samme model står øverst.
3. Den gamle og den nye enhed vises side om side. For hver gammel entitet er den matchende valgt, fx temperatur til temperatur og batteri til batteri. Ret den, hvis den er forkert, eller vælg "— fjernes".
4. Se, hvad der flyttes, hvad der fjernes, og hvilke automatiseringer der bruger den gamle enhed. Tryk så **Udskift nu**.

Det samme kan gøres uden panelet: **Indstillinger → Enheder og tjenester → Udskift enhed → Udskift en enhed**.

### Godt at vide

- Den gamle enhed bliver fjernet, så dens navne bliver ledige. Tillader dens integration ikke det, fx fordi enheden stadig er forbundet, får du besked om at fjerne den der.
- Er den gamle enhed stadig i dit Zigbee-netværk, så fjern den også der, så den ikke kommer igen.
- Enhedstriggere fra en anden integration (ZHA → Zigbee2MQTT) kan have andre triggertyper. Forhåndsvisningen viser de automatiseringer, så du kan tjekke dem.
- Kun `automations.yaml` og `scripts.yaml`, som editorerne skriver, bliver opdateret. YAML, du selv har skrevet i andre filer, virker videre via entity-id'erne, men device-id'er dér bliver ikke ændret.
- Alt foregår lokalt. Intet forlader din Home Assistant.

## License

MIT
