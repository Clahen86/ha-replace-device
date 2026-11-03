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
| **Device triggers and actions** | Automations and scripts that point at the old device by ID are updated. Button triggers that are called something else in the new integration (ZHA `remote_button_short_press` → Zigbee2MQTT `action: single`) are translated. |

A note is added to the logbook, and if the new device sends no values after 10 minutes, you get a repair. Changed your mind? **Undo** gives the new device its own names back (for 30 days).

### It notices by itself

Pair a new device of the same make and model while an old one has been dead for an hour, and a repair shows up: **"New Aqara WSDCGQ11LM found – replace Kitchen?"**. Tap **Fix**, check the preview, done.

### Move many devices at once

Moving from **ZHA to Zigbee2MQTT** (or any integration to another)? Pair the devices in the new integration, then tap **Move many devices** in the panel and pick *from* and *to*. Every device found in both is paired by what doesn't change: the **Zigbee address** (IEEE), the **serial number** (Matter) or the **MAC address** (Wi-Fi). Names don't matter. Untick the ones to leave, and move them all with one tap.

Moving to Zigbee2MQTT, it can also give each device its Home Assistant name in Zigbee2MQTT, without Zigbee2MQTT changing the entity IDs.

<p><img src="docs/panel-migrate.png" alt="Move many devices from ZHA to Zigbee2MQTT" width="300"></p>

### Optional AI help

Connect any AI Task entity (e.g. Google Gemini, free) under **Settings → Devices & services → Replace Device → Configure**. It is only asked when something can't be matched by itself: entities named differently on the old and the new device ("Analog input" ↔ "Local temperature"), and button triggers with no obvious twin. Only names and types are sent. AI suggestions are marked **AI** in the panel, and you can change them. Tip: give it its own free Gemini key in its own project, so it doesn't share the daily quota.

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
- Automations that listen to the integration itself are fixed too: **blueprints** with inputs for one integration (e.g. a "ZHA / Zigbee2MQTT" remote blueprint gets the Zigbee2MQTT name and base topic instead of the ZHA device), **`zha_event`** triggers and **Zigbee2MQTT MQTT topics** (`<base>/<name>/action`) become device triggers of the new device.
- Button triggers that can't be translated are listed when it's done, so you can fix them by hand. Node-RED, AppDaemon, pyscript and NetDaemon code that mentions the old device can't be changed from Home Assistant; if it is found in a folder Home Assistant can see (e.g. `appdaemon/`, `node-red/`, `/share`), you are told which file to check.
- `automations.yaml`, `scripts.yaml`, `scenes.yaml` and everything in `packages/` are updated. Other YAML keeps working through the entity IDs.
- **Undo all** undoes a whole "move many" in one go.
- Before you replace, it shows what could still bite: entities only the old one had that are used somewhere, values the new one doesn't have (e.g. `On` vs `on` in a select), unit changes (Wh → kWh breaks energy statistics), and device actions of the old integration that can't be moved.
- Dashboards made in the UI and other integrations that store the device (e.g. Battery Notes) are updated too.
- **Zigbee groups**: make the group again in the new integration with the same name, and "move many" lets it take over the old group's entity ID and history.
- Dead devices are found by being unavailable for an hour. In Zigbee2MQTT that needs **availability** turned on (Settings → Availability); without it, a dead device keeps its last value.
- If one step fails (a broken dashboard, a file it can't read), the rest still runs and the replacement can still be undone; the log says what was skipped.
- Not moved: Zigbee bindings (a remote bound directly to a bulb) and calibration set in ZHA or Zigbee2MQTT.
- Everything is local. Nothing leaves your Home Assistant.

## Dansk

Når en enhed går i stykker, og du køber en ny, ser Home Assistant en fremmed. Den får nye entity-id'er og ingen historik, og alle automatiseringer, scripts og dashboards peger stadig på den døde. Udskift enhed flytter det hele over i ét hug.

### Det flyttes over

- **Entity-id'er:** De nye entiteter får de gamle id'er, så automatiseringer, scripts, scener, dashboards og skabeloner virker videre.
- **Historik og statistik:** Grafer og langtidsstatistik fortsætter. Det gælder også energi. En ny måler, der starter på 0 kWh, bliver regnet som en nulstilling.
- **Dine indstillinger:** Navne, ikoner, områder, etiketter, kategorier, stemme-aliasser, antal decimaler og enheder.
- **Enheden:** Den nye enhed får den gamles navn og område.
- **Enhedstriggere og -handlinger:** Automatiseringer og scripts, der peger på den gamle enhed via id, bliver opdateret. Knaptriggere, der hedder noget andet i den nye integration (ZHA `remote_button_short_press` → Zigbee2MQTT `action: single`), bliver oversat.

Der kommer en note i logbogen. Sender den nye enhed ingen værdier efter 10 minutter, får du en reparation. Fortryder du, giver **Fortryd** den nye enhed dens egne navne tilbage (i 30 dage).

### Den opdager det selv

Parrer du en ny enhed af samme mærke og model, mens en gammel har været død i en time, kommer der en reparation: **"Ny Aqara WSDCGQ11LM fundet – skal den erstatte Køkken?"**. Tryk **Ret**, se forhåndsvisningen, og så er det klaret.

### Flyt mange enheder på én gang

Skal du flytte fra **ZHA til Zigbee2MQTT** eller mellem to andre integrationer? Par først enhederne i den nye integration. Tryk så **Flyt mange enheder** i panelet, og vælg *fra* og *til*. Alle enheder, der findes begge steder, bliver parret på det, der ikke ændrer sig: **Zigbee-adressen** (IEEE), **serienummeret** (Matter) eller **MAC-adressen** (Wi-Fi). Navnene er ligegyldige. Fjern fluebenet ved dem, der skal blive, og flyt resten med ét tryk.

Flytter du til Zigbee2MQTT, kan den også give hver enhed dens Home Assistant-navn i Zigbee2MQTT, uden at Zigbee2MQTT ændrer entity-id'erne.

### Valgfri AI-hjælp

Tilslut en AI Task-enhed, fx Google Gemini, som er gratis, under **Indstillinger → Enheder og tjenester → Udskift enhed → Konfigurer**. Den bliver kun spurgt, når noget ikke kan matches af sig selv. Det gælder entiteter med forskellige navne på den gamle og den nye enhed ("Analog input" ↔ "Local temperature") og knaptriggere uden en oplagt tvilling. Kun navne og typer sendes. AI-forslag er markeret med **AI** i panelet, og du kan ændre dem. Tip: Giv den sin egen gratis Gemini-nøgle i sit eget projekt, så den ikke deler dagskvoten med andet.

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
- Automatiseringer, der lytter direkte på integrationen, bliver også rettet. Det gælder **blueprints** med felter til én integration (fx får en "ZHA / Zigbee2MQTT"-fjernbetjeningsblueprint Zigbee2MQTT-navnet og base topic i stedet for ZHA-enheden), og **`zha_event`**-triggere og **Zigbee2MQTT-MQTT-emner** (`<base>/<navn>/action`), som bliver til enhedstriggere på den nye enhed.
- Knaptriggere, der ikke kan oversættes, bliver vist bagefter, så du kan rette dem selv. Kode i Node-RED, AppDaemon, pyscript og NetDaemon, der nævner den gamle enhed, kan ikke ændres fra Home Assistant. Findes den i en mappe, Home Assistant kan se (fx `appdaemon/`, `node-red/` eller `/share`), får du at vide, hvilken fil du skal tjekke.
- `automations.yaml`, `scripts.yaml`, `scenes.yaml` og alt i `packages/` bliver opdateret. Anden YAML virker videre via entity-id'erne.
- **Fortryd alle** fortryder en hel "flyt mange" på én gang.
- Før du udskifter, viser den, hvad der stadig kan drille. Det gælder entiteter, som kun den gamle havde, og som bruges et sted, værdier den nye ikke har (fx `On` mod `on` i en select), skift af enhed (Wh → kWh ødelægger energistatistikken) og enhedshandlinger fra den gamle integration, som ikke kan flyttes.
- Dashboards lavet i brugerfladen og andre integrationer, der gemmer enheden (fx Battery Notes), bliver også opdateret.
- **Zigbee-grupper:** Lav gruppen igen i den nye integration med samme navn. Så kan "flyt mange" lade den overtage den gamle gruppes entity-id og historik.
- Døde enheder findes ved, at de har været utilgængelige i en time. I Zigbee2MQTT kræver det, at **availability** er slået til (Settings → Availability). Uden den beholder en død enhed sin sidste værdi.
- Fejler ét trin, fx et ødelagt dashboard eller en fil den ikke kan læse, kører resten alligevel, og udskiftningen kan stadig fortrydes. Loggen viser, hvad der blev sprunget over.
- Det flyttes ikke: Zigbee-bindinger (en fjernbetjening bundet direkte til en pære) og kalibrering sat i ZHA eller Zigbee2MQTT.
- Alt foregår lokalt. Intet forlader din Home Assistant.

## License

MIT
