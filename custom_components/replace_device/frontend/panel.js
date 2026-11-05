// Replace Device – sidebar panel. Plain web component, no build step; follows the Home Assistant theme.

const TEXT = {
  en: {
    historyAll: "Replaced ({n})",
    dryOldMarked: "The old device is called {name}, so you can see it can be deleted",
    title: "Replace device",
    heroTitle: "A device died?",
    heroText: "Pair the new one first. It then takes over the old one's name, entity IDs and history – your automations and dashboards keep working.",
    start: "Replace a device",
    leftoversTitle: "Left behind after a move",
    leftoversHint: "Already moved – but the old integration still knows the old device. Remove it, so it doesn't come back with new names.",
    movedTo: "Moved to {name}",
    removeLeftover: "Remove the old one",
    removeFailed: "Couldn't remove it here – remove it in {integration}.",
    dead: "No contact",
    deadHint: "Not necessarily broken – often an empty battery, a bulb switched off at the wall, or out of range.",
    batteryLast: "Battery last: {n} %",
    batteryLow: "Battery last: {n} % – change the battery first",
    maybeOff: "Switched off at the wall, or out of range?",
    hide: "Hide – it's only switched off",
    unhide: "Show again",
    showHidden: "{n} hidden – show",
    hideHidden: "Hide the hidden ones",
    noDead: "Everything is reporting.",
    deadFor: "No contact for {t}",
    twin: "Possible replacement",
    replaceWith: "Replace with {name}",
    pickReplacement: "Pick replacement",
    history: "Replaced",
    needsAction: "Needs a look",
    historyDone: "Done ({n})",
    todoButtons: "{n} button triggers to check",
    todoIds: "{n} entity IDs can be tidied up",
    markDone: "Mark as done",
    openEdit: "Open",
    undo: "Undo",
    undone: "Undone",
    moved: "{n} entities moved",
    pickTitle: "Which device is replaced?",
    old: "Old device",
    new: "New device",
    choose: "Choose…",
    deadGroup: "No contact",
    allGroup: "All devices",
    newestGroup: "Newest first",
    next: "Next",
    back: "Back",
    tookOver: "takes over",
    deadTag: "no contact",
    matchTitle: "What goes where",
    matchText: "Each old entity has its match picked. Change it if it's wrong.",
    removed: "— removed",
    keepsOwn: "New, keep their own entity ID",
    usesDevice: "Automations and scripts that use the old device itself",
    usesDeviceHint: "They are updated. If the new device uses another integration, check their device triggers.",
    removeOld: "Remove the old device",
    removeOldHint: "Needed for the names to be free. If it's still in your Zigbee network, remove it there too.",
    replace: "Replace now",
    working: "Replacing…",
    doneTitle: "{name} is replaced",
    doneText: "{n} entities moved over with their history. Automations and dashboards keep working.",
    keptOld: "The old device's integration didn't allow removing it here – remove it there, so it doesn't come back.",
    undoHint: "Undo gives the new device its own names back. The old one only returns if its integration finds it again.",
    home: "Done",
    duplicate: "Two old entities point at the same new one.",
    sameDevice: "Pick two different devices.",
    error: "Something went wrong: {e}",
    minutes: "{n} min",
    hours: "{n} h",
    days: "{n} days",
    checksTitle: "Check after the move",
    outside: "Used outside Home Assistant – change it there yourself: {list}",
    yamlDashboards: "YAML dashboards that mention the old device – change them yourself: {list}",
    droppedUsed: "{name} has no match but is used in: {where}",
    valuesDiffer: "{name}: the new one has no {missing} (it has {new}). Automations that use these values must be changed.",
    unitDiffers: "{name}: unit changes from {old} to {new}.",
    unitEnergy: "{name}: unit changes from {old} to {new} – this breaks the energy statistics. Fix it under Developer tools → Statistics afterwards.",
    stateClassDiffers: "{name}: changes from {old} to {new} – long-term statistics may restart.",
    statisticsGone: "{name}: the new one keeps no long-term statistics. Afterwards Home Assistant asks what to do with the old ones (Developer tools → Statistics).",
    deviceActions: "Device actions of the old integration can't be moved: {list}",
    otherIntegrations: "Change by hand in these integrations: {list}",
    packagesByHand: "Change by hand in packages: {list}",
    fixTitle: "You can also let it change these",
    fixHint: "Tick what may be changed. Files are backed up first (.bak-replace-device-…); integrations are changed through their own settings form.",
    fixDone: "Changed after your OK: {list}",
    fixFailed: "Could not change (do it by hand): {list}",
    dashboardsUpdated: "Dashboards updated: {list}",
    warnCount: "{n} things to check",
    groupsTitle: "Zigbee groups",
    groupsText: "Groups made again in the new integration with the same name take over the old group's entity ID and history.",
    noGroups: "No groups with the same name were found. Make the group again in the new integration – with the same name – and it shows up here.",
    unsureTag: "check",
    aiFailed: "The AI couldn't answer ({e}) – what it would have helped with is marked to check.",
    aiQuota: "The AI's daily quota is used up – what it would have helped with is marked to check. It works again tomorrow.",
    rememberedTag: "{n} names remembered",
    eventTypesDiffer: "{name}: the presses are called differently now ({missing} → {new}). Automations that check the press type must be changed.",
    unsureLine: "Not sure: {name} → {new}. Check that it is the same thing.",
    aiTag: "AI",
    aiHint: "Some entities found no match. Connect an AI under Settings → Devices & services → Replace Device → Configure, and it will help.",
    triggersDone: "{n} button triggers were translated to the new integration.",
    triggersOpen: "Check these button triggers – no match was found:",
    recheck: "Check buttons again",
    tidy: "Tidy up entity IDs",
    tidyHint: "Entities only the new device has get IDs after the device's name, like the others. Automations and dashboards are updated too.",
    tidyNone: "All entity IDs already follow the device's name.",
    tidyApply: "Rename {n}",
    tidyDone: "{n} entity IDs renamed.",
    dryOwnRenamed: "New – get IDs after the device's name",
    recheckDone: "{n} button triggers translated. Still to check: {open}",
    recheckNone: "No button triggers left to translate.",
    pressOnce: "Press each button once, so Zigbee2MQTT tells Home Assistant about it.",
    edit: "Change",
    editTitle: "Change names",
    editIntro: "Change which entity of the new device has each name. The device itself is not moved – it stays in {integration}.",
    noneOption: "— none (the name disappears)",
    save: "Save",
    giveBack: "Give the new device its own names back",
    giveBackWarn: "The old device doesn't come back, and automations that use the old names stop working. Want to go back to the old integration? Pair the device there and make a new replacement.",
    cancel: "Cancel",
    giveBackYes: "Yes, give the names back",
    namesBack: "Names given back",
    undoAll: "Undo all",
    redo: "Do again",
    redoAll: "Do all again",
    notMoved: "Could not be moved (see the log): {list}",
    batchRow: "{n} devices moved",
    pickOld: "Which device is replaced?",
    pickNew: "Which device takes over?",
    search: "Search name, area or model…",
    allIntegrations: "All integrations",
    sameHardware: "same device",
    sameModel: "same model",
    newTag: "new",
    noResults: "Nothing found.",
    change: "Change",
    migrateTitle: "Move many devices",
    migrateStart: "Move many devices",
    renameStart: "Rename a device",
    renameTitle: "Rename a device",
    renameText: "The device, its entity IDs and every place that uses them get the new name – automations, scripts, dashboards, helpers, YAML and the energy dashboard. History follows.",
    renamePick: "Pick the device to rename",
    newName: "New name",
    renameDo: "Rename",
    renameWorking: "Renaming…",
    renameEntities: "Entity IDs that change",
    renameNone: "No entity IDs change – only the device's name.",
    renameFixed: "Updated automatically",
    renameYaml: "YAML files",
    renameEsphome: "ESPHome – install the device again afterwards",
    renameEnergy: "Energy dashboard",
    renameOutside: "Outside Home Assistant – change it there yourself",
    renameAlsoZ2m: "Also renamed in Zigbee2MQTT",
    renameNothingUses: "Nothing else uses these entity IDs.",
    renameDone: "{name} has its new name",
    renameDoneText: "{n} entity IDs renamed and updated everywhere they are used.",
    renameByHand: "Not changed (hand-written configuration and other integrations) – change the entity IDs yourself:",
    renamedLine: "Renamed · {n} entity IDs",
    sumIds: "Entity IDs",
    sumPlaces: "Places",
    migrateText: "Moving to another integration, e.g. ZHA → Zigbee2MQTT? Pair the devices there first. They are matched by their Zigbee address, serial number or MAC address – names don't matter.",
    from: "From",
    to: "To",
    findPairs: "Find pairs",
    matches: "{n} found",
    noTargets: "Not found anywhere else",
    noTargetsHint: "None of your {source} devices is in another integration yet. Pair them in the integration you are moving to first – then it shows up here.",
    pairsFound: "{n} devices found in both",
    noPairs: "No device was found in both. Pair them in {target} first.",
    by_ieee: "Zigbee address",
    by_serial: "serial number",
    by_mac: "MAC address",
    entitiesMatched: "{m}/{t} entities",
    missing: "{n} devices in {source} have no partner in {target} yet.",
    renameZ2m: "Same name in Zigbee2MQTT",
    renameZ2mHint: "The device gets its Home Assistant name in Zigbee2MQTT too. Entity IDs are not changed.",
    moveN: "Move {n} devices",
    migrateDone: "{d} devices moved",
    migrateDoneText: "{n} entities moved over with their history. Each device can be undone under Replaced.",
    all: "All",
    none: "None",
    dryRun: "Test first",
    dryWorking: "Testing…",
    planning: "Getting ready…",
    planningHint: "Pairing the entities and checking automations – asking the AI if something is unclear. This can take a few seconds.",
    dryTitle: "Test run – nothing has been changed",
    dryMoreUnused: "{n} more, not used anywhere – show",
    dryAllUnused: "{n} entities, none used anywhere – show",
    sumMoved: "Move over",
    sumUpdated: "Updated",
    sumButtons: "Buttons",
    sumCheck: "To check",
    usedIn: "Used in",
    notUsed: "Not used anywhere",
    dryUpdated: "Updated automatically",
    dryCheck: "Check these yourself",
    dryAllGood: "Nothing for you to check",
    dryNewName: "New device",
    dryOldName: "Gets the name",
    dryIntro: "This is what would happen. Go back and press the button to do it for real.",
    dryEntities: "Takes over the old names and history",
    dryDropped: "Removed – no match on the new device",
    dryOwn: "New – keep their own entity ID",
    dryDevice: "{from} is renamed {to}",
    dryArea: "Area: {area}",
    dryRemove: "The old device is removed from its integration",
    dryKeep: "The old device is kept",
    dryZ2m: "Renamed in Zigbee2MQTT to {name}",
    dryUsers: "Automations, scripts and scenes that are pointed at the new device",
    dryTriggers: "Button triggers that are translated",
    byHand: "change by hand in {file}",
    dryUnresolved: "Button triggers you must check yourself",
    dryDashboards: "Dashboards updated",
    dryIntegrations: "Other integrations updated",
    dryBack: "Back",
  },
  da: {
    historyAll: "Udskiftet ({n})",
    dryOldMarked: "Den gamle enhed kommer til at hedde {name}, så du kan se, den kan slettes",
    title: "Udskift enhed",
    heroTitle: "Er en enhed død?",
    heroText: "Par den nye først. Så overtager den den gamles navn, entity-id'er og historik – dine automatiseringer og dashboards virker videre.",
    start: "Udskift en enhed",
    leftoversTitle: "Rester efter flytning",
    leftoversHint: "Allerede flyttet – men den gamle integration kender stadig den gamle enhed. Fjern den, så den ikke kommer igen med nye navne.",
    movedTo: "Flyttet til {name}",
    removeLeftover: "Fjern den gamle",
    removeFailed: "Kunne ikke fjernes her – fjern den i {integration}.",
    dead: "Uden kontakt",
    deadHint: "Ikke nødvendigvis i stykker – ofte fladt batteri, en pære slukket på kontakten eller for langt væk.",
    batteryLast: "Batteri sidst: {n} %",
    batteryLow: "Batteri sidst: {n} % – skift batteriet først",
    maybeOff: "Slukket på kontakten, eller for langt væk?",
    hide: "Skjul – den er bare slukket",
    unhide: "Vis igen",
    showHidden: "{n} skjulte – vis",
    hideHidden: "Skjul de skjulte",
    noDead: "Alt melder sig.",
    deadFor: "Ingen kontakt i {t}",
    twin: "Mulig afløser",
    replaceWith: "Udskift med {name}",
    pickReplacement: "Vælg afløser",
    history: "Udskiftet",
    needsAction: "Kræver handling",
    historyDone: "Færdige ({n})",
    todoButtons: "{n} knaptriggere skal tjekkes",
    todoIds: "{n} entity-id'er kan ryddes op",
    markDone: "Marker som færdig",
    openEdit: "Åbn",
    undo: "Fortryd",
    undone: "Fortrudt",
    moved: "{n} entiteter flyttet",
    pickTitle: "Hvilken enhed skal udskiftes?",
    old: "Gammel enhed",
    new: "Ny enhed",
    choose: "Vælg…",
    deadGroup: "Uden kontakt",
    allGroup: "Alle enheder",
    newestGroup: "Nyeste først",
    next: "Næste",
    back: "Tilbage",
    tookOver: "overtager",
    deadTag: "uden kontakt",
    matchTitle: "Hvad hører sammen",
    matchText: "For hver gammel entitet er den matchende valgt. Ret den, hvis den er forkert.",
    removed: "— fjernes",
    keepsOwn: "Nye, beholder deres eget entity-id",
    usesDevice: "Automatiseringer og scripts, der bruger selve den gamle enhed",
    usesDeviceHint: "De bliver opdateret. Bruger den nye enhed en anden integration, så tjek deres enhedstriggere.",
    removeOld: "Fjern den gamle enhed",
    removeOldHint: "Nødvendigt, for at navnene bliver ledige. Er den stadig i dit Zigbee-netværk, så fjern den også der.",
    replace: "Udskift nu",
    working: "Udskifter…",
    doneTitle: "{name} er udskiftet",
    doneText: "{n} entiteter er flyttet med deres historik. Automatiseringer og dashboards virker videre.",
    keptOld: "Den gamle enheds integration tillod ikke at fjerne den her – fjern den dér, så den ikke kommer igen.",
    undoHint: "Fortryd giver den nye enhed dens egne navne tilbage. Den gamle kommer kun igen, hvis dens integration finder den.",
    home: "Færdig",
    duplicate: "To gamle entiteter peger på den samme nye.",
    sameDevice: "Vælg to forskellige enheder.",
    error: "Noget gik galt: {e}",
    minutes: "{n} min",
    hours: "{n} t",
    days: "{n} dage",
    checksTitle: "Tjek efter flytningen",
    outside: "Bruges uden for Home Assistant – ret det selv dér: {list}",
    yamlDashboards: "YAML-dashboards, der nævner den gamle enhed – ret dem selv: {list}",
    droppedUsed: "{name} har ingen match, men bruges i: {where}",
    valuesDiffer: "{name}: den nye har ikke {missing} (den har {new}). Automatiseringer, der bruger de værdier, skal rettes.",
    unitDiffers: "{name}: enheden skifter fra {old} til {new}.",
    unitEnergy: "{name}: enheden skifter fra {old} til {new} – det ødelægger energistatistikken. Ret det under Udviklerværktøjer → Statistik bagefter.",
    stateClassDiffers: "{name}: skifter fra {old} til {new} – langtidsstatistikken kan starte forfra.",
    statisticsGone: "{name}: den nye gemmer ingen langtidsstatistik. Bagefter spørger Home Assistant, hvad der skal ske med den gamle (Udviklerværktøjer → Statistik).",
    deviceActions: "Enhedshandlinger fra den gamle integration kan ikke flyttes: {list}",
    otherIntegrations: "Ret selv i disse integrationer: {list}",
    packagesByHand: "Ret selv i packages: {list}",
    fixTitle: "Den kan også rette disse",
    fixHint: "Sæt flueben ved det, der må rettes. Filer bliver kopieret først (.bak-replace-device-…), og integrationer rettes via deres egen indstillingsside.",
    fixDone: "Rettet efter dit ok: {list}",
    fixFailed: "Kunne ikke rettes (ret selv): {list}",
    dashboardsUpdated: "Dashboards, der opdateres: {list}",
    warnCount: "{n} ting at tjekke",
    groupsTitle: "Zigbee-grupper",
    groupsText: "Grupper, der er lavet igen i den nye integration med samme navn, overtager den gamle gruppes entity-id og historik.",
    noGroups: "Der blev ikke fundet grupper med samme navn. Lav gruppen igen i den nye integration – med samme navn – så dukker den op her.",
    unsureTag: "tjek",
    aiFailed: "AI'en kunne ikke svare ({e}) – det, den skulle have hjulpet med, er markeret til at tjekke.",
    aiQuota: "AI'ens kvote for i dag er brugt op – det, den skulle have hjulpet med, er markeret til at tjekke. Den virker igen i morgen.",
    rememberedTag: "{n} navne huskes",
    eventTypesDiffer: "{name}: trykkene hedder noget andet nu ({missing} → {new}). Automatiseringer, der tjekker typen af tryk, skal rettes.",
    unsureLine: "Usikkert: {name} → {new}. Tjek at det er det samme.",
    aiTag: "AI",
    aiHint: "Nogle entiteter fandt ingen match. Tilslut AI under Indstillinger → Enheder og tjenester → Udskift enhed → Konfigurer, så hjælper den.",
    triggersDone: "{n} knaptriggere er oversat til den nye integration.",
    triggersOpen: "Tjek disse knaptriggere – der blev ikke fundet et match:",
    recheck: "Tjek knapper igen",
    tidy: "Ryd op i entity-id'er",
    tidyHint: "Entiteter, som kun den nye enhed har, får id'er efter enhedens navn ligesom de andre. Automatiseringer og dashboards rettes med.",
    tidyNone: "Alle entity-id'er følger allerede enhedens navn.",
    tidyApply: "Omdøb {n}",
    tidyDone: "{n} entity-id'er omdøbt.",
    dryOwnRenamed: "Nye – får id efter enhedens navn",
    recheckDone: "{n} knaptriggere oversat. Skal stadig tjekkes: {open}",
    recheckNone: "Der er ingen knaptriggere tilbage at oversætte.",
    pressOnce: "Tryk på hver knap én gang, så Zigbee2MQTT melder den til Home Assistant.",
    edit: "Ret",
    editTitle: "Ret navne",
    editIntro: "Ret hvilken entitet på den nye enhed der har hvert navn. Selve enheden flyttes ikke – den bliver i {integration}.",
    noneOption: "— ingen (navnet forsvinder)",
    save: "Gem",
    giveBack: "Giv den nye enhed dens egne navne tilbage",
    giveBackWarn: "Den gamle enhed kommer ikke tilbage, og automatiseringer, der bruger de gamle navne, holder op med at virke. Vil du tilbage til den gamle integration? Par enheden dér og lav en ny udskiftning.",
    cancel: "Annullér",
    giveBackYes: "Ja, giv navnene tilbage",
    namesBack: "Navne givet tilbage",
    undoAll: "Fortryd alle",
    redo: "Gentag",
    redoAll: "Gentag alle",
    notMoved: "Kunne ikke flyttes (se loggen): {list}",
    batchRow: "{n} enheder flyttet",
    pickOld: "Hvilken enhed skal udskiftes?",
    pickNew: "Hvilken enhed overtager?",
    search: "Søg på navn, område eller model…",
    allIntegrations: "Alle integrationer",
    sameHardware: "samme enhed",
    sameModel: "samme model",
    newTag: "ny",
    noResults: "Intet fundet.",
    change: "Skift",
    migrateTitle: "Flyt mange enheder",
    migrateStart: "Flyt mange enheder",
    renameStart: "Omdøb en enhed",
    renameTitle: "Omdøb en enhed",
    renameText: "Enheden, dens entity-id'er og alle steder, de bruges, får det nye navn – automatiseringer, scripts, dashboards, hjælpere, YAML og energi-dashboardet. Historikken følger med.",
    renamePick: "Vælg den enhed, der skal omdøbes",
    newName: "Nyt navn",
    renameDo: "Omdøb",
    renameWorking: "Omdøber…",
    renameEntities: "Entity-id'er, der skifter",
    renameNone: "Ingen entity-id'er skifter – kun enhedens navn.",
    renameFixed: "Rettes automatisk",
    renameYaml: "YAML-filer",
    renameEsphome: "ESPHome – installer enheden igen bagefter",
    renameEnergy: "Energi-dashboardet",
    renameOutside: "Uden for Home Assistant – ret det selv dér",
    renameAlsoZ2m: "Omdøbes også i Zigbee2MQTT",
    renameNothingUses: "Intet andet bruger disse entity-id'er.",
    renameDone: "{name} har fået sit nye navn",
    renameDoneText: "{n} entity-id'er omdøbt og rettet alle de steder, de bruges.",
    renameByHand: "Ændres ikke (håndskrevet konfiguration og andre integrationer) – ret selv entity-id'erne:",
    renamedLine: "Omdøbt · {n} entity-id'er",
    sumIds: "Entity-id'er",
    sumPlaces: "Steder",
    migrateText: "Skal du flytte til en anden integration, fx ZHA → Zigbee2MQTT? Par enhederne dér først. De matches på deres Zigbee-adresse, serienummer eller MAC-adresse – navnene er ligegyldige.",
    from: "Fra",
    to: "Til",
    findPairs: "Find par",
    matches: "{n} fundet",
    noTargets: "Ikke fundet andre steder",
    noTargetsHint: "Ingen af dine {source}-enheder findes i en anden integration endnu. Par dem først i den integration, du vil flytte til – så dukker den op her.",
    pairsFound: "{n} enheder fundet begge steder",
    noPairs: "Ingen enheder blev fundet begge steder. Par dem i {target} først.",
    by_ieee: "Zigbee-adresse",
    by_serial: "serienummer",
    by_mac: "MAC-adresse",
    entitiesMatched: "{m}/{t} entiteter",
    missing: "{n} enheder i {source} har ingen partner i {target} endnu.",
    renameZ2m: "Samme navn i Zigbee2MQTT",
    renameZ2mHint: "Enheden får også sit Home Assistant-navn i Zigbee2MQTT. Entity-id'erne ændres ikke.",
    moveN: "Flyt {n} enheder",
    migrateDone: "{d} enheder er flyttet",
    migrateDoneText: "{n} entiteter er flyttet med deres historik. Hver enhed kan fortrydes under Udskiftet.",
    all: "Alle",
    none: "Ingen",
    dryRun: "Test først",
    dryWorking: "Tester…",
    planning: "Gør klar…",
    planningHint: "Parrer entiteterne og tjekker automatiseringer – spørger AI, hvis noget er uklart. Det kan tage nogle sekunder.",
    dryTitle: "Testkørsel – intet er ændret",
    dryMoreUnused: "{n} mere, der ikke bruges nogen steder – vis",
    dryAllUnused: "{n} entiteter, ingen bruges nogen steder – vis",
    sumMoved: "Flyttes over",
    sumUpdated: "Opdateres",
    sumButtons: "Knapper",
    sumCheck: "Skal tjekkes",
    usedIn: "Bruges i",
    notUsed: "Bruges ingen steder",
    dryUpdated: "Opdateres automatisk",
    dryCheck: "Tjek selv disse",
    dryAllGood: "Intet, du skal tjekke",
    dryNewName: "Ny enhed",
    dryOldName: "Får navnet",
    dryIntro: "Sådan ville det gå. Gå tilbage og tryk på knappen for at gøre det for alvor.",
    dryEntities: "Overtager de gamle navne og historik",
    dryDropped: "Fjernes – ingen match på den nye enhed",
    dryOwn: "Nye – beholder deres eget entity-id",
    dryDevice: "{from} omdøbes til {to}",
    dryArea: "Område: {area}",
    dryRemove: "Den gamle enhed fjernes fra sin integration",
    dryKeep: "Den gamle enhed beholdes",
    dryZ2m: "Omdøbes i Zigbee2MQTT til {name}",
    dryUsers: "Automatiseringer, scripts og scener, der peges over på den nye enhed",
    dryTriggers: "Knaptriggere, der oversættes",
    byHand: "ret selv i {file}",
    dryUnresolved: "Knaptriggere, du selv skal tjekke",
    dryDashboards: "Dashboards, der opdateres",
    dryIntegrations: "Andre integrationer, der opdateres",
    dryBack: "Tilbage",
  },
  de: {
    historyAll: "Ersetzt ({n})",
    dryOldMarked: "Das alte Gerät heißt dann {name}, damit du siehst, dass es gelöscht werden kann",
    needsAction: "Braucht einen Blick",
    historyDone: "Erledigt ({n})",
    todoButtons: "{n} Tasten-Auslöser prüfen",
    todoIds: "{n} Entitäts-IDs können aufgeräumt werden",
    markDone: "Als erledigt markieren",
    openEdit: "Öffnen",
    title: "Gerät ersetzen",
    heroTitle: "Ein Gerät ist ausgefallen?",
    heroText: "Kopple zuerst das neue. Es übernimmt dann Namen, Entitäts-IDs und Verlauf des alten – deine Automationen und Dashboards funktionieren weiter.",
    start: "Ein Gerät ersetzen",
    leftoversTitle: "Nach einem Umzug zurückgeblieben",
    leftoversHint: "Schon umgezogen – aber die alte Integration kennt das alte Gerät noch. Entferne es, damit es nicht mit neuen Namen zurückkommt.",
    movedTo: "Umgezogen zu {name}",
    removeLeftover: "Das alte entfernen",
    removeFailed: "Konnte hier nicht entfernt werden – entferne es in {integration}.",
    dead: "Keine Verbindung",
    deadHint: "Nicht unbedingt kaputt – oft eine leere Batterie, eine am Schalter ausgeschaltete Lampe oder außer Reichweite.",
    batteryLast: "Batterie zuletzt: {n} %",
    batteryLow: "Batterie zuletzt: {n} % – zuerst die Batterie wechseln",
    maybeOff: "Am Schalter ausgeschaltet oder außer Reichweite?",
    hide: "Ausblenden – ist nur ausgeschaltet",
    unhide: "Wieder anzeigen",
    showHidden: "{n} ausgeblendet – anzeigen",
    hideHidden: "Ausgeblendete verbergen",
    noDead: "Alle Geräte melden sich.",
    deadFor: "Keine Verbindung seit {t}",
    twin: "Möglicher Ersatz",
    replaceWith: "Durch {name} ersetzen",
    pickReplacement: "Ersatz wählen",
    history: "Ersetzt",
    undo: "Rückgängig",
    undone: "Rückgängig gemacht",
    moved: "{n} Entitäten übernommen",
    pickTitle: "Welches Gerät wird ersetzt?",
    old: "Altes Gerät",
    new: "Neues Gerät",
    choose: "Auswählen…",
    deadGroup: "Keine Verbindung",
    allGroup: "Alle Geräte",
    newestGroup: "Neueste zuerst",
    next: "Weiter",
    back: "Zurück",
    tookOver: "übernimmt",
    deadTag: "keine Verbindung",
    matchTitle: "Was wohin gehört",
    matchText: "Für jede alte Entität ist ein Gegenstück gewählt. Ändere es, wenn es falsch ist.",
    removed: "— entfernt",
    keepsOwn: "Neu, behalten ihre eigene Entitäts-ID",
    usesDevice: "Automationen und Skripte, die das alte Gerät selbst verwenden",
    usesDeviceHint: "Sie werden angepasst. Wenn das neue Gerät eine andere Integration nutzt, prüfe ihre Geräte-Auslöser.",
    removeOld: "Altes Gerät entfernen",
    removeOldHint: "Nötig, damit die Namen frei werden. Ist es noch in deinem Zigbee-Netz, entferne es dort auch.",
    replace: "Jetzt ersetzen",
    working: "Wird ersetzt…",
    doneTitle: "{name} ist ersetzt",
    doneText: "{n} Entitäten mit ihrem Verlauf übernommen. Automationen und Dashboards funktionieren weiter.",
    keptOld: "Die Integration des alten Geräts erlaubt das Entfernen hier nicht – entferne es dort, damit es nicht zurückkommt.",
    undoHint: "Rückgängig gibt dem neuen Gerät seine eigenen Namen zurück. Das alte kommt nur zurück, wenn seine Integration es wiederfindet.",
    home: "Fertig",
    duplicate: "Zwei alte Entitäten zeigen auf dieselbe neue.",
    sameDevice: "Wähle zwei verschiedene Geräte.",
    error: "Etwas ist schiefgelaufen: {e}",
    minutes: "{n} Min.",
    hours: "{n} Std.",
    days: "{n} Tagen",
    checksTitle: "Nach dem Umzug prüfen",
    outside: "Außerhalb von Home Assistant verwendet – dort selbst ändern: {list}",
    yamlDashboards: "YAML-Dashboards, die das alte Gerät nennen – selbst ändern: {list}",
    droppedUsed: "{name} hat kein Gegenstück, wird aber verwendet in: {where}",
    valuesDiffer: "{name}: das neue hat kein {missing} (es hat {new}). Automationen, die diese Werte nutzen, müssen geändert werden.",
    unitDiffers: "{name}: Einheit ändert sich von {old} zu {new}.",
    unitEnergy: "{name}: Einheit ändert sich von {old} zu {new} – das bricht die Energiestatistik. Behebe es danach unter Entwicklerwerkzeuge → Statistiken.",
    stateClassDiffers: "{name}: ändert sich von {old} zu {new} – die Langzeitstatistik kann neu beginnen.",
    statisticsGone: "{name}: das neue speichert keine Langzeitstatistik. Danach fragt Home Assistant, was mit der alten geschehen soll (Entwicklerwerkzeuge → Statistiken).",
    deviceActions: "Geräte-Aktionen der alten Integration können nicht übernommen werden: {list}",
    otherIntegrations: "Selbst ändern in diesen Integrationen: {list}",
    packagesByHand: "Selbst ändern in Packages: {list}",
    fixTitle: "Das kann es auch ändern",
    fixHint: "Hake an, was geändert werden darf. Dateien werden vorher gesichert (.bak-replace-device-…), Integrationen über ihr eigenes Einstellungsformular geändert.",
    fixDone: "Nach deinem OK geändert: {list}",
    fixFailed: "Konnte nicht geändert werden (selbst ändern): {list}",
    dashboardsUpdated: "Dashboards angepasst: {list}",
    warnCount: "{n} Dinge zu prüfen",
    groupsTitle: "Zigbee-Gruppen",
    groupsText: "Gruppen, die in der neuen Integration mit demselben Namen neu angelegt werden, übernehmen Entitäts-ID und Verlauf der alten Gruppe.",
    noGroups: "Keine Gruppen mit demselben Namen gefunden. Lege die Gruppe in der neuen Integration neu an – mit demselben Namen – dann erscheint sie hier.",
    unsureTag: "prüfen",
    aiFailed: "Die KI konnte nicht antworten ({e}) – wobei sie geholfen hätte, ist zum Prüfen markiert.",
    aiQuota: "Das Tageskontingent der KI ist aufgebraucht – wobei sie geholfen hätte, ist zum Prüfen markiert. Morgen geht es wieder.",
    rememberedTag: "{n} Namen gemerkt",
    eventTypesDiffer: "{name}: die Tastendrücke heißen jetzt anders ({missing} → {new}). Automationen, die die Art des Drückens prüfen, müssen geändert werden.",
    unsureLine: "Nicht sicher: {name} → {new}. Prüfe, ob es dasselbe ist.",
    aiTag: "KI",
    aiHint: "Für einige Entitäten wurde kein Gegenstück gefunden. Verbinde eine KI unter Einstellungen → Geräte & Dienste → Replace Device → Konfigurieren, dann hilft sie.",
    triggersDone: "{n} Tasten-Auslöser wurden in die neue Integration übersetzt.",
    triggersOpen: "Prüfe diese Tasten-Auslöser – kein Gegenstück gefunden:",
    recheck: "Tasten erneut prüfen",
    tidy: "Entitäts-IDs aufräumen",
    tidyHint: "Entitäten, die nur das neue Gerät hat, bekommen IDs nach dem Gerätenamen wie die anderen. Automationen und Dashboards werden mit angepasst.",
    tidyNone: "Alle Entitäts-IDs folgen bereits dem Gerätenamen.",
    tidyApply: "{n} umbenennen",
    tidyDone: "{n} Entitäts-IDs umbenannt.",
    dryOwnRenamed: "Neu – bekommen IDs nach dem Gerätenamen",
    recheckDone: "{n} Tasten-Auslöser übersetzt. Noch zu prüfen: {open}",
    recheckNone: "Keine Tasten-Auslöser mehr zu übersetzen.",
    pressOnce: "Drücke jede Taste einmal, damit Zigbee2MQTT sie Home Assistant meldet.",
    edit: "Ändern",
    editTitle: "Namen ändern",
    editIntro: "Ändere, welche Entität des neuen Geräts welchen Namen hat. Das Gerät selbst wird nicht verschoben – es bleibt in {integration}.",
    noneOption: "— keine (der Name verschwindet)",
    save: "Speichern",
    giveBack: "Dem neuen Gerät seine eigenen Namen zurückgeben",
    giveBackWarn: "Das alte Gerät kommt nicht zurück, und Automationen, die die alten Namen nutzen, funktionieren nicht mehr. Zurück zur alten Integration? Kopple das Gerät dort und mache einen neuen Ersatz.",
    cancel: "Abbrechen",
    giveBackYes: "Ja, Namen zurückgeben",
    namesBack: "Namen zurückgegeben",
    undoAll: "Alle rückgängig",
    redo: "Erneut ausführen",
    redoAll: "Alle erneut ausführen",
    notMoved: "Konnten nicht übernommen werden (siehe Protokoll): {list}",
    batchRow: "{n} Geräte umgezogen",
    pickOld: "Welches Gerät wird ersetzt?",
    pickNew: "Welches Gerät übernimmt?",
    search: "Name, Bereich oder Modell suchen…",
    allIntegrations: "Alle Integrationen",
    sameHardware: "dasselbe Gerät",
    sameModel: "dasselbe Modell",
    newTag: "neu",
    noResults: "Nichts gefunden.",
    change: "Ändern",
    migrateTitle: "Viele Geräte umziehen",
    migrateStart: "Viele Geräte umziehen",
    renameStart: "Ein Gerät umbenennen",
    renameTitle: "Ein Gerät umbenennen",
    renameText: "Das Gerät, seine Entitäts-IDs und alle Stellen, die sie nutzen, bekommen den neuen Namen – Automationen, Skripte, Dashboards, Helfer, YAML und das Energie-Dashboard. Der Verlauf bleibt erhalten.",
    renamePick: "Wähle das Gerät zum Umbenennen",
    newName: "Neuer Name",
    renameDo: "Umbenennen",
    renameWorking: "Wird umbenannt…",
    renameEntities: "Entitäts-IDs, die sich ändern",
    renameNone: "Keine Entitäts-IDs ändern sich – nur der Gerätename.",
    renameFixed: "Wird automatisch angepasst",
    renameYaml: "YAML-Dateien",
    renameEsphome: "ESPHome – danach das Gerät neu installieren",
    renameEnergy: "Energie-Dashboard",
    renameOutside: "Außerhalb von Home Assistant – dort selbst ändern",
    renameAlsoZ2m: "Auch in Zigbee2MQTT umbenannt",
    renameNothingUses: "Nichts anderes nutzt diese Entitäts-IDs.",
    renameDone: "{name} hat den neuen Namen",
    renameDoneText: "{n} Entitäts-IDs umbenannt und überall angepasst.",
    renameByHand: "Nicht geändert (handgeschriebene Konfiguration und andere Integrationen) – Entitäts-IDs selbst ändern:",
    renamedLine: "Umbenannt · {n} Entitäts-IDs",
    sumIds: "Entitäts-IDs",
    sumPlaces: "Stellen",
    migrateText: "Umzug in eine andere Integration, z. B. ZHA → Zigbee2MQTT? Kopple die Geräte zuerst dort. Sie werden über ihre Zigbee-Adresse, Seriennummer oder MAC-Adresse zugeordnet – Namen spielen keine Rolle.",
    from: "Von",
    to: "Nach",
    findPairs: "Paare finden",
    matches: "{n} gefunden",
    noTargets: "Nirgendwo sonst gefunden",
    noTargetsHint: "Keines deiner {source}-Geräte ist schon in einer anderen Integration. Kopple sie zuerst in der Integration, in die du umziehst – dann erscheint sie hier.",
    pairsFound: "{n} Geräte in beiden gefunden",
    noPairs: "Kein Gerät in beiden gefunden. Kopple sie zuerst in {target}.",
    by_ieee: "Zigbee-Adresse",
    by_serial: "Seriennummer",
    by_mac: "MAC-Adresse",
    entitiesMatched: "{m}/{t} Entitäten",
    missing: "{n} Geräte in {source} haben noch kein Gegenstück in {target}.",
    renameZ2m: "Gleicher Name in Zigbee2MQTT",
    renameZ2mHint: "Das Gerät bekommt seinen Home-Assistant-Namen auch in Zigbee2MQTT. Entitäts-IDs werden nicht geändert.",
    moveN: "{n} Geräte umziehen",
    migrateDone: "{d} Geräte umgezogen",
    migrateDoneText: "{n} Entitäten mit ihrem Verlauf übernommen. Jedes Gerät kann unter Ersetzt geändert werden.",
    all: "Alle",
    none: "Keine",
    dryRun: "Erst testen",
    dryWorking: "Wird getestet…",
    planning: "Wird vorbereitet…",
    planningHint: "Entitäten werden zugeordnet und Automationen geprüft – bei Unklarheiten wird die KI gefragt. Das kann ein paar Sekunden dauern.",
    dryTitle: "Testlauf – nichts wurde geändert",
    dryMoreUnused: "{n} weitere, nirgends verwendet – anzeigen",
    dryAllUnused: "{n} Entitäten, keine wird verwendet – anzeigen",
    sumMoved: "Übernommen",
    sumUpdated: "Aktualisiert",
    sumButtons: "Tasten",
    sumCheck: "Zu prüfen",
    usedIn: "Verwendet in",
    notUsed: "Nirgends verwendet",
    dryUpdated: "Wird automatisch aktualisiert",
    dryCheck: "Bitte selbst prüfen",
    dryAllGood: "Nichts zu prüfen",
    dryNewName: "Neues Gerät",
    dryOldName: "Bekommt den Namen",
    dryIntro: "So würde es ablaufen. Geh zurück und drücke den Knopf, um es wirklich zu tun.",
    dryEntities: "Übernimmt die alten Namen und den Verlauf",
    dryDropped: "Wird entfernt – kein Gegenstück auf dem neuen Gerät",
    dryOwn: "Neu – behalten ihre eigene Entitäts-ID",
    dryDevice: "{from} wird in {to} umbenannt",
    dryArea: "Bereich: {area}",
    dryRemove: "Das alte Gerät wird aus seiner Integration entfernt",
    dryKeep: "Das alte Gerät bleibt erhalten",
    dryZ2m: "In Zigbee2MQTT umbenannt in {name}",
    dryUsers: "Automationen, Skripte und Szenen, die auf das neue Gerät umgestellt werden",
    dryTriggers: "Tasten-Auslöser, die übersetzt werden",
    byHand: "selbst ändern in {file}",
    dryUnresolved: "Tasten-Auslöser, die du selbst prüfen musst",
    dryDashboards: "Dashboards, die angepasst werden",
    dryIntegrations: "Andere Integrationen, die angepasst werden",
    dryBack: "Zurück",
  },
  sv: {
    historyAll: "Utbytta ({n})",
    dryOldMarked: "Den gamla enheten får namnet {name}, så du ser att den kan tas bort",
    needsAction: "Behöver en titt",
    historyDone: "Klara ({n})",
    todoButtons: "{n} knapputlösare att kontrollera",
    todoIds: "{n} entitets-ID kan städas",
    markDone: "Markera som klar",
    openEdit: "Öppna",
    title: "Byt enhet",
    heroTitle: "Har en enhet dött?",
    heroText: "Para den nya först. Den tar sedan över den gamlas namn, entitets-ID:n och historik – dina automationer och instrumentpaneler fortsätter att fungera.",
    start: "Byt en enhet",
    leftoversTitle: "Kvar efter en flytt",
    leftoversHint: "Redan flyttad – men den gamla integrationen känner fortfarande till den gamla enheten. Ta bort den, så att den inte kommer tillbaka med nya namn.",
    movedTo: "Flyttad till {name}",
    removeLeftover: "Ta bort den gamla",
    removeFailed: "Kunde inte tas bort här – ta bort den i {integration}.",
    dead: "Ingen kontakt",
    deadHint: "Inte nödvändigtvis trasig – ofta ett tomt batteri, en lampa avstängd med strömbrytaren eller utom räckvidd.",
    batteryLast: "Batteri senast: {n} %",
    batteryLow: "Batteri senast: {n} % – byt batteriet först",
    maybeOff: "Avstängd med strömbrytaren, eller utom räckvidd?",
    hide: "Dölj – den är bara avstängd",
    unhide: "Visa igen",
    showHidden: "{n} dolda – visa",
    hideHidden: "Dölj de dolda",
    noDead: "Allt rapporterar.",
    deadFor: "Ingen kontakt på {t}",
    twin: "Möjlig ersättare",
    replaceWith: "Byt mot {name}",
    pickReplacement: "Välj ersättare",
    history: "Bytta",
    undo: "Ångra",
    undone: "Ångrad",
    moved: "{n} entiteter flyttade",
    pickTitle: "Vilken enhet byts ut?",
    old: "Gammal enhet",
    new: "Ny enhet",
    choose: "Välj…",
    deadGroup: "Ingen kontakt",
    allGroup: "Alla enheter",
    newestGroup: "Nyaste först",
    next: "Nästa",
    back: "Tillbaka",
    tookOver: "tar över",
    deadTag: "ingen kontakt",
    matchTitle: "Vad hamnar var",
    matchText: "Varje gammal entitet har fått en motsvarighet vald. Ändra den om den är fel.",
    removed: "— tas bort",
    keepsOwn: "Nya, behåller sitt eget entitets-ID",
    usesDevice: "Automationer och skript som använder själva den gamla enheten",
    usesDeviceHint: "De uppdateras. Om den nya enheten använder en annan integration, kontrollera deras enhetsutlösare.",
    removeOld: "Ta bort den gamla enheten",
    removeOldHint: "Behövs för att namnen ska bli lediga. Om den fortfarande finns i ditt Zigbee-nät, ta bort den där också.",
    replace: "Byt nu",
    working: "Byter…",
    doneTitle: "{name} är utbytt",
    doneText: "{n} entiteter flyttades över med sin historik. Automationer och instrumentpaneler fortsätter att fungera.",
    keptOld: "Den gamla enhetens integration tillät inte att den togs bort här – ta bort den där, så att den inte kommer tillbaka.",
    undoHint: "Ångra ger den nya enheten tillbaka sina egna namn. Den gamla kommer bara tillbaka om dess integration hittar den igen.",
    home: "Klar",
    duplicate: "Två gamla entiteter pekar på samma nya.",
    sameDevice: "Välj två olika enheter.",
    error: "Något gick fel: {e}",
    minutes: "{n} min",
    hours: "{n} tim",
    days: "{n} dagar",
    checksTitle: "Kontrollera efter flytten",
    outside: "Används utanför Home Assistant – ändra det där själv: {list}",
    yamlDashboards: "YAML-instrumentpaneler som nämner den gamla enheten – ändra dem själv: {list}",
    droppedUsed: "{name} har ingen motsvarighet men används i: {where}",
    valuesDiffer: "{name}: den nya har inget {missing} (den har {new}). Automationer som använder dessa värden måste ändras.",
    unitDiffers: "{name}: enheten ändras från {old} till {new}.",
    unitEnergy: "{name}: enheten ändras från {old} till {new} – det förstör energistatistiken. Åtgärda det efteråt under Utvecklarverktyg → Statistik.",
    stateClassDiffers: "{name}: ändras från {old} till {new} – långtidsstatistiken kan börja om.",
    statisticsGone: "{name}: den nya sparar ingen långtidsstatistik. Efteråt frågar Home Assistant vad som ska hända med den gamla (Utvecklarverktyg → Statistik).",
    deviceActions: "Enhetsåtgärder från den gamla integrationen kan inte flyttas: {list}",
    otherIntegrations: "Ändra själv i dessa integrationer: {list}",
    packagesByHand: "Ändra själv i packages: {list}",
    fixTitle: "Den kan också ändra dessa",
    fixHint: "Kryssa i det som får ändras. Filer säkerhetskopieras först (.bak-replace-device-…), integrationer ändras via sitt eget inställningsformulär.",
    fixDone: "Ändrat efter ditt OK: {list}",
    fixFailed: "Kunde inte ändras (ändra själv): {list}",
    dashboardsUpdated: "Instrumentpaneler uppdaterade: {list}",
    warnCount: "{n} saker att kontrollera",
    groupsTitle: "Zigbee-grupper",
    groupsText: "Grupper som skapas igen i den nya integrationen med samma namn tar över den gamla gruppens entitets-ID och historik.",
    noGroups: "Inga grupper med samma namn hittades. Skapa gruppen igen i den nya integrationen – med samma namn – så dyker den upp här.",
    unsureTag: "kontrollera",
    aiFailed: "AI:n kunde inte svara ({e}) – det den skulle ha hjälpt med är markerat att kontrollera.",
    aiQuota: "AI:ns dagliga kvot är slut – det den skulle ha hjälpt med är markerat att kontrollera. Det fungerar igen i morgon.",
    rememberedTag: "{n} namn ihågkomna",
    eventTypesDiffer: "{name}: knapptrycken heter något annat nu ({missing} → {new}). Automationer som kontrollerar typen av tryck måste ändras.",
    unsureLine: "Inte säker: {name} → {new}. Kontrollera att det är samma sak.",
    aiTag: "AI",
    aiHint: "Vissa entiteter fick ingen motsvarighet. Anslut en AI under Inställningar → Enheter & tjänster → Replace Device → Konfigurera, så hjälper den till.",
    triggersDone: "{n} knapputlösare översattes till den nya integrationen.",
    triggersOpen: "Kontrollera dessa knapputlösare – ingen motsvarighet hittades:",
    recheck: "Kontrollera knapparna igen",
    tidy: "Städa entitets-ID:n",
    tidyHint: "Entiteter som bara den nya enheten har får ID efter enhetens namn som de andra. Automationer och instrumentpaneler uppdateras också.",
    tidyNone: "Alla entitets-ID följer redan enhetens namn.",
    tidyApply: "Byt namn på {n}",
    tidyDone: "{n} entitets-ID har bytt namn.",
    dryOwnRenamed: "Nya – får ID efter enhetens namn",
    recheckDone: "{n} knapputlösare översatta. Kvar att kontrollera: {open}",
    recheckNone: "Inga knapputlösare kvar att översätta.",
    pressOnce: "Tryck på varje knapp en gång, så att Zigbee2MQTT berättar om den för Home Assistant.",
    edit: "Ändra",
    editTitle: "Ändra namn",
    editIntro: "Ändra vilken entitet på den nya enheten som har vilket namn. Själva enheten flyttas inte – den stannar i {integration}.",
    noneOption: "— ingen (namnet försvinner)",
    save: "Spara",
    giveBack: "Ge den nya enheten tillbaka sina egna namn",
    giveBackWarn: "Den gamla enheten kommer inte tillbaka, och automationer som använder de gamla namnen slutar fungera. Vill du tillbaka till den gamla integrationen? Para enheten där och gör ett nytt byte.",
    cancel: "Avbryt",
    giveBackYes: "Ja, ge tillbaka namnen",
    namesBack: "Namnen tillbakagivna",
    undoAll: "Ångra alla",
    redo: "Gör igen",
    redoAll: "Gör alla igen",
    notMoved: "Kunde inte flyttas (se loggen): {list}",
    batchRow: "{n} enheter flyttade",
    pickOld: "Vilken enhet byts ut?",
    pickNew: "Vilken enhet tar över?",
    search: "Sök namn, område eller modell…",
    allIntegrations: "Alla integrationer",
    sameHardware: "samma enhet",
    sameModel: "samma modell",
    newTag: "ny",
    noResults: "Inget hittades.",
    change: "Ändra",
    migrateTitle: "Flytta många enheter",
    migrateStart: "Flytta många enheter",
    renameStart: "Byt namn på en enhet",
    renameTitle: "Byt namn på en enhet",
    renameText: "Enheten, dess entitets-ID och alla ställen som använder dem får det nya namnet – automationer, skript, instrumentpaneler, hjälpare, YAML och energipanelen. Historiken följer med.",
    renamePick: "Välj enheten som ska byta namn",
    newName: "Nytt namn",
    renameDo: "Byt namn",
    renameWorking: "Byter namn…",
    renameEntities: "Entitets-ID som ändras",
    renameNone: "Inga entitets-ID ändras – bara enhetens namn.",
    renameFixed: "Uppdateras automatiskt",
    renameYaml: "YAML-filer",
    renameEsphome: "ESPHome – installera enheten igen efteråt",
    renameEnergy: "Energipanelen",
    renameOutside: "Utanför Home Assistant – ändra det där själv",
    renameAlsoZ2m: "Byter även namn i Zigbee2MQTT",
    renameNothingUses: "Inget annat använder dessa entitets-ID.",
    renameDone: "{name} har fått sitt nya namn",
    renameDoneText: "{n} entitets-ID har bytt namn och uppdaterats överallt.",
    renameByHand: "Ändras inte (handskriven konfiguration och andra integrationer) – ändra entitets-ID:n själv:",
    renamedLine: "Bytt namn · {n} entitets-ID",
    sumIds: "Entitets-ID",
    sumPlaces: "Ställen",
    migrateText: "Flyttar du till en annan integration, t.ex. ZHA → Zigbee2MQTT? Para enheterna där först. De matchas via sin Zigbee-adress, serienummer eller MAC-adress – namnen spelar ingen roll.",
    from: "Från",
    to: "Till",
    findPairs: "Hitta par",
    matches: "{n} hittade",
    noTargets: "Hittades ingen annanstans",
    noTargetsHint: "Ingen av dina {source}-enheter finns i en annan integration än. Para dem först i integrationen du flyttar till – då dyker den upp här.",
    pairsFound: "{n} enheter hittades i båda",
    noPairs: "Ingen enhet hittades i båda. Para dem i {target} först.",
    by_ieee: "Zigbee-adress",
    by_serial: "serienummer",
    by_mac: "MAC-adress",
    entitiesMatched: "{m}/{t} entiteter",
    missing: "{n} enheter i {source} har ingen partner i {target} än.",
    renameZ2m: "Samma namn i Zigbee2MQTT",
    renameZ2mHint: "Enheten får sitt Home Assistant-namn även i Zigbee2MQTT. Entitets-ID:n ändras inte.",
    moveN: "Flytta {n} enheter",
    migrateDone: "{d} enheter flyttade",
    migrateDoneText: "{n} entiteter flyttades över med sin historik. Varje enhet kan ändras under Bytta.",
    all: "Alla",
    none: "Inga",
    dryRun: "Testa först",
    dryWorking: "Testar…",
    planning: "Förbereder…",
    planningHint: "Parar ihop entiteterna och kontrollerar automationer – frågar AI om något är oklart. Det kan ta några sekunder.",
    dryTitle: "Testkörning – inget har ändrats",
    dryMoreUnused: "{n} till som inte används någonstans – visa",
    dryAllUnused: "{n} entiteter, ingen används någonstans – visa",
    sumMoved: "Flyttas över",
    sumUpdated: "Uppdateras",
    sumButtons: "Knappar",
    sumCheck: "Att kontrollera",
    usedIn: "Används i",
    notUsed: "Används ingenstans",
    dryUpdated: "Uppdateras automatiskt",
    dryCheck: "Kontrollera själv",
    dryAllGood: "Inget att kontrollera",
    dryNewName: "Ny enhet",
    dryOldName: "Får namnet",
    dryIntro: "Så här skulle det gå. Gå tillbaka och tryck på knappen för att göra det på riktigt.",
    dryEntities: "Tar över de gamla namnen och historiken",
    dryDropped: "Tas bort – ingen motsvarighet på den nya enheten",
    dryOwn: "Nya – behåller sitt eget entitets-ID",
    dryDevice: "{from} döps om till {to}",
    dryArea: "Område: {area}",
    dryRemove: "Den gamla enheten tas bort från sin integration",
    dryKeep: "Den gamla enheten behålls",
    dryZ2m: "Döps om i Zigbee2MQTT till {name}",
    dryUsers: "Automationer, skript och scener som pekas om till den nya enheten",
    dryTriggers: "Knapputlösare som översätts",
    byHand: "ändra själv i {file}",
    dryUnresolved: "Knapputlösare du själv måste kontrollera",
    dryDashboards: "Instrumentpaneler som uppdateras",
    dryIntegrations: "Andra integrationer som uppdateras",
    dryBack: "Tillbaka",
  },
  nl: {
    historyAll: "Vervangen ({n})",
    dryOldMarked: "Het oude apparaat heet dan {name}, zodat je ziet dat het verwijderd kan worden",
    needsAction: "Moet bekeken worden",
    historyDone: "Klaar ({n})",
    todoButtons: "{n} knoptriggers controleren",
    todoIds: "{n} entiteit-ID's kunnen opgeruimd worden",
    markDone: "Markeer als klaar",
    openEdit: "Openen",
    title: "Apparaat vervangen",
    heroTitle: "Is er een apparaat kapot?",
    heroText: "Koppel eerst het nieuwe. Dat neemt dan de naam, entiteit-ID's en geschiedenis van het oude over – je automatiseringen en dashboards blijven werken.",
    start: "Een apparaat vervangen",
    leftoversTitle: "Achtergebleven na een verhuizing",
    leftoversHint: "Al verhuisd – maar de oude integratie kent het oude apparaat nog. Verwijder het, zodat het niet terugkomt met nieuwe namen.",
    movedTo: "Verhuisd naar {name}",
    removeLeftover: "Het oude verwijderen",
    removeFailed: "Kon hier niet worden verwijderd – verwijder het in {integration}.",
    dead: "Geen contact",
    deadHint: "Niet per se kapot – vaak een lege batterij, een lamp die met de schakelaar is uitgezet of buiten bereik.",
    batteryLast: "Batterij laatst: {n} %",
    batteryLow: "Batterij laatst: {n} % – vervang eerst de batterij",
    maybeOff: "Met de schakelaar uitgezet, of buiten bereik?",
    hide: "Verbergen – hij staat alleen uit",
    unhide: "Weer tonen",
    showHidden: "{n} verborgen – tonen",
    hideHidden: "Verborgen weer verbergen",
    noDead: "Alles meldt zich.",
    deadFor: "Geen contact sinds {t}",
    twin: "Mogelijke vervanger",
    replaceWith: "Vervangen door {name}",
    pickReplacement: "Vervanger kiezen",
    history: "Vervangen",
    undo: "Ongedaan maken",
    undone: "Ongedaan gemaakt",
    moved: "{n} entiteiten overgezet",
    pickTitle: "Welk apparaat wordt vervangen?",
    old: "Oud apparaat",
    new: "Nieuw apparaat",
    choose: "Kiezen…",
    deadGroup: "Geen contact",
    allGroup: "Alle apparaten",
    newestGroup: "Nieuwste eerst",
    next: "Volgende",
    back: "Terug",
    tookOver: "neemt over",
    deadTag: "geen contact",
    matchTitle: "Wat gaat waarheen",
    matchText: "Voor elke oude entiteit is een tegenhanger gekozen. Pas het aan als het niet klopt.",
    removed: "— verwijderd",
    keepsOwn: "Nieuw, houden hun eigen entiteit-ID",
    usesDevice: "Automatiseringen en scripts die het oude apparaat zelf gebruiken",
    usesDeviceHint: "Ze worden bijgewerkt. Als het nieuwe apparaat een andere integratie gebruikt, controleer dan hun apparaattriggers.",
    removeOld: "Het oude apparaat verwijderen",
    removeOldHint: "Nodig om de namen vrij te maken. Zit het nog in je Zigbee-netwerk, verwijder het daar dan ook.",
    replace: "Nu vervangen",
    working: "Bezig met vervangen…",
    doneTitle: "{name} is vervangen",
    doneText: "{n} entiteiten met hun geschiedenis overgezet. Automatiseringen en dashboards blijven werken.",
    keptOld: "De integratie van het oude apparaat liet verwijderen hier niet toe – verwijder het daar, zodat het niet terugkomt.",
    undoHint: "Ongedaan maken geeft het nieuwe apparaat zijn eigen namen terug. Het oude komt alleen terug als zijn integratie het weer vindt.",
    home: "Klaar",
    duplicate: "Twee oude entiteiten wijzen naar dezelfde nieuwe.",
    sameDevice: "Kies twee verschillende apparaten.",
    error: "Er ging iets mis: {e}",
    minutes: "{n} min",
    hours: "{n} uur",
    days: "{n} dagen",
    checksTitle: "Controleren na de verhuizing",
    outside: "Gebruikt buiten Home Assistant – pas het daar zelf aan: {list}",
    yamlDashboards: "YAML-dashboards die het oude apparaat noemen – pas ze zelf aan: {list}",
    droppedUsed: "{name} heeft geen tegenhanger maar wordt gebruikt in: {where}",
    valuesDiffer: "{name}: het nieuwe heeft geen {missing} (het heeft {new}). Automatiseringen die deze waarden gebruiken moeten worden aangepast.",
    unitDiffers: "{name}: de eenheid verandert van {old} naar {new}.",
    unitEnergy: "{name}: de eenheid verandert van {old} naar {new} – dat breekt de energiestatistieken. Los het daarna op onder Ontwikkelhulpmiddelen → Statistieken.",
    stateClassDiffers: "{name}: verandert van {old} naar {new} – de langetermijnstatistieken kunnen opnieuw beginnen.",
    statisticsGone: "{name}: het nieuwe bewaart geen langetermijnstatistieken. Daarna vraagt Home Assistant wat er met de oude moet gebeuren (Ontwikkelhulpmiddelen → Statistieken).",
    deviceActions: "Apparaatacties van de oude integratie kunnen niet worden overgezet: {list}",
    otherIntegrations: "Zelf aanpassen in deze integraties: {list}",
    packagesByHand: "Zelf aanpassen in packages: {list}",
    fixTitle: "Dit kan het ook aanpassen",
    fixHint: "Vink aan wat mag worden aangepast. Bestanden worden eerst geback-upt (.bak-replace-device-…), integraties via hun eigen instellingenformulier.",
    fixDone: "Aangepast na je OK: {list}",
    fixFailed: "Kon niet worden aangepast (zelf doen): {list}",
    dashboardsUpdated: "Dashboards bijgewerkt: {list}",
    warnCount: "{n} dingen om te controleren",
    groupsTitle: "Zigbee-groepen",
    groupsText: "Groepen die in de nieuwe integratie opnieuw met dezelfde naam worden gemaakt, nemen de entiteit-ID en geschiedenis van de oude groep over.",
    noGroups: "Geen groepen met dezelfde naam gevonden. Maak de groep opnieuw in de nieuwe integratie – met dezelfde naam – en hij verschijnt hier.",
    unsureTag: "controleren",
    aiFailed: "De AI kon niet antwoorden ({e}) – waar hij bij had geholpen, is gemarkeerd om te controleren.",
    aiQuota: "Het dagquotum van de AI is op – waar hij bij had geholpen, is gemarkeerd om te controleren. Morgen werkt het weer.",
    rememberedTag: "{n} namen onthouden",
    eventTypesDiffer: "{name}: de knopdrukken heten nu anders ({missing} → {new}). Automatiseringen die het soort druk controleren moeten worden aangepast.",
    unsureLine: "Niet zeker: {name} → {new}. Controleer of het hetzelfde is.",
    aiTag: "AI",
    aiHint: "Voor sommige entiteiten is geen tegenhanger gevonden. Koppel een AI onder Instellingen → Apparaten & diensten → Replace Device → Configureren, dan helpt die.",
    triggersDone: "{n} knoptriggers zijn vertaald naar de nieuwe integratie.",
    triggersOpen: "Controleer deze knoptriggers – geen tegenhanger gevonden:",
    recheck: "Knoppen opnieuw controleren",
    tidy: "Entiteit-ID's opruimen",
    tidyHint: "Entiteiten die alleen het nieuwe apparaat heeft krijgen ID's naar de apparaatnaam, net als de andere. Automatiseringen en dashboards worden ook bijgewerkt.",
    tidyNone: "Alle entiteit-ID's volgen al de apparaatnaam.",
    tidyApply: "{n} hernoemen",
    tidyDone: "{n} entiteit-ID's hernoemd.",
    dryOwnRenamed: "Nieuw – krijgen ID's naar de apparaatnaam",
    recheckDone: "{n} knoptriggers vertaald. Nog te controleren: {open}",
    recheckNone: "Geen knoptriggers meer om te vertalen.",
    pressOnce: "Druk elke knop één keer in, zodat Zigbee2MQTT hem aan Home Assistant doorgeeft.",
    edit: "Wijzigen",
    editTitle: "Namen wijzigen",
    editIntro: "Wijzig welke entiteit van het nieuwe apparaat welke naam heeft. Het apparaat zelf wordt niet verplaatst – het blijft in {integration}.",
    noneOption: "— geen (de naam verdwijnt)",
    save: "Opslaan",
    giveBack: "Het nieuwe apparaat zijn eigen namen teruggeven",
    giveBackWarn: "Het oude apparaat komt niet terug, en automatiseringen die de oude namen gebruiken werken niet meer. Terug naar de oude integratie? Koppel het apparaat daar en maak een nieuwe vervanging.",
    cancel: "Annuleren",
    giveBackYes: "Ja, namen teruggeven",
    namesBack: "Namen teruggegeven",
    undoAll: "Alles ongedaan maken",
    redo: "Opnieuw doen",
    redoAll: "Alles opnieuw doen",
    notMoved: "Konden niet worden overgezet (zie het logboek): {list}",
    batchRow: "{n} apparaten verhuisd",
    pickOld: "Welk apparaat wordt vervangen?",
    pickNew: "Welk apparaat neemt het over?",
    search: "Zoek naam, ruimte of model…",
    allIntegrations: "Alle integraties",
    sameHardware: "hetzelfde apparaat",
    sameModel: "hetzelfde model",
    newTag: "nieuw",
    noResults: "Niets gevonden.",
    change: "Wijzigen",
    migrateTitle: "Veel apparaten verhuizen",
    migrateStart: "Veel apparaten verhuizen",
    renameStart: "Een apparaat hernoemen",
    renameTitle: "Een apparaat hernoemen",
    renameText: "Het apparaat, zijn entiteit-ID's en alle plekken die ze gebruiken krijgen de nieuwe naam – automatiseringen, scripts, dashboards, helpers, YAML en het energiedashboard. De geschiedenis blijft.",
    renamePick: "Kies het apparaat om te hernoemen",
    newName: "Nieuwe naam",
    renameDo: "Hernoemen",
    renameWorking: "Bezig met hernoemen…",
    renameEntities: "Entiteit-ID's die veranderen",
    renameNone: "Geen entiteit-ID's veranderen – alleen de apparaatnaam.",
    renameFixed: "Automatisch bijgewerkt",
    renameYaml: "YAML-bestanden",
    renameEsphome: "ESPHome – installeer het apparaat daarna opnieuw",
    renameEnergy: "Energiedashboard",
    renameOutside: "Buiten Home Assistant – pas het daar zelf aan",
    renameAlsoZ2m: "Ook hernoemd in Zigbee2MQTT",
    renameNothingUses: "Niets anders gebruikt deze entiteit-ID's.",
    renameDone: "{name} heeft de nieuwe naam",
    renameDoneText: "{n} entiteit-ID's hernoemd en overal bijgewerkt.",
    renameByHand: "Niet gewijzigd (handgeschreven configuratie en andere integraties) – pas de entiteit-ID's zelf aan:",
    renamedLine: "Hernoemd · {n} entiteit-ID's",
    sumIds: "Entiteit-ID's",
    sumPlaces: "Plekken",
    migrateText: "Verhuis je naar een andere integratie, bijv. ZHA → Zigbee2MQTT? Koppel de apparaten daar eerst. Ze worden herkend aan hun Zigbee-adres, serienummer of MAC-adres – namen maken niet uit.",
    from: "Van",
    to: "Naar",
    findPairs: "Paren zoeken",
    matches: "{n} gevonden",
    noTargets: "Nergens anders gevonden",
    noTargetsHint: "Geen van je {source}-apparaten zit al in een andere integratie. Koppel ze eerst in de integratie waarnaar je verhuist – dan verschijnt die hier.",
    pairsFound: "{n} apparaten in beide gevonden",
    noPairs: "Geen apparaat in beide gevonden. Koppel ze eerst in {target}.",
    by_ieee: "Zigbee-adres",
    by_serial: "serienummer",
    by_mac: "MAC-adres",
    entitiesMatched: "{m}/{t} entiteiten",
    missing: "{n} apparaten in {source} hebben nog geen partner in {target}.",
    renameZ2m: "Dezelfde naam in Zigbee2MQTT",
    renameZ2mHint: "Het apparaat krijgt zijn Home Assistant-naam ook in Zigbee2MQTT. Entiteit-ID's worden niet gewijzigd.",
    moveN: "{n} apparaten verhuizen",
    migrateDone: "{d} apparaten verhuisd",
    migrateDoneText: "{n} entiteiten met hun geschiedenis overgezet. Elk apparaat kan worden gewijzigd onder Vervangen.",
    all: "Alle",
    none: "Geen",
    dryRun: "Eerst testen",
    dryWorking: "Bezig met testen…",
    planning: "Bezig met voorbereiden…",
    planningHint: "Entiteiten koppelen en automatiseringen controleren – de AI wordt gevraagd als iets onduidelijk is. Dit kan een paar seconden duren.",
    dryTitle: "Testrun – er is niets gewijzigd",
    dryMoreUnused: "{n} meer, nergens gebruikt – toon",
    dryAllUnused: "{n} entiteiten, geen enkele gebruikt – toon",
    sumMoved: "Overgenomen",
    sumUpdated: "Bijgewerkt",
    sumButtons: "Knoppen",
    sumCheck: "Te controleren",
    usedIn: "Gebruikt in",
    notUsed: "Nergens gebruikt",
    dryUpdated: "Automatisch bijgewerkt",
    dryCheck: "Controleer deze zelf",
    dryAllGood: "Niets te controleren",
    dryNewName: "Nieuw apparaat",
    dryOldName: "Krijgt de naam",
    dryIntro: "Zo zou het gaan. Ga terug en druk op de knop om het echt te doen.",
    dryEntities: "Neemt de oude namen en geschiedenis over",
    dryDropped: "Wordt verwijderd – geen tegenhanger op het nieuwe apparaat",
    dryOwn: "Nieuw – houden hun eigen entiteit-ID",
    dryDevice: "{from} wordt hernoemd naar {to}",
    dryArea: "Ruimte: {area}",
    dryRemove: "Het oude apparaat wordt uit zijn integratie verwijderd",
    dryKeep: "Het oude apparaat blijft behouden",
    dryZ2m: "Hernoemd in Zigbee2MQTT naar {name}",
    dryUsers: "Automatiseringen, scripts en scènes die naar het nieuwe apparaat worden omgezet",
    dryTriggers: "Knoptriggers die worden vertaald",
    byHand: "zelf aanpassen in {file}",
    dryUnresolved: "Knoptriggers die je zelf moet controleren",
    dryDashboards: "Dashboards die worden bijgewerkt",
    dryIntegrations: "Andere integraties die worden bijgewerkt",
    dryBack: "Terug",
  },
};

const DOMAIN_ICON = {
  sensor: "mdi:eye", binary_sensor: "mdi:radiobox-marked", light: "mdi:lightbulb", switch: "mdi:toggle-switch",
  button: "mdi:gesture-tap-button", event: "mdi:bell-ring", climate: "mdi:thermostat", cover: "mdi:window-shutter",
  fan: "mdi:fan", lock: "mdi:lock", number: "mdi:ray-vertex", select: "mdi:format-list-bulleted", update: "mdi:package-up",
};
const CLASS_ICON = {
  temperature: "mdi:thermometer", humidity: "mdi:water-percent", battery: "mdi:battery", pressure: "mdi:gauge",
  illuminance: "mdi:brightness-5", motion: "mdi:motion-sensor", occupancy: "mdi:home-account", door: "mdi:door",
  window: "mdi:window-open", power: "mdi:flash", energy: "mdi:lightning-bolt", voltage: "mdi:sine-wave",
  signal_strength: "mdi:wifi", moisture: "mdi:water", carbon_dioxide: "mdi:molecule-co2",
};

// Button presses in plain words, for the test run. Anything not recognised is shown as it is.
const PRESS = {
  en: { toggle: "toggle", button: "Button", short: "short press", double: "double press", triple: "triple press", long: "long press", longUp: "release after long press", down: "press down", on: "on", off: "off", up: "brighter", dim: "dimmer", stop: "stop", left: "left", right: "right" },
  da: { toggle: "skift", button: "Knap", short: "kort tryk", double: "dobbelttryk", triple: "tredobbelt tryk", long: "langt tryk", longUp: "slip efter langt tryk", down: "tryk ned", on: "tænd", off: "sluk", up: "lysere", dim: "mørkere", stop: "stop", left: "venstre", right: "højre" },
  de: { toggle: "umschalten", button: "Taste", short: "kurz drücken", double: "doppelt drücken", triple: "dreifach drücken", long: "lang drücken", longUp: "loslassen nach lang", down: "herunterdrücken", on: "ein", off: "aus", up: "heller", dim: "dunkler", stop: "stopp", left: "links", right: "rechts" },
  sv: { toggle: "växla", button: "Knapp", short: "kort tryck", double: "dubbeltryck", triple: "trippeltryck", long: "långt tryck", longUp: "släpp efter långt tryck", down: "tryck ned", on: "på", off: "av", up: "ljusare", dim: "mörkare", stop: "stopp", left: "vänster", right: "höger" },
  nl: { toggle: "schakelen", button: "Knop", short: "kort drukken", double: "dubbel drukken", triple: "driedubbel drukken", long: "lang drukken", longUp: "loslaten na lang", down: "indrukken", on: "aan", off: "uit", up: "feller", dim: "donkerder", stop: "stop", left: "links", right: "rechts" },
};
function pressWords(label, code) {
  const w = PRESS[code] || (["nb", "nn", "no"].includes(code) ? PRESS.da : PRESS.en);
  const text = String(label || "").replace(/\s*\(.*\)\s*$/, "");
  if (!text || text.startsWith("blueprint:")) return text;
  const words = text.toLowerCase().replace(/([a-z])(\d)/g, "$1 $2").replace(/(\d)([a-z])/g, "$1 $2").split(/[\s_/:-]+/).filter(Boolean);
  const has = (...xs) => xs.some((x) => words.includes(x));
  const num = words.find((x) => /^\d+$/.test(x));
  let kind = null;
  if (has("double", "dbl")) kind = w.double;
  else if (has("triple")) kind = w.triple;
  else if (has("brightness", "dim") && has("up")) kind = w.up;
  else if (has("brightness", "dim") && has("down")) kind = w.dim;
  else if (has("long", "hold") && has("release")) kind = w.longUp;
  else if (has("long", "hold")) kind = w.long;
  else if (has("toggle")) kind = w.toggle;
  else if (has("stop")) kind = w.stop;
  else if (has("initial") || (has("press") && has("down"))) kind = w.down;
  else if (has("short", "single", "click", "release", "press", "pressed")) kind = w.short;
  const side = has("left") ? w.left : has("right") ? w.right : null;
  const onoff = has("on") ? w.on : has("off") ? w.off : null;
  const parts = [num ? `${w.button} ${num}` : side || onoff, kind].filter(Boolean);
  if (!parts.length) return text;
  const out = parts.join(", ");
  return out.charAt(0).toUpperCase() + out.slice(1);
}
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class ReplaceDevicePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.view = "home";
    this.devices = [];
    this.historyItems = [];
    this.plan = null;
    this.mapping = {};
    this.removeOld = true;
    this.result = null;
    this.error = "";
    this.oldId = "";
    this.newId = "";
    this.query = "";
    this.srcFilter = "";
    this.renameZ2m = true;
    this.migrateSource = "";
    this.migrateTarget = "";
    this.migratePlan = null;
    this.migrateSelected = new Set();
    this.groupSelected = new Set();
    this.picked = { files: new Set(), entries: new Set() };
  }

  // What the user ticked in the test run: their own files and other integrations' settings.
  pickedFix() {
    return { files: [...this.picked.files], entries: [...this.picked.entries] };
  }

  fixBlock(fixable) {
    const items = [
      ...(fixable?.files || []).map((f) => ({ kind: "files", id: f.file, name: f.file, icon: "mdi:file-code-outline", lines: f.lines })),
      ...(fixable?.entries || []).map((e) => ({ kind: "entries", id: e.entry_id, name: e.title, icon: "mdi:puzzle", lines: e.lines })),
    ];
    if (!items.length) return "";
    const row = (it) => `<label class="mrow fixrow"><input type="checkbox" data-fix="${it.kind}" data-fixid="${esc(it.id)}" ${this.picked[it.kind].has(it.id) ? "checked" : ""}><span class="box"></span>
        <div class="grow"><div class="dname"><ha-icon icon="${it.icon}"></ha-icon> ${esc(it.name)}</div>
        ${(it.lines || []).map((l) => `<div class="mono small fixline"><span class="red-text">− ${esc(l.before)}</span><br><span class="ok-text">+ ${esc(l.after)}</span></div>`).join("")}</div></label>`;
    return `<h3 class="dsec warn-text"><ha-icon icon="mdi:check-decagram-outline"></ha-icon>${this.t("fixTitle")}</h3>
      <p class="muted small">${this.t("fixHint")}</p>${items.map(row).join("")}`;
  }

  fixResult(fixed) {
    if (!fixed) return "";
    const done = [...(fixed.files || []), ...(fixed.entries || [])];
    return `${done.length ? `<p class="ok-text">${esc(this.t("fixDone", { list: done.join(", ") }))}</p>` : ""}
      ${(fixed.failed || []).length ? `<p class="warn-text">${esc(this.t("fixFailed", { list: fixed.failed.join(", ") }))}</p>` : ""}`;
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this.load();
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = hass;
  }

  set narrow(narrow) {
    this._narrow = narrow;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.narrow = narrow;
  }

  t(key, vars = {}) {
    const code = (this._hass?.language || "en").split("-")[0];
    const lang = TEXT[code] ? code : code === "nb" || code === "nn" || code === "no" ? "da" : "en";
    return (TEXT[lang][key] || TEXT.en[key]).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  }

  ago(ts) {
    const s = Math.max(0, (Date.now() / 1000) - ts);
    if (s < 3600) return this.t("minutes", { n: Math.round(s / 60) });
    if (s < 172800) return this.t("hours", { n: Math.round(s / 3600) });
    return this.t("days", { n: Math.round(s / 86400) });
  }

  async ws(type, data = {}) {
    return this._hass.callWS({ type: `replace_device/${type}`, ...data });
  }

  async load() {
    try {
      const [devices, history] = await Promise.all([this.ws("devices"), this.ws("history")]);
      this.devices = devices.devices;
      this.historyItems = history.history;
      this.error = "";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code || e });
    }
    this.render();
  }

  device(id) {
    return this.devices.find((d) => d.id === id);
  }

  async openPlan(oldId, newId, mapping) {
    if (!oldId || !newId || oldId === newId) {
      this.error = this.t("sameDevice");
      return this.render();
    }
    this.oldId = oldId;
    this.newId = newId;
    const back = this.view;
    if (!mapping) {
      // A fresh plan can take a few seconds (checks, maybe the AI): show that something is happening.
      this.view = "working";
      this.planning = true;
      this.error = "";
      this.render();
    }
    try {
      if (!mapping) this.picked = { files: new Set(), entries: new Set() };
      this.plan = await this.ws("plan", { old: oldId, new: newId, ...(mapping ? { mapping } : {}) });
      this.mapping = { ...this.plan.mapping };
      this.view = "match";
      this.error = "";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
      this.view = back;
    }
    this.planning = false;
    this.render();
  }

  async doReplace() {
    const picked = Object.values(this.mapping).filter(Boolean);
    if (picked.length !== new Set(picked).size) {
      this.error = this.t("duplicate");
      return this.render();
    }
    this.view = "working";
    this.render();
    try {
      this.result = await this.ws("replace", { old: this.oldId, new: this.newId, mapping: this.mapping, remove_old: this.removeOld, rename_z2m: Boolean(this.plan.new.z2m && this.renameZ2m), fix: this.pickedFix() });
      this.result.name = this.plan.old.name;
      this.view = "done";
      this.error = "";
    } catch (e) {
      this.view = "match";
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
    this.load();
  }

  async redo(id, batch) {
    try {
      await this.ws("redo", batch ? { batch } : { record: id });
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.load();
  }

  async undo(id, batch) {
    try {
      await this.ws("undo", batch ? { batch } : { record: id });
      this.view = "home";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.load();
  }

  icon(e) {
    return esc(e.icon || CLASS_ICON[e.device_class] || DOMAIN_ICON[e.domain] || "mdi:shape");
  }

  // ---------- views ----------

  homeView() {
    const leftovers = this.devices.filter((d) => d.moved_to);
    const quiet = this.devices.filter((d) => d.dead && !d.moved_to).sort((a, b) => (b.twins?.length || 0) - (a.twins?.length || 0));
    const shown = quiet.filter((d) => !d.hidden);
    const hidden = quiet.filter((d) => d.hidden);
    const card = (d) => {
      const twin = d.twins?.length ? this.device(d.twins[0]) : null;
      const low = d.battery != null && d.battery <= 20;
      const why = d.battery != null
        ? `<div class="why ${low ? "low" : ""}"><ha-icon icon="${low ? "mdi:battery-alert-variant-outline" : "mdi:battery-50"}"></ha-icon><span>${this.t(low ? "batteryLow" : "batteryLast", { n: Math.round(d.battery) })}</span></div>`
        : `<div class="why"><ha-icon icon="mdi:power-plug-off-outline"></ha-icon><span>${this.t("maybeOff")}</span></div>`;
      return `
        <div class="card dead-card ${d.hidden ? "is-hidden" : ""}">
          <div class="dev-head">
            <div class="dot ${d.hidden ? "grey" : "red"}"></div>
            <div class="grow">
              <div class="dev-name">${esc(d.name)}</div>
              <div class="muted">${esc([d.area, d.model, d.integration_title].filter(Boolean).join(" · "))}</div>
              <div class="muted small">${esc(this.t("deadFor", { t: d.dead_since ? this.ago(d.dead_since) : "?" }))}</div>
            </div>
          </div>
          ${why}
          ${twin ? `
            <div class="twin"><ha-icon icon="mdi:auto-fix"></ha-icon><div class="grow"><div class="small muted">${this.t("twin")}</div><b>${esc(twin.name)}</b></div></div>
            <button class="primary full" data-act="plan" data-old="${d.id}" data-new="${twin.id}">${esc(this.t("replaceWith", { name: twin.name }))}</button>` : ""}
          <div class="card-links">
            ${twin ? "" : `<button class="link" data-act="pick" data-old="${d.id}">${this.t("pickReplacement")}</button>`}
            <button class="link" data-act="${d.hidden ? "unhide" : "hide"}" data-id="${d.id}">${this.t(d.hidden ? "unhide" : "hide")}</button>
          </div>
        </div>`;
    };
    const deadCards = shown.length
      ? shown.map(card).join("")
      : `<div class="card empty"><ha-icon icon="mdi:check-circle"></ha-icon>${this.t("noDead")}</div>`;
    const hiddenPart = hidden.length
      ? `<p class="center-link"><button class="link" data-act="toggleHidden">${this.t(this.showHidden ? "hideHidden" : "showHidden", { n: hidden.length })}</button></p>
         ${this.showHidden ? `<div class="grid">${hidden.map(card).join("")}</div>` : ""}`
      : "";
    const rows = [];
    const open = (h) => !h.undone && !h.done && (h.todo?.buttons || h.todo?.ids);
    const needs = this.historyItems.filter(open);
    for (const h of this.historyItems.filter((x) => !open(x))) {
      const last = rows[rows.length - 1];
      if (h.batch && last?.batch === h.batch) last.items.push(h);
      else rows.push({ batch: h.batch, items: [h] });
    }
    const history = rows.map((g) => (g.items.length > 1 ? this.batchRow(g) : this.historyRow(g.items[0]))).join("");
    return `
      <div class="hero card">
        <div class="hero-icon"><ha-icon icon="mdi:swap-horizontal-circle"></ha-icon></div>
        <div class="grow"><h2>${this.t("heroTitle")}</h2><p class="muted">${this.t("heroText")}</p>
        <div class="btns"><button class="primary" data-act="pick">${this.t("start")}</button>
        <button class="ghost" data-act="migrate"><ha-icon icon="mdi:transfer"></ha-icon>${this.t("migrateStart")}</button>
        <button class="ghost" data-act="renameStart"><ha-icon icon="mdi:rename"></ha-icon>${this.t("renameStart")}</button></div></div>
      </div>
      ${leftovers.length ? `<h3>${this.t("leftoversTitle")} <span class="count">${leftovers.length}</span></h3>
        <p class="muted small section-hint">${this.t("leftoversHint")}</p>
        <div class="grid">${leftovers.map((d) => this.leftoverCard(d)).join("")}</div>` : ""}
      <h3>${this.t("dead")} ${shown.length ? `<span class="count">${shown.length}</span>` : ""}</h3>
      <p class="muted small section-hint">${this.t("deadHint")}</p>
      <div class="grid">${deadCards}</div>
      ${hiddenPart}
      ${needs.length ? `<h3>${this.t("needsAction")} <span class="count amber">${needs.length}</span></h3><div class="card list">${needs.map((h) => this.historyRow(h)).join("")}</div>` : ""}
      ${history ? `<details class="dmore hist-done"><summary><ha-icon icon="mdi:check-circle"></ha-icon> ${esc(this.t(needs.length ? "historyDone" : "historyAll", { n: this.historyItems.length - needs.length }))}</summary><div class="card list">${history}</div></details>` : ""}`;
  }

  // What could still bite, as lines; also used to count them in "move many".
  checkLines(c) {
    if (!c) return [];
    const name = (id) => id;
    const lines = [];
    for (const u of c.unsure || []) lines.push(["warn", this.t("unsureLine", { name: name(u.entity_id), new: u.new })]);
    for (const d of c.dropped_used || []) lines.push(["warn", this.t("droppedUsed", { name: name(d.entity_id), where: d.used_in.join(", ") })]);
    for (const e of c.differences || []) {
      for (const d of e.differences) {
        if (d.kind === "values" && e.entity_id.startsWith("event.")) lines.push(["warn", this.t("eventTypesDiffer", { name: name(e.entity_id), missing: d.missing.join(", "), new: d.new.join(", ") })]);
        else if (d.kind === "values") lines.push(["warn", this.t("valuesDiffer", { name: name(e.entity_id), missing: d.missing.join(", "), new: d.new.join(", ") })]);
        else if (d.kind === "unit") lines.push([e.energy ? "bad" : "warn", this.t(e.energy ? "unitEnergy" : "unitDiffers", { name: name(e.entity_id), old: d.old, new: d.new })]);
        else if (d.kind === "statistics_gone") lines.push(["info", this.t("statisticsGone", { name: name(e.entity_id) })]);
        else lines.push(["warn", this.t("stateClassDiffers", { name: name(e.entity_id), old: d.old, new: d.new })]);
      }
    }
    if (c.outside?.length) lines.push(["bad", this.t("outside", { list: c.outside.join(", ") })]);
    if (c.yaml_dashboards?.length) lines.push(["bad", this.t("yamlDashboards", { list: c.yaml_dashboards.join(", ") })]);
    if (c.device_actions?.length) lines.push(["warn", this.t("deviceActions", { list: c.device_actions.join(", ") })]);
    if (c.integrations?.length) lines.push(["warn", this.t("otherIntegrations", { list: c.integrations.join(", ") })]);
    if (c.packages?.length) lines.push(["warn", this.t("packagesByHand", { list: c.packages.join(", ") })]);
    if (c.dashboards?.length) lines.push(["info", this.t("dashboardsUpdated", { list: c.dashboards.join(", ") })]);
    return lines;
  }

  checksCard(c) {
    const lines = this.checkLines(c);
    if (!lines.length) return "";
    const icon = { bad: "mdi:alert-octagon", warn: "mdi:alert", info: "mdi:information-outline" };
    return `<div class="card warn"><h3 class="in"><ha-icon icon="mdi:clipboard-check-outline"></ha-icon> ${this.t("checksTitle")}</h3>
      <div class="checks">${lines.map(([k, txt]) => `<div class="check-line c-${k}"><ha-icon icon="${icon[k]}"></ha-icon><span>${esc(txt)}</span></div>`).join("")}</div></div>`;
  }

  leftoverCard(d) {
    return `
      <div class="card leftover">
        <div class="dev-head"><ha-icon icon="mdi:ghost-outline"></ha-icon>
          <div class="grow"><div class="dev-name">${esc(d.name)}</div>
            <div class="muted small">${esc([d.area, d.integration_title].filter(Boolean).join(" · "))}</div>
            <div class="small ok-text">${esc(this.t("movedTo", { name: d.moved_to }))}</div></div></div>
        <button class="ghost full" data-act="removeLeftover" data-id="${d.id}" data-integration="${esc(d.integration_title || "")}">${this.t("removeLeftover")}</button>
      </div>`;
  }

  async removeLeftover(id, integration) {
    try {
      const r = await this.ws("remove_device", { device: id });
      this.error = r.removed ? "" : this.t("removeFailed", { integration });
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    if (this.view === "migrate" && this.migratePlan) await this.findPairs();
    this.load();
  }

  aiNote(error) {
    if (!error) return "";
    const text = error === "quota" ? this.t("aiQuota") : this.t("aiFailed", { e: error });
    return `<p class="hint left-hint"><ha-icon icon="mdi:robot-confused-outline"></ha-icon><span>${esc(text)}</span></p>`;
  }

  historyRow(h) {
    if (h.kind === "rename") {
      return `
      <div class="hist">
        <ha-icon icon="mdi:rename"></ha-icon>
        <div class="grow"><b>${esc(h.old_device.name)}</b> → ${esc(h.new_device.name)}
          <div class="muted small">${new Date(h.at * 1000).toLocaleString(this._hass.language)} · ${esc(this.t("renamedLine", { n: h.renamed }))}</div></div>
        ${h.undone ? `<span class="tag">${this.t("undone")}</span>` : `<button class="ghost small-btn" data-act="undo" data-id="${h.id}">${this.t("undo")}</button>`}
      </div>`;
    }
    return `
      <div class="hist">
        <ha-icon icon="mdi:swap-horizontal"></ha-icon>
        <div class="grow"><b>${esc(h.old_device.name)}</b> → ${esc(h.new_device.model || h.new_device.name)}
          <div class="muted small">${new Date(h.at * 1000).toLocaleString(this._hass.language)} · ${this.t("moved", { n: h.moved })}</div>
          ${!h.undone && !h.done && (h.todo?.buttons || h.todo?.ids) ? `<div class="small warn-text">${[h.todo.buttons ? esc(this.t("todoButtons", { n: h.todo.buttons })) : "", h.todo.ids ? esc(this.t("todoIds", { n: h.todo.ids })) : ""].filter(Boolean).join(" · ")}</div>
            <button class="link small" data-act="markDone" data-id="${h.id}">${this.t("markDone")}</button>` : ""}</div>
        ${h.undone ? `<span class="tag">${this.t("namesBack")}</span><button class="ghost small-btn" data-act="redo" data-id="${h.id}">${this.t("redo")}</button>` : h.new_device?.id ? `<button class="ghost small-btn" data-act="edit" data-id="${h.id}">${this.t("edit")}</button>` : ""}
      </div>`;
  }

  // One "move many": a header with when and how many, then each device with its own "Change".
  batchRow(g) {
    return `
      <div class="hist batch-head">
        <ha-icon icon="mdi:transfer"></ha-icon>
        <div class="grow"><b>${this.t("batchRow", { n: g.items.length })}</b>
          <div class="muted small">${new Date(g.items[0].at * 1000).toLocaleString(this._hass.language)}</div></div>
      </div>
      <div class="batch-items">${g.items.map((h) => this.historyRow(h)).join("")}</div>`;
  }

  pickView() {
    const old = this.oldId && this.device(this.oldId);
    const counts = new Map();
    for (const d of this.devices.filter((x) => x.integration)) counts.set(d.integration, [d.integration_title, (counts.get(d.integration)?.[1] || 0) + 1]);
    const sources = [...counts.entries()].sort((a, b) => b[1][1] - a[1][1]);
    return `
      ${old ? `<div class="card chosen"><div class="dev-head"><ha-icon icon="mdi:devices"></ha-icon><div class="grow"><div class="muted small">${this.t("old")}</div><div class="dev-name">${esc(old.name)}</div>
        <div class="muted small">${esc([old.area, old.model, old.integration_title].filter(Boolean).join(" · "))}</div></div>
        <button class="ghost small-btn" data-act="changeOld">${this.t("change")}</button></div></div>` : ""}
      <h3>${this.pickMode === "rename" ? this.t("renamePick") : old ? this.t("pickNew") : this.t("pickOld")}</h3>
      <div class="filters">
        <div class="search"><ha-icon icon="mdi:magnify"></ha-icon><input id="q" type="search" placeholder="${this.t("search")}" value="${esc(this.query)}"></div>
        <select id="src"><option value="">${this.t("allIntegrations")}</option>${sources.map(([k, [v, n]]) => `<option value="${esc(k)}" ${k === this.srcFilter ? "selected" : ""}>${esc(v || k)} (${n})</option>`).join("")}</select>
      </div>
      <div class="pick-list" id="list">${this.pickList()}</div>
      <div class="actions"><button class="ghost" data-act="home">${this.t("back")}</button></div>`;
  }

  pickList() {
    const old = this.oldId && this.device(this.oldId);
    const q = this.query.trim().toLowerCase();
    let list = this.devices.filter((d) => (!this.srcFilter || d.integration === this.srcFilter)
      && (!q || [d.name, d.area, d.model, d.manufacturer, d.integration_title].join(" ").toLowerCase().includes(q)));
    const day = Date.now() / 1000 - 86400;
    const tags = (d) => {
      const out = [];
      if (old && d.hardware?.some((k) => old.hardware?.includes(k))) out.push(`<span class="tag green">${this.t("sameHardware")}</span>`);
      else if (old && d.model && d.model === old.model) out.push(`<span class="tag blue">${this.t("sameModel")}</span>`);
      if (d.remembered) out.push(`<span class="tag">${this.t("rememberedTag", { n: d.remembered })}</span>`);
      if (d.dead) out.push(`<span class="tag red">${this.t("deadTag")}</span>`);
      else if (d.created > day) out.push(`<span class="tag blue">${this.t("newTag")}</span>`);
      return out.join("");
    };
    if (old) {
      const score = (d) => (d.hardware?.some((k) => old.hardware?.includes(k)) ? 1e12 : 0) + (d.model && d.model === old.model ? 1e11 : 0) + d.created;
      list = list.filter((d) => d.id !== old.id && !d.dead).sort((a, b) => score(b) - score(a));
    } else {
      list = list.sort((a, b) => (b.dead - a.dead) || a.name.localeCompare(b.name));
    }
    if (!list.length) return `<div class="card empty">${this.t("noResults")}</div>`;
    return list.slice(0, 60).map((d) => `
      <button class="devpick" data-act="choose" data-id="${d.id}">
        <span class="dot ${d.dead ? "red" : "green"}"></span>
        <span class="grow"><span class="dev-name">${esc(d.name)}</span>
          <span class="muted small">${esc([d.area, [d.manufacturer, d.model].filter(Boolean).join(" "), d.integration_title].filter(Boolean).join(" · "))}</span></span>
        <span class="tags">${tags(d)}</span><ha-icon icon="mdi:chevron-right"></ha-icon>
      </button>`).join("");
  }

  // Integrations with physical devices (Zigbee address, serial number or MAC), with how many.
  migrateSources() {
    const counts = new Map();
    for (const d of this.devices) {
      if (!d.integration || !d.hardware?.length) continue;
      const c = counts.get(d.integration) || { key: d.integration, name: d.integration_title || d.integration, n: 0 };
      c.n += 1;
      counts.set(d.integration, c);
    }
    return [...counts.values()].sort((a, b) => b.n - a.n);
  }

  // Integrations where devices of the source are found again, with how many.
  migrateTargets(source) {
    const keys = new Set(this.devices.filter((d) => d.integration === source).flatMap((d) => d.hardware || []));
    const counts = new Map();
    for (const d of this.devices) {
      if (!d.integration || d.integration === source || !d.hardware?.some((k) => keys.has(k))) continue;
      const c = counts.get(d.integration) || { key: d.integration, name: d.integration_title || d.integration, n: 0 };
      c.n += 1;
      counts.set(d.integration, c);
    }
    return [...counts.values()].sort((a, b) => b.n - a.n);
  }

  migrateView() {
    const sources = this.migrateSources();
    const targets = this.migrateTargets(this.migrateSource);
    if (!targets.some((t) => t.key === this.migrateTarget)) this.migrateTarget = targets[0]?.key || "";
    const all = [...sources, ...targets];
    const name = (k) => esc(all.find((x) => x.key === k)?.name || k);
    const srcOpts = sources.map((x) => `<option value="${esc(x.key)}" ${x.key === this.migrateSource ? "selected" : ""}>${esc(x.name)} (${x.n})</option>`).join("");
    const dstOpts = targets.length
      ? targets.map((x) => `<option value="${esc(x.key)}" ${x.key === this.migrateTarget ? "selected" : ""}>${esc(x.name)} (${this.t("matches", { n: x.n })})</option>`).join("")
      : `<option value="">${this.t("noTargets")}</option>`;
    const plan = this.migratePlan;
    let result = "";
    if (plan) {
      const rows = plan.pairs.map((p) => `
        <label class="mrow"><input type="checkbox" data-pair="${p.old.id}" ${this.migrateSelected.has(p.old.id) ? "checked" : ""}><span class="box"></span>
          <span class="grow"><span class="dev-name">${esc(p.old.name)}</span>
            <span class="muted small">→ ${esc(p.new.name)} · ${this.t("by_" + p.by)} · ${this.t("entitiesMatched", { m: p.matched, t: p.total })}</span>
            ${this.checkLines(p.checks).filter(([k]) => k !== "info").length ? `<span class="small warn-text">⚠ ${this.t("warnCount", { n: this.checkLines(p.checks).filter(([k]) => k !== "info").length })}</span>` : ""}</span>
          ${p.old.area ? `<span class="tag">${esc(p.old.area)}</span>` : ""}</label>`).join("");
      result = plan.pairs.length ? `
        <div class="card">
          <div class="mhead"><h3 class="in">${this.t("pairsFound", { n: plan.pairs.length })}</h3>
            <span><button class="ghost small-btn" data-act="selectAll">${this.t("all")}</button> <button class="ghost small-btn" data-act="selectNone">${this.t("none")}</button></span></div>
          <div class="mrows">${rows}</div>
          ${plan.missing.length ? `<p class="muted small">${this.t("missing", { n: plan.missing.length, source: name(this.migrateSource), target: name(this.migrateTarget) })}</p>` : ""}
        </div>
        ${plan.leftovers?.length ? `<div class="card"><h3 class="in"><ha-icon icon="mdi:ghost-outline"></ha-icon> ${this.t("leftoversTitle")}</h3>
          <p class="muted small">${this.t("leftoversHint")}</p><div class="grid">${plan.leftovers.map((d) => this.leftoverCard(d)).join("")}</div></div>` : ""}
        ${this.groupsCard(plan)}
        ${plan.pairs.filter((p) => this.migrateSelected.has(p.old.id)).map((p) => this.checkLines(p.checks).length ? `<div class="card"><b>${esc(p.old.name)}</b>${this.checksCard(p.checks)}</div>` : "").join("")}
        <div class="card">
          <label class="switch-row"><input type="checkbox" id="removeOld" ${this.removeOld ? "checked" : ""}><span class="switch"></span>
            <div class="grow"><b>${this.t("removeOld")}</b><div class="muted small">${this.t("removeOldHint")}</div></div></label>
          ${this.migrateTarget === "zigbee2mqtt" ? `<label class="switch-row sep"><input type="checkbox" id="renameZ2m" ${this.renameZ2m ? "checked" : ""}><span class="switch"></span>
            <div class="grow"><b>${this.t("renameZ2m")}</b><div class="muted small">${this.t("renameZ2mHint")}</div></div></label>` : ""}
        </div>
        <div class="actions sticky"><button class="ghost" data-act="dryMigrate" ${this.migrateSelected.size ? "" : "disabled"}><ha-icon icon="mdi:test-tube"></ha-icon>${this.t("dryRun")}</button>
          <button class="primary big" data-act="doMigrate" ${this.migrateSelected.size + this.groupSelected.size ? "" : "disabled"}><ha-icon icon="mdi:transfer"></ha-icon>${this.t("moveN", { n: this.migrateSelected.size + this.groupSelected.size })}</button></div>`
        : `<div class="card empty">${this.t("noPairs", { target: name(this.migrateTarget) })}</div>`;
    }
    return `
      <div class="card">
        <h2>${this.t("migrateTitle")}</h2><p class="muted">${this.t("migrateText")}</p>
        <div class="fromto">
          <div><label>${this.t("from")}</label><select id="msrc">${srcOpts}</select></div>
          <ha-icon icon="mdi:arrow-right"></ha-icon>
          <div><label>${this.t("to")}</label><select id="mdst" ${targets.length ? "" : "disabled"}>${dstOpts}</select></div>
        </div>
        ${targets.length ? "" : `<p class="hint"><ha-icon icon="mdi:information-outline"></ha-icon><span>${this.t("noTargetsHint", { source: name(this.migrateSource) })}</span></p>`}
        <div class="actions"><button class="ghost" data-act="home">${this.t("back")}</button><button class="primary" data-act="findPairs" ${this.migrateTarget ? "" : "disabled"}>${this.t("findPairs")}</button></div>
      </div>
      ${result}`;
  }

  groupsCard(plan) {
    const groups = plan.groups || [];
    return `<div class="card"><h3 class="in"><ha-icon icon="mdi:lightbulb-group"></ha-icon> ${this.t("groupsTitle")}</h3>
      <p class="muted small">${groups.length ? this.t("groupsText") : this.t("noGroups")}</p>
      ${groups.map((g) => `<label class="mrow"><input type="checkbox" data-group="${esc(g.old)}" ${this.groupSelected.has(g.old) ? "checked" : ""}><span class="box"></span>
        <span class="grow"><span class="dev-name">${esc(g.name)}</span><span class="muted small">${esc(g.old)} ← ${esc(g.new)}</span></span></label>`).join("")}</div>`;
  }

  migrateDoneView() {
    const r = this.result;
    return `
      <div class="card center done">
        <div class="check"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
        <h2>${this.t("migrateDone", { d: r.devices })}</h2>
        <p class="muted">${this.t("migrateDoneText", { n: r.moved })}</p>
        ${r.triggers?.translated?.length ? `<p class="ok-text">${this.t("triggersDone", { n: r.triggers.translated.length })}</p>` : ""}
        ${this.aiNote(r.ai_error || r.triggers?.ai_error)}
        ${r.triggers?.translated?.length || r.translated ? `<p class="hint left-hint"><ha-icon icon="mdi:gesture-tap-button"></ha-icon><span>${this.t("pressOnce")}</span></p>` : ""}
        ${r.integrations?.length ? `<p class="warn-text">${esc(this.t("otherIntegrations", { list: r.integrations.join(", ") }))}</p>` : ""}
        ${r.packages?.length ? `<p class="warn-text">${esc(this.t("packagesByHand", { list: r.packages.join(", ") }))}</p>` : ""}
        ${this.fixResult(r.fixed)}
        ${r.dashboards?.length ? `<p class="ok-text">${esc(this.t("dashboardsUpdated", { list: r.dashboards.join(", ") }))}</p>` : ""}
        ${(r.triggers?.unresolved || r.unresolved || []).length ? `<div class="card warn left"><b>${this.t("triggersOpen")}</b><ul>${(r.triggers?.unresolved || r.unresolved).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
        <div class="actions"><button class="primary" data-act="home">${this.t("home")}</button></div>
      </div>`;
  }

  async findPairs() {
    this.migrateSource = this.shadowRoot.getElementById("msrc").value;
    this.migrateTarget = this.shadowRoot.getElementById("mdst").value;
    if (!this.migrateSource || this.migrateSource === this.migrateTarget) {
      this.error = this.t("sameDevice");
      return this.render();
    }
    try {
      this.migratePlan = await this.ws("migrate_plan", { source: this.migrateSource, target: this.migrateTarget });
      this.migrateSelected = new Set(this.migratePlan.pairs.filter((p) => p.matched > 0).map((p) => p.old.id));
      this.groupSelected = new Set((this.migratePlan.groups || []).map((g) => g.old));
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async doMigrate() {
    const pairs = this.migratePlan.pairs.filter((p) => this.migrateSelected.has(p.old.id)).map((p) => ({ old: p.old.id, new: p.new.id }));
    const groups = (this.migratePlan.groups || []).filter((g) => this.groupSelected.has(g.old));
    this.view = "working";
    this.render();
    try {
      this.result = await this.ws("migrate", { pairs, groups, remove_old: this.removeOld, rename_z2m: this.migrateTarget === "zigbee2mqtt" && this.renameZ2m, fix: this.pickedFix() });
      this.view = "migrated";
      this.migratePlan = null;
    } catch (e) {
      this.view = "migrate";
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
    this.load();
  }

  // Test run: what a replacement or a move would do, worked out by the backend without changing anything.
  async dryRun() {
    await this.runDry("match", () => this.ws("dry_run", { old: this.oldId, new: this.newId, mapping: this.mapping, remove_old: this.removeOld, rename_z2m: Boolean(this.plan.new.z2m && this.renameZ2m) })
      .then((r) => ({ devices: [{ name: this.plan.old.name, ...r }] })));
  }

  async dryMigrate() {
    const pairs = this.migratePlan.pairs.filter((p) => this.migrateSelected.has(p.old.id)).map((p) => ({ old: p.old.id, new: p.new.id }));
    await this.runDry("migrate", () => this.ws("migrate_dry_run", { pairs, remove_old: this.removeOld, rename_z2m: this.migrateTarget === "zigbee2mqtt" && this.renameZ2m }));
  }

  async runDry(from, job) {
    const picked = Object.values(this.mapping || {}).filter(Boolean);
    if (from === "match" && picked.length !== new Set(picked).size) {
      this.error = this.t("duplicate");
      return this.render();
    }
    this.dryFrom = from;
    this.testing = true;
    this.view = "working";
    this.render();
    try {
      this.dry = await job();
      this.view = "dry";
      this.error = "";
    } catch (e) {
      this.view = from;
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.testing = false;
    this.render();
  }

  async doRename(apply) {
    const input = this.shadowRoot.getElementById("newName");
    if (input) this.renameName = input.value;
    const name = (this.renameName || "").trim();
    if (!name) return;
    this.renaming = apply ? "do" : "dry";
    this.view = "working";
    this.render();
    try {
      const r = await this.ws(apply ? "rename" : "rename_dry_run", { device: this.renameId, name, ...(apply ? { fix: this.pickedFix() } : {}) });
      if (apply) {
        this.renameResult = r;
        this.renameDry = null;
      } else {
        this.renameDry = r;
      }
      this.error = "";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.renaming = "";
    this.view = "rename";
    if (apply) await this.load();
    this.view = "rename";
    this.render();
  }

  renamePlaces(r) {
    const chips = [
      ...(r.users || []).map((u) => [u.startsWith("script") ? "mdi:script-text" : u.startsWith("scene") ? "mdi:palette" : "mdi:robot", u.replace(/^(automation|script|scene): /, "")]),
      ...(r.dashboards || []).map((x) => ["mdi:view-dashboard", x]),
      ...(r.energy ? [["mdi:lightning-bolt", this.t("renameEnergy")]] : []),
    ];
    const canFix = new Set([...(r.fixable?.files || []).map((f) => f.file), ...(r.fixable?.entries || []).map((e) => e.title)]);
    const hand = [
      ...(r.yaml || []).filter((x) => !canFix.has(x)).map((x) => ["mdi:file-code-outline", x]),
      ...(r.integrations || []).filter((x) => !canFix.has(x)).map((x) => ["mdi:puzzle", x]),
    ];
    const chip = ([i, x]) => `<span class="chip sm"><ha-icon icon="${i}"></ha-icon>${esc(x)}</span>`;
    return `
      ${chips.length ? `<h3 class="dsec"><ha-icon icon="mdi:sync"></ha-icon>${this.t("renameFixed")}</h3><div class="dchips">${chips.map(chip).join("")}</div>`
        : `<p class="muted small">${this.t("renameNothingUses")}</p>`}
      ${hand.length ? `<h3 class="dsec warn-text"><ha-icon icon="mdi:file-document-edit-outline"></ha-icon>${this.t("renameByHand")}</h3><div class="dchips">${hand.map(chip).join("")}</div>` : ""}
      ${(r.esphome || []).filter((x) => !canFix.has(x)).length ? `<h3 class="dsec warn-text"><ha-icon icon="mdi:chip"></ha-icon>${this.t("renameEsphome")}</h3><div class="dchips">${r.esphome.filter((x) => !canFix.has(x)).map((x) => chip(["mdi:file-code-outline", x])).join("")}</div>` : ""}
      ${this.fixBlock(r.fixable)}${this.fixResult(r.fixed)}
      ${(r.outside || []).length ? `<h3 class="dsec red-text"><ha-icon icon="mdi:alert-octagon"></ha-icon>${this.t("renameOutside")}</h3><div class="dchips">${r.outside.map((x) => chip(["mdi:file-alert-outline", x])).join("")}</div>` : ""}`;
  }

  renameView() {
    const d = this.device(this.renameId);
    if (this.renameResult) {
      const r = this.renameResult;
      return `
        <div class="card center"><div class="check"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M14 27l8 8 16-16"/></svg></div>
          <h2>${esc(this.t("renameDone", { name: this.renameName }))}</h2>
          <p class="muted">${esc(this.t("renameDoneText", { n: r.entities.length }))}</p></div>
        <div class="card">${this.renamePlaces(r)}</div>
        <div class="actions"><button class="ghost" data-act="undo" data-id="${r.id}">${this.t("undo")}</button><button class="primary" data-act="home">${this.t("home")}</button></div>`;
    }
    const r = this.renameDry;
    const rows = r ? r.entities.map((c) => `<div class="drow"><ha-icon icon="${DOMAIN_ICON[c.from.split(".")[0]] || "mdi:shape"}"></ha-icon>
        <div class="grow"><div class="dname">${esc(c.name || c.to)}</div><div class="mono muted small">${esc(c.from)} → ${esc(c.to)}</div></div></div>`).join("") : "";
    const places = r ? (r.users || []).length + (r.dashboards || []).length + (r.integrations || []).length + (r.yaml || []).length + (r.energy ? 1 : 0) + (r.esphome || []).length : 0;
    return `
      <div class="card hero"><ha-icon icon="mdi:rename"></ha-icon><div class="grow"><h2>${this.t("renameTitle")}</h2><p class="muted">${this.t("renameText")}</p></div></div>
      <div class="card">
        <div class="muted small">${esc([d?.area, d?.model, d?.integration_title].filter(Boolean).join(" · "))}</div>
        <div class="dname">${esc(d?.name || "")}</div>
        <label class="muted small" for="newName" style="display:block;margin-top:12px">${this.t("newName")}</label>
        <input id="newName" class="name-input" type="text" value="${esc(this.renameName)}" autocomplete="off">
      </div>
      ${r ? `<div class="card">
        <div class="tiles" style="grid-template-columns:repeat(2,1fr)">
          <div class="tile"><div class="num">${r.entities.length}</div><div class="small">${this.t("sumIds")}</div></div>
          <div class="tile"><div class="num">${places}</div><div class="small">${this.t("sumPlaces")}</div></div>
        </div>
        ${r.z2m ? `<div class="dmeta"><span class="chip sm"><ha-icon icon="mdi:zigbee"></ha-icon>${this.t("renameAlsoZ2m")}</span></div>` : ""}
        ${rows ? `<h3 class="dsec"><ha-icon icon="mdi:swap-horizontal"></ha-icon>${this.t("renameEntities")}</h3><div class="drows">${rows}</div>` : `<p class="muted small">${this.t("renameNone")}</p>`}
        ${this.renamePlaces(r)}
      </div>` : ""}
      <div class="actions sticky"><button class="ghost" data-act="home">${this.t("back")}</button>
        <button class="ghost" data-act="renameDry"><ha-icon icon="mdi:test-tube"></ha-icon>${this.t("dryRun")}</button>
        <button class="primary big" data-act="renameDo"><ha-icon icon="mdi:rename"></ha-icon>${this.t("renameDo")}</button></div>`;
  }

  dryView() {
    const code = (this._hass?.language || "en").split("-")[0];
    const press = (l) => esc(pressWords(l, code));
    const icon = (id) => esc(DOMAIN_ICON[String(id).split(".")[0]] || "mdi:shape");
    const usedIn = (list) => !Array.isArray(list) ? "" : list.length
      ? `<div class="dchips"><span class="muted small">${this.t("usedIn")}:</span>${list.map((u) => `<span class="chip sm"><ha-icon icon="${u.startsWith("Dashboard") ? "mdi:view-dashboard" : "mdi:robot"}"></ha-icon>${esc(u.replace(/^Dashboard: /, ""))}</span>`).join("")}</div>`
      : `<div class="muted small">${this.t("notUsed")}</div>`;
    const section = (title, icon, body, extra = "") => body ? `<h3 class="dsec ${extra}"><ha-icon icon="${icon}"></ha-icon>${esc(title)}</h3><div class="drows">${body}</div>` : "";
    const userIcon = (u) => u.startsWith("script") ? "mdi:script-text" : u.startsWith("scene") ? "mdi:palette" : "mdi:robot";
    const device = (d) => {
      const tr = d.triggers || {};
      const changes = tr.changes || [];
      const auto = changes.filter((c) => !c.by_hand);
      const byHand = changes.filter((c) => c.by_hand);
      const open = (tr.unresolved || []).filter((u) => !byHand.some((c) => u.startsWith(`${c.automation} (`)));
      const updated = [
        ...d.users.map((u) => [userIcon(u), u.replace(/^(automation|script|scene): /, "")]),
        ...d.dashboards.map((x) => ["mdi:view-dashboard", x]),
      ];
      const canFix = new Set([...(d.fixable?.files || []).map((f) => f.file), ...(d.fixable?.entries || []).map((e) => e.title)]);
      const handInt = (d.integrations || []).filter((x) => !canFix.has(x));
      const handPkg = (d.packages || []).filter((x) => !canFix.has(x));
      const handOther = [...handInt, ...handPkg];
      const toCheck = open.length + byHand.length + handOther.length;
      const entityRow = (e) => `<div class="drow">
          <ha-icon icon="${icon(e.to)}"></ha-icon>
          <div class="grow"><div class="dname">${esc(e.name || e.to)}</div>
            <div class="mono muted small">${esc(e.from)} → ${esc(e.to)}</div>${usedIn(e.used_in)}</div></div>`;
      const all = d.entities || [];
      const known = all.some((e) => Array.isArray(e.used_in));
      const inUse = known ? all.filter((e) => e.used_in?.length) : all;
      const unused = known ? all.filter((e) => !e.used_in?.length) : [];
      const entities = inUse.map(entityRow).join("") + (unused.length
        ? `<details class="dmore"><summary>${esc(this.t(inUse.length ? "dryMoreUnused" : "dryAllUnused", { n: unused.length }))}</summary><div class="drows">${unused.map(entityRow).join("")}</div></details>`
        : "");
      const dropped = (d.dropped_info || d.dropped.map((x) => ({ entity_id: x }))).map((e) => `<div class="drow gone">
          <ha-icon icon="mdi:delete-outline"></ha-icon>
          <div class="grow"><div class="dname">${esc(e.name || e.entity_id)}</div>
            <div class="mono muted small">${esc(e.entity_id)}</div>${e.used_in ? usedIn(e.used_in) : ""}</div></div>`).join("");
      const ownList = d.own_info || d.own.map((x) => ({ entity_id: x }));
      const own = ownList.map((e) => `<div class="drow new">
          <ha-icon icon="${icon(e.entity_id)}"></ha-icon>
          <div class="grow"><div class="dname">${esc(e.name || e.entity_id)}</div><div class="mono muted small">${esc(e.entity_id)}${e.to ? ` → ${esc(e.to)}` : ""}</div></div></div>`).join("");
      const buttons = auto.map((c) => `<div class="drow">
          <ha-icon icon="mdi:gesture-tap-button"></ha-icon>
          <div class="grow"><div class="dname">${esc(c.automation)}</div>
            <div class="press"><span>${press(c.before)}</span><ha-icon icon="mdi:arrow-right"></ha-icon><span>${press(c.after)}</span></div>
            <div class="mono muted small">${esc(c.before)} → ${esc(c.after)}</div></div></div>`).join("");
      const checks = [
        ...byHand.map((c) => `<div class="drow warnrow"><ha-icon icon="mdi:file-document-edit-outline"></ha-icon>
          <div class="grow"><div class="dname">${esc(c.automation)}</div>
            <div class="press"><span>${press(c.before)}</span><ha-icon icon="mdi:arrow-right"></ha-icon><span>${press(c.after)}</span></div>
            <div class="muted small">${esc(this.t("byHand", { file: c.by_hand }))}</div></div></div>`),
        ...handInt.map((x) => `<div class="drow warnrow"><ha-icon icon="mdi:puzzle"></ha-icon><div class="grow"><div class="dname">${esc(x)}</div><div class="muted small">${esc(this.t("otherIntegrations", { list: x }))}</div></div></div>`),
        ...handPkg.map((x) => `<div class="drow warnrow"><ha-icon icon="mdi:file-document-edit-outline"></ha-icon><div class="grow"><div class="dname">${esc(x)}</div><div class="muted small">${esc(this.t("byHand", { file: x }))}</div></div></div>`),
        ...open.map((u) => {
          const at = u.indexOf(": ");
          const [name, what] = at > 0 ? [u.slice(0, at), u.slice(at + 2)] : [u, ""];
          return `<div class="drow warnrow"><ha-icon icon="mdi:alert"></ha-icon><div class="grow"><div class="dname">${esc(name)}</div>${what ? `<div class="press"><span>${press(what)}</span></div><div class="mono muted small">${esc(what)}</div>` : ""}</div></div>`;
        }),
      ].join("");
      const tile = (n, label, cls = "") => `<div class="tile ${cls}"><div class="num">${n}</div><div class="small">${esc(label)}</div></div>`;
      return `<div class="card">
        <div class="dhead">
          <div class="dpill"><div class="muted small">${this.t("dryNewName")}</div><b>${esc(d.device.from)}</b></div>
          <ha-icon icon="mdi:arrow-right-bold"></ha-icon>
          <div class="dpill main"><div class="muted small">${this.t("dryOldName")}</div><b>${esc(d.device.to)}</b></div>
        </div>
        <div class="dmeta">
          ${d.device.area ? `<span class="chip sm"><ha-icon icon="mdi:sofa"></ha-icon>${esc(d.device.area)}</span>` : ""}
          <span class="chip sm"><ha-icon icon="${d.remove_old ? "mdi:delete-outline" : "mdi:archive-outline"}"></ha-icon>${this.t(d.remove_old && !d.old_name ? "dryRemove" : "dryKeep")}</span>
          ${d.old_name ? `<span class="chip sm"><ha-icon icon="mdi:rename"></ha-icon>${esc(this.t("dryOldMarked", { name: d.old_name }))}</span>` : ""}
          ${d.z2m_name ? `<span class="chip sm"><ha-icon icon="mdi:zigbee"></ha-icon>${esc(this.t("dryZ2m", { name: d.z2m_name }))}</span>` : ""}
        </div>
        <div class="tiles">
          ${tile(d.entities.length, this.t("sumMoved"))}
          ${tile(updated.length, this.t("sumUpdated"))}
          ${tile(auto.length, this.t("sumButtons"))}
          ${tile(toCheck || "✓", toCheck ? this.t("sumCheck") : this.t("dryAllGood"), toCheck ? "amber" : "green")}
        </div>
        ${section(this.t("dryCheck"), "mdi:alert", checks, "warn-text")}
        ${this.fixBlock(d.fixable)}
        ${section(this.t("dryEntities"), "mdi:swap-horizontal", entities)}
        ${section(this.t("dryTriggers"), "mdi:gesture-tap-button", buttons)}
        ${updated.length ? `<h3 class="dsec"><ha-icon icon="mdi:sync"></ha-icon>${this.t("dryUpdated")}</h3><div class="dchips">${updated.map(([i, x]) => `<span class="chip sm"><ha-icon icon="${i}"></ha-icon>${esc(x)}</span>`).join("")}</div>` : ""}
        ${section(this.t("dryDropped"), "mdi:delete-outline", dropped, "red-text")}
        ${section(this.t(ownList.some((e) => e.to) ? "dryOwnRenamed" : "dryOwn"), "mdi:new-box", own)}
      </div>`;
    };
    return `
      <div class="card hero"><ha-icon icon="mdi:test-tube"></ha-icon><div class="grow"><h2>${this.t("dryTitle")}</h2><p class="muted">${this.t("dryIntro")}</p></div></div>
      ${this.aiNote(this.dry.ai_error || this.dry.devices.map((d) => d.triggers?.ai_error).find(Boolean))}
      ${this.dry.devices.map(device).join("")}
      <div class="actions sticky"><button class="primary big" data-act="dryBack">${this.t("dryBack")}</button></div>`;
  }

  deviceCard(d, kind) {
    return `
      <div class="card devcard ${kind}">
        <div class="dev-head"><ha-icon icon="${kind === "old" ? "mdi:devices" : "mdi:new-box"}"></ha-icon>
          <div class="grow"><div class="dev-name">${esc(d.name)}</div><div class="muted small">${esc([d.manufacturer, d.model].filter(Boolean).join(" "))}</div>
          <div class="muted small">${esc(d.integration_title || d.integration || "")}</div></div>
          ${kind === "old" && d.dead ? `<span class="tag red">${this.t("deadTag")}</span>` : ""}
          ${kind === "new" ? `<span class="tag blue">${this.t("tookOver")}</span>` : ""}
        </div>
      </div>`;
  }

  matchView() {
    const p = this.plan;
    const taken = new Set(Object.values(this.mapping).filter(Boolean));
    const rows = p.old_entities.map((o) => {
      const choice = this.mapping[o.entity_id];
      const options = p.new_entities.filter((n) => n.domain === o.domain);
      return `
        <div class="row ${choice ? "ok" : "gone"}">
          <div class="side">
            <ha-icon icon="${this.icon(o)}"></ha-icon>
            <div class="grow"><div class="ename">${esc(o.name || o.entity_id)}${(p.ai || []).includes(o.entity_id) && choice === p.mapping[o.entity_id] ? ` <span class="tag ai">${this.t("aiTag")}</span>` : ""}${(p.unsure || []).includes(o.entity_id) && choice === p.mapping[o.entity_id] ? ` <span class="tag unsure">${this.t("unsureTag")}</span>` : ""}</div><code>${esc(o.entity_id)}</code></div>
          </div>
          <div class="mid"><ha-icon icon="${choice ? "mdi:arrow-left-bold" : "mdi:close"}"></ha-icon></div>
          <div class="side">
            <select data-old="${o.entity_id}">
              <option value="">${this.t("removed")}</option>
              ${options.map((n) => `<option value="${n.entity_id}" ${n.entity_id === choice ? "selected" : ""}>${esc(n.name || n.entity_id)}${n.state && n.state !== "unavailable" ? ` · ${esc(n.state)}${n.unit ? ` ${esc(n.unit)}` : ""}` : ""}</option>`).join("")}
            </select>
          </div>
        </div>`;
    }).join("");
    const own = p.new_entities.filter((n) => !taken.has(n.entity_id));
    return `
      <div class="pair">
        ${this.deviceCard(p.old, "old")}
        <div class="pair-arrow"><ha-icon icon="mdi:arrow-right-thick"></ha-icon></div>
        ${this.deviceCard(p.new, "new")}
      </div>
      <div class="card">
        <h3 class="in">${this.t("matchTitle")}</h3>
        <p class="muted">${this.t("matchText")}</p>
        <div class="rows">${rows}</div>
        ${this.aiNote(p.ai_error)}
        ${!p.ai_enabled && p.old_entities.some((o) => !this.mapping[o.entity_id]) ? `<p class="hint"><ha-icon icon="mdi:robot-outline"></ha-icon><span>${this.t("aiHint")}</span></p>` : ""}
      </div>
      ${own.length ? `<div class="card"><h3 class="in">${this.t("keepsOwn")}</h3><div class="chips">${own.map((n) => `<span class="chip"><ha-icon icon="${this.icon(n)}"></ha-icon>${esc(n.name || n.entity_id)}</span>`).join("")}</div></div>` : ""}
      ${this.checksCard(p.checks)}
      ${p.uses_device.length ? `<div class="card warn"><h3 class="in"><ha-icon icon="mdi:robot"></ha-icon> ${this.t("usesDevice")}</h3><ul>${p.uses_device.map((n) => `<li>${esc(n)}</li>`).join("")}</ul><p class="muted small">${this.t("usesDeviceHint")}</p></div>` : ""}
      <div class="card">
        <label class="switch-row"><input type="checkbox" id="removeOld" ${this.removeOld ? "checked" : ""}><span class="switch"></span>
          <div class="grow"><b>${this.t("removeOld")}</b><div class="muted small">${this.t("removeOldHint")}</div></div></label>
        ${p.new.z2m ? `<label class="switch-row sep"><input type="checkbox" id="renameZ2m" ${this.renameZ2m ? "checked" : ""}><span class="switch"></span>
          <div class="grow"><b>${this.t("renameZ2m")}</b><div class="muted small">${this.t("renameZ2mHint")}</div></div></label>` : ""}
      </div>
      <div class="actions sticky"><button class="ghost" data-act="back">${this.t("back")}</button>
        <button class="ghost" data-act="dryRun"><ha-icon icon="mdi:test-tube"></ha-icon>${this.t("dryRun")}</button>
        <button class="primary big" data-act="replace"><ha-icon icon="mdi:swap-horizontal"></ha-icon>${esc(this.t("replace", { name: p.old.name }))}</button></div>`;
  }

  editView() {
    const p = this.editPlan;
    const dev = this.device(p.device_id) || {};
    const rows = p.slots.map((slot) => {
      const domain = slot.entity_id.split(".")[0];
      const choice = this.editMapping[slot.entity_id];
      return `
        <div class="row ${choice ? "ok" : "gone"}">
          <div class="side"><div class="grow"><div class="ename">${esc(slot.name)}</div><code>${esc(slot.entity_id)}</code></div></div>
          <div class="mid"><ha-icon icon="${choice ? "mdi:arrow-left-bold" : "mdi:close"}"></ha-icon></div>
          <div class="side"><select data-slot="${esc(slot.entity_id)}">
            <option value="">${this.t("noneOption")}</option>
            ${p.choices.filter((c) => c.domain === domain).map((c) => `<option value="${c.uuid}" ${c.uuid === choice ? "selected" : ""}>${esc(c.name)}${c.state && c.state !== "unavailable" ? ` · ${esc(c.state)}${c.unit ? ` ${esc(c.unit)}` : ""}` : ""}</option>`).join("")}
          </select></div>
        </div>`;
    }).join("");
    return `
      <div class="card">
        <h2>${this.t("editTitle")}: ${esc(p.old_name)}</h2>
        <p class="hint"><ha-icon icon="mdi:information-outline"></ha-icon><span>${esc(this.t("editIntro", { integration: dev.integration_title || dev.integration || "" }))}</span></p>
        <div class="rows">${rows}</div>
      </div>
      <div class="card"><button class="ghost full" data-act="recheck"><ha-icon icon="mdi:gesture-tap-button"></ha-icon>${this.t("recheck")}</button>
        ${this.recheckResult ? `<p class="small ${this.recheckResult.unresolved.length ? "warn-text" : "ok-text"}">${esc(this.recheckResult.translated.length || this.recheckResult.unresolved.length ? this.t("recheckDone", { n: this.recheckResult.translated.length, open: this.recheckResult.unresolved.join(", ") || "–" }) : this.t("recheckNone"))}</p>` : ""}</div>
      <div class="card"><button class="ghost full" data-act="tidyCheck"><ha-icon icon="mdi:rename-box"></ha-icon>${this.t("tidy")}</button>
        <p class="muted small">${this.t("tidyHint")}</p>
        ${this.tidyResult ? (this.tidyResult.done
          ? `<p class="small ok-text">${esc(this.t("tidyDone", { n: this.tidyResult.changes.length }))}</p>`
          : this.tidyResult.changes.length
            ? `<div class="drows">${this.tidyResult.changes.map((c) => `<div class="drow new"><ha-icon icon="mdi:rename"></ha-icon><div class="grow"><div class="dname">${esc(c.name || c.to)}</div><div class="mono muted small">${esc(c.from)} → ${esc(c.to)}</div></div></div>`).join("")}</div>
               <div class="actions"><button class="primary" data-act="tidyApply">${esc(this.t("tidyApply", { n: this.tidyResult.changes.length }))}</button></div>`
            : `<p class="small ok-text">${this.t("tidyNone")}</p>`) : ""}
      </div>
      <div class="actions"><button class="ghost" data-act="home">${this.t("back")}</button><button class="primary big" data-act="saveEdit">${this.t("save")}</button></div>
      ${this.confirmGiveBack ? `
        <div class="card warn give-back"><p>${this.t("giveBackWarn")}</p>
          <div class="actions"><button class="ghost" data-act="cancelGiveBack">${this.t("cancel")}</button><button class="danger" data-act="giveBack">${this.t("giveBackYes")}</button></div></div>`
      : `<p class="center-link"><button class="link" data-act="askGiveBack">${this.t("giveBack")}</button></p>`}`;
  }

  async openEdit(id) {
    try {
      this.editPlan = await this.ws("edit_plan", { record: id });
      this.editMapping = Object.fromEntries(this.editPlan.slots.map((slot) => [slot.entity_id, slot.holder]));
      this.confirmGiveBack = false;
      this.recheckResult = null;
      this.tidyResult = null;
      this.view = "edit";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async tidy(apply) {
    try {
      const r = await this.ws("tidy", { record: this.editPlan.id, apply });
      this.tidyResult = { changes: r.changes, done: apply };
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async recheck() {
    try {
      this.recheckResult = await this.ws("retranslate", { record: this.editPlan.id });
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async saveEdit() {
    const picked = Object.values(this.editMapping).filter(Boolean);
    if (picked.length !== new Set(picked).size) {
      this.error = this.t("duplicate");
      return this.render();
    }
    try {
      await this.ws("edit", { record: this.editPlan.id, mapping: this.editMapping });
      this.view = "home";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.load();
  }

  workingView() {
    if (this.renaming) return `<div class="card center"><div class="spinner"></div><h2>${this.t(this.renaming === "dry" ? "dryWorking" : "renameWorking")}</h2></div>`;
    if (this.planning) return `<div class="card center"><div class="spinner"></div><h2>${this.t("planning")}</h2><p class="muted small">${this.t("planningHint")}</p></div>`;
    return `<div class="card center"><div class="spinner"></div><h2>${this.t(this.testing ? "dryWorking" : "working")}</h2></div>`;
  }

  doneView() {
    const r = this.result;
    return `
      <div class="card center done">
        <div class="check"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
        <h2>${esc(this.t("doneTitle", { name: r.name }))}</h2>
        <p class="muted">${this.t("doneText", { n: r.moved })}</p>
        ${this.removeOld && !r.removed ? `<p class="warn-text">${this.t("keptOld")}</p>` : ""}
        ${r.failed?.length ? `<p class="warn-text">${esc(this.t("notMoved", { list: r.failed.join(", ") }))}</p>` : ""}
        ${r.triggers?.translated?.length ? `<p class="ok-text">${this.t("triggersDone", { n: r.triggers.translated.length })}</p>` : ""}
        ${this.aiNote(r.ai_error || r.triggers?.ai_error)}
        ${r.triggers?.translated?.length || r.translated ? `<p class="hint left-hint"><ha-icon icon="mdi:gesture-tap-button"></ha-icon><span>${this.t("pressOnce")}</span></p>` : ""}
        ${r.integrations?.length ? `<p class="warn-text">${esc(this.t("otherIntegrations", { list: r.integrations.join(", ") }))}</p>` : ""}
        ${r.packages?.length ? `<p class="warn-text">${esc(this.t("packagesByHand", { list: r.packages.join(", ") }))}</p>` : ""}
        ${this.fixResult(r.fixed)}
        ${r.dashboards?.length ? `<p class="ok-text">${esc(this.t("dashboardsUpdated", { list: r.dashboards.join(", ") }))}</p>` : ""}
        ${(r.triggers?.unresolved || r.unresolved || []).length ? `<div class="card warn left"><b>${this.t("triggersOpen")}</b><ul>${(r.triggers?.unresolved || r.unresolved).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}

        <div class="actions"><button class="ghost" data-act="edit" data-id="${r.id}">${this.t("edit")}</button><button class="primary" data-act="home">${this.t("home")}</button></div>
      </div>`;
  }

  render() {
    if (!this._hass) return;
    const body = {
      home: () => this.homeView(), pick: () => this.pickView(), match: () => this.matchView(), working: () => this.workingView(),
      done: () => this.doneView(), migrate: () => this.migrateView(), migrated: () => this.migrateDoneView(),
      edit: () => this.editView(), dry: () => this.dryView(), rename: () => this.renameView(),
    }[this.view]();
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      <div class="toolbar">${customElements.get("ha-menu-button") ? "<ha-menu-button></ha-menu-button>" : ""}${this.view !== "home" && this.view !== "working" ? `<button class="tb-back" data-act="topBack" title="${this.t("back")}" aria-label="${this.t("back")}"><ha-icon icon="mdi:arrow-left"></ha-icon></button>` : ""}<div class="tb-title">${this.t("title")}</div></div>
      <div class="content">${this.error ? `<div class="card error"><ha-icon icon="mdi:alert-circle"></ha-icon>${esc(this.error)}</div>` : ""}${body}</div>`;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) {
      menu.hass = this._hass;
      menu.narrow = this._narrow;
    }
    this.shadowRoot.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset)));
    this.shadowRoot.querySelectorAll("select[data-old]").forEach((el) =>
      el.addEventListener("change", () => {
        this.mapping[el.dataset.old] = el.value || null;
        this.error = "";
        this.render();
      }));
    const remove = this.shadowRoot.getElementById("removeOld");
    if (remove) remove.addEventListener("change", () => (this.removeOld = remove.checked));
    const newName = this.shadowRoot.getElementById("newName");
    if (newName) newName.addEventListener("input", () => (this.renameName = newName.value));
    const rename = this.shadowRoot.getElementById("renameZ2m");
    if (rename) rename.addEventListener("change", () => (this.renameZ2m = rename.checked));
    const q = this.shadowRoot.getElementById("q");
    if (q) {
      q.addEventListener("input", () => {
        this.query = q.value;
        this.renderList();
      });
    }
    const src = this.shadowRoot.getElementById("src");
    if (src) {
      src.addEventListener("change", () => {
        this.srcFilter = src.value;
        this.renderList();
      });
    }
    const msrc = this.shadowRoot.getElementById("msrc");
    if (msrc) {
      msrc.addEventListener("change", () => {
        this.migrateSource = msrc.value;
        this.migratePlan = null;
        this.render();
      });
    }
    const mdst = this.shadowRoot.getElementById("mdst");
    if (mdst) {
      mdst.addEventListener("change", () => {
        this.migrateTarget = mdst.value;
        this.migratePlan = null;
        this.render();
      });
    }
    this.shadowRoot.querySelectorAll("select[data-slot]").forEach((el) =>
      el.addEventListener("change", () => {
        this.editMapping[el.dataset.slot] = el.value || null;
        this.error = "";
        this.render();
      }));
    this.shadowRoot.querySelectorAll("input[data-group]").forEach((el) =>
      el.addEventListener("change", () => {
        if (el.checked) this.groupSelected.add(el.dataset.group);
        else this.groupSelected.delete(el.dataset.group);
        this.render();
      }));
    this.shadowRoot.querySelectorAll("input[data-fix]").forEach((el) =>
      el.addEventListener("change", () => {
        const set = this.picked[el.dataset.fix];
        if (el.checked) set.add(el.dataset.fixid);
        else set.delete(el.dataset.fixid);
      }));
    this.shadowRoot.querySelectorAll("input[data-pair]").forEach((el) =>
      el.addEventListener("change", () => {
        if (el.checked) this.migrateSelected.add(el.dataset.pair);
        else this.migrateSelected.delete(el.dataset.pair);
        this.render();
      }));
  }

  renderList() {
    const list = this.shadowRoot.getElementById("list");
    list.innerHTML = this.pickList();
    list.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset)));
  }

  act(data) {
    this.error = "";
    if (data.act === "topBack") {
      // The same as the back button at the bottom of each page, so nobody has to scroll down for it.
      if (this.view === "pick" && this.oldId && this.pickMode !== "rename") data = { act: "changeOld" };
      else if (this.view === "match") data = { act: "back" };
      else if (this.view === "dry") data = { act: "dryBack" };
      else data = { act: "home" };
    }
    if (data.act === "home") {
      this.view = "home";
      this.oldId = this.newId = "";
      this.load();
    } else if (data.act === "pick") {
      this.pickMode = "";
      this.oldId = data.old || "";
      this.newId = "";
      this.query = "";
      this.view = "pick";
      this.render();
    } else if (data.act === "choose" && this.pickMode === "rename") {
      this.renameId = data.id;
      this.renameName = this.device(data.id)?.name || "";
      this.renameDry = null;
      this.renameResult = null;
      this.view = "rename";
      this.render();
    } else if (data.act === "markDone") {
      this.ws("mark_done", { record: data.id }).then(() => this.load());
    } else if (data.act === "renameStart") {
      this.pickMode = "rename";
      this.oldId = "";
      this.query = "";
      this.view = "pick";
      this.render();
    } else if (data.act === "renameDry" || data.act === "renameDo") {
      this.doRename(data.act === "renameDo");
    } else if (data.act === "choose") {
      if (!this.oldId) {
        this.oldId = data.id;
        this.query = "";
        this.render();
      } else {
        this.openPlan(this.oldId, data.id);
      }
    } else if (data.act === "changeOld") {
      this.oldId = "";
      this.render();
    } else if (data.act === "back") {
      this.view = "pick";
      this.render();
    } else if (data.act === "migrate") {
      // Start with the source that has the most devices to move somewhere.
      const best = this.migrateSources().find((x) => this.migrateTargets(x.key).length);
      this.migrateSource ||= best?.key || this.migrateSources()[0]?.key || "";
      this.view = "migrate";
      this.render();
    } else if (data.act === "findPairs") {
      this.findPairs();
    } else if (data.act === "selectAll" || data.act === "selectNone") {
      this.migrateSelected = new Set(data.act === "selectAll" ? this.migratePlan.pairs.map((p) => p.old.id) : []);
      this.render();
    } else if (data.act === "doMigrate") {
      this.doMigrate();
    } else if (data.act === "plan") {
      this.openPlan(data.old, data.new);
    } else if (data.act === "replace") {
      this.doReplace();
    } else if (data.act === "dryRun") {
      this.dryRun();
    } else if (data.act === "dryMigrate") {
      this.dryMigrate();
    } else if (data.act === "dryBack") {
      this.view = this.dryFrom;
      this.render();
    } else if (data.act === "undo") {
      this.undo(data.id);
    } else if (data.act === "undoBatch") {
      this.undo(null, data.batch);
    } else if (data.act === "hide" || data.act === "unhide") {
      this.ws("hide", { device: data.id, hidden: data.act === "hide" }).then(() => this.load());
    } else if (data.act === "toggleHidden") {
      this.showHidden = !this.showHidden;
      this.render();
    } else if (data.act === "removeLeftover") {
      this.removeLeftover(data.id, data.integration);
    } else if (data.act === "edit") {
      this.openEdit(data.id);
    } else if (data.act === "recheck") {
      this.recheck();
    } else if (data.act === "tidyCheck" || data.act === "tidyApply") {
      this.tidy(data.act === "tidyApply");
    } else if (data.act === "saveEdit") {
      this.saveEdit();
    } else if (data.act === "askGiveBack" || data.act === "cancelGiveBack") {
      this.confirmGiveBack = data.act === "askGiveBack";
      this.render();
    } else if (data.act === "giveBack") {
      this.undo(this.editPlan.id);
    } else if (data.act === "redo" || data.act === "redoBatch") {
      this.redo(data.id, data.batch);
    }
  }
}

const STYLE = `
:host{display:block;min-height:100vh;background:var(--primary-background-color,#f3f5f8);color:var(--primary-text-color,#1c2430);font-family:var(--paper-font-body1_-_font-family,Roboto,"Noto Sans",sans-serif);
  --rd-red:var(--error-color,#db4437);--rd-green:var(--success-color,#43a047);--rd-blue:var(--primary-color,#03a9f4);--rd-amber:var(--warning-color,#ffa600)}
*{box-sizing:border-box}
.toolbar{display:flex;align-items:center;height:56px;padding:0 12px;background:var(--app-header-background-color,var(--primary-color,#03a9f4));color:var(--app-header-text-color,#fff);position:sticky;top:0;z-index:2}
.tb-title{font-size:20px;margin-left:8px}.tb-back{background:none;border:0;color:inherit;padding:8px;margin-left:-4px;border-radius:50%;cursor:pointer;display:flex}.tb-back:hover{background:rgba(255,255,255,.15)}.tb-back ha-icon{--mdc-icon-size:24px}.beta{margin-left:10px;font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;padding:2px 8px;border-radius:99px;background:rgba(255,255,255,.22)}
.content{max-width:960px;margin:0 auto;padding:16px 16px 96px}
.card{background:var(--card-background-color,#fff);border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,0 1px 4px rgba(0,0,0,.1));border:1px solid var(--divider-color,transparent);padding:16px;margin-bottom:16px}
h2{margin:0 0 6px;font-size:22px}h3{margin:24px 4px 10px;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}h3.in{margin:0 0 6px}
p{margin:4px 0 12px;line-height:1.45}.muted{color:var(--secondary-text-color,#6b7686)}.small{font-size:13px}.grow{flex:1;min-width:0}
code{font-family:var(--code-font-family,monospace);font-size:12px;color:var(--secondary-text-color);word-break:break-all}
button{font:inherit;font-weight:500;border-radius:10px;padding:10px 18px;cursor:pointer;border:1px solid transparent;display:inline-flex;align-items:center;justify-content:center;gap:8px}
button.primary{background:var(--rd-blue);color:var(--text-primary-color,#fff)}button.primary:hover{filter:brightness(1.08)}
button.ghost{background:transparent;color:var(--rd-blue);border-color:var(--divider-color,#d0d7e0)}
button.full{width:100%;margin-top:12px}button.big{padding:13px 22px;font-size:16px}button.small-btn{padding:6px 12px;font-size:13px}
.hero{display:flex;gap:16px;align-items:flex-start;background:linear-gradient(135deg,rgba(3,169,244,.10),transparent 60%),var(--card-background-color,#fff)}
.hero-icon ha-icon{--mdc-icon-size:48px;color:var(--rd-blue)}
.count{background:var(--rd-red);color:#fff;border-radius:99px;font-size:12px;padding:1px 8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}.grid .card{margin:0}
.dev-head{display:flex;gap:12px;align-items:flex-start}.dev-name{font-weight:600;font-size:16px}
.dot{width:12px;height:12px;border-radius:50%;margin-top:5px;flex:none}.dot.red{background:var(--rd-red);box-shadow:0 0 0 4px rgba(219,68,55,.15)}
.twin{display:flex;gap:10px;align-items:center;margin-top:12px;padding:10px 12px;border-radius:10px;background:rgba(67,160,71,.10)}.twin ha-icon{color:var(--rd-green)}
.empty{display:flex;gap:10px;align-items:center;color:var(--secondary-text-color)}.empty ha-icon{color:var(--rd-green)}
.list{padding:4px 16px}.hist{display:flex;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--divider-color,#e6e9ee)}.hist:last-child{border:0}
.tag{font-size:12px;padding:3px 10px;border-radius:99px;background:var(--secondary-background-color,#eef1f5);white-space:nowrap}
.tag.red{background:rgba(219,68,55,.14);color:var(--rd-red)}.tag.blue{background:rgba(3,169,244,.14);color:var(--rd-blue)}
.pick label{display:block;font-size:13px;color:var(--secondary-text-color);margin:16px 0 6px}
select{width:100%;font:inherit;padding:10px 12px;border-radius:10px;border:1px solid var(--divider-color,#d0d7e0);background:var(--card-background-color,#fff);color:var(--primary-text-color)}
.arrow-down{text-align:center;margin-top:12px;color:var(--secondary-text-color)}
.actions{display:flex;gap:12px;justify-content:flex-end;margin-top:20px;flex-wrap:wrap}
.actions.sticky{position:sticky;bottom:0;padding:12px 0;background:linear-gradient(transparent,var(--primary-background-color,#f3f5f8) 30%)}
.pair{display:flex;gap:12px;align-items:stretch}.pair .card{flex:1;margin-bottom:16px}
.pair-arrow{align-self:center;color:var(--rd-blue);margin-bottom:16px}.pair-arrow ha-icon{--mdc-icon-size:32px}
.devcard.old{opacity:.75}.devcard.new{border:2px solid var(--rd-blue)}
.rows{display:flex;flex-direction:column;gap:8px}
.row{display:grid;grid-template-columns:1fr 36px 1fr;align-items:center;gap:8px;padding:10px;border-radius:10px;border-left:4px solid var(--rd-green);background:var(--secondary-background-color,#f6f8fa)}
.row.gone{border-left-color:var(--rd-red)}.row.gone .side:first-child .ename{text-decoration:line-through;opacity:.7}
.side{display:flex;gap:10px;align-items:center;min-width:0}.side ha-icon{color:var(--secondary-text-color);flex:none}
.mid{text-align:center;color:var(--rd-green)}.row.gone .mid{color:var(--rd-red)}
.ename{font-weight:500;overflow:hidden;text-overflow:ellipsis}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.chip{display:inline-flex;gap:6px;align-items:center;padding:6px 12px;border-radius:99px;background:var(--secondary-background-color,#eef1f5);font-size:13px}.chip ha-icon{--mdc-icon-size:16px}
.warn{border-left:4px solid var(--rd-amber)}.warn ul{margin:6px 0;padding-left:20px}
.error{display:flex;gap:10px;align-items:center;border-left:4px solid var(--rd-red);color:var(--rd-red)}
.switch-row{display:flex;gap:14px;align-items:center;cursor:pointer}.switch-row input{display:none}
.switch{width:44px;height:24px;border-radius:12px;background:var(--divider-color,#c4cbd4);position:relative;flex:none;transition:.2s}
.switch:after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.2s}
input:checked+.switch{background:var(--rd-blue)}input:checked+.switch:after{left:23px}
.center{text-align:center;padding:40px 20px}.center .actions{justify-content:center}
.spinner{width:48px;height:48px;margin:0 auto 16px;border-radius:50%;border:4px solid var(--divider-color,#e0e0e0);border-top-color:var(--rd-blue);animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.check svg{width:84px;height:84px;margin-bottom:12px;animation:pop .5s cubic-bezier(.3,1.6,.6,1)}
.check circle{fill:rgba(67,160,71,.12);stroke:var(--rd-green);stroke-width:3}
.check path{fill:none;stroke:var(--rd-green);stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
@keyframes pop{from{transform:scale(.5)}}
.warn-text{color:var(--rd-amber)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:14px 0 4px}.tile{padding:10px 6px;border-radius:12px;background:var(--secondary-background-color,#f6f8fa);text-align:center}.tile .num{font-size:24px;font-weight:600;line-height:1.2}.tile.amber{background:rgba(255,166,0,.16);color:#b36b00}.tile.green{background:rgba(67,160,71,.14);color:var(--rd-green)}
@media (max-width:520px){.tiles{grid-template-columns:repeat(2,1fr)}}
.dhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.dhead>ha-icon{color:var(--rd-blue);flex:none}.dpill{flex:1;min-width:120px;padding:10px 12px;border-radius:12px;background:var(--secondary-background-color,#f6f8fa)}.dpill.main{background:rgba(3,169,244,.12)}.dpill b{display:block;overflow-wrap:anywhere}
.dmeta{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.dsec{display:flex;align-items:center;gap:8px;font-size:15px;margin:18px 0 8px}.dsec ha-icon{--mdc-icon-size:20px}.red-text{color:var(--rd-red)}
.drows{display:flex;flex-direction:column;gap:6px}.drow{display:flex;gap:10px;align-items:flex-start;padding:10px;border-radius:10px;background:var(--secondary-background-color,#f6f8fa);border-left:4px solid var(--rd-green)}.drow>ha-icon{flex:none;--mdc-icon-size:20px;margin-top:1px;color:var(--secondary-text-color)}
.drow.gone{border-left-color:var(--rd-red)}.drow.new{border-left-color:var(--rd-blue)}.drow.warnrow{border-left-color:var(--rd-amber)}.drow.warnrow>ha-icon{color:var(--rd-amber)}
.name-input{width:100%;box-sizing:border-box;margin-top:4px;padding:12px;border-radius:10px;border:1px solid var(--divider-color,#d0d7e0);background:var(--card-background-color,#fff);color:var(--primary-text-color);font-size:16px}
.count.amber{background:var(--rd-amber)}.hist-done summary{display:flex;align-items:center;gap:8px;margin:16px 0 8px}.hist-done summary ha-icon{color:var(--rd-green);--mdc-icon-size:18px}.link.small{font-size:13px;padding:2px 0}
.dmore{margin-top:6px}.dmore summary{cursor:pointer;padding:10px;border-radius:10px;background:var(--secondary-background-color,#f6f8fa);color:var(--rd-blue);font-size:14px;list-style:none}.dmore summary::-webkit-details-marker{display:none}.dmore[open] summary{margin-bottom:6px}
.dname{font-weight:500;overflow-wrap:anywhere}.mono{font-family:var(--code-font-family,monospace);font-size:12px;overflow-wrap:anywhere}
.dchips{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px}.chip.sm{padding:3px 10px;font-size:12px}.chip.sm ha-icon{--mdc-icon-size:14px}
.press{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:2px 0}.press span{padding:2px 8px;border-radius:8px;background:var(--card-background-color,#fff);font-size:13px}.press ha-icon{--mdc-icon-size:16px;color:var(--rd-blue)}
.tag.unsure{background:rgba(255,166,0,.18);color:#b36b00;font-size:11px;padding:1px 7px}
.left-hint{text-align:left}
.leftover{border-left:4px solid var(--rd-amber)}.leftover .dev-head>ha-icon{color:var(--rd-amber)}
.why{display:flex;gap:8px;align-items:center;margin-top:10px;font-size:14px;color:var(--secondary-text-color)}.why ha-icon{--mdc-icon-size:18px}.why.low{color:var(--rd-amber);font-weight:500}
.card-links{display:flex;justify-content:space-between;gap:8px;margin-top:8px}.dot.grey{background:var(--disabled-text-color,#9aa3ad);box-shadow:none}.is-hidden{opacity:.7}.section-hint{margin:-4px 4px 12px}
.batch-items{padding-left:22px;border-left:2px solid var(--divider-color,#e3e7ec);margin:0 0 6px 10px}.batch-head{border-bottom:0}
button.link{background:none;border:0;color:var(--secondary-text-color);text-decoration:underline;font-size:13px;padding:6px}.center-link{text-align:center;margin-top:18px}
button.danger{background:var(--rd-red);color:#fff}.give-back{margin-top:16px}
.checks{display:flex;flex-direction:column;gap:8px;margin-top:8px}.check-line{display:flex;gap:10px;align-items:flex-start;font-size:14px;line-height:1.4}.check-line ha-icon{flex:none;--mdc-icon-size:18px}.check-line.c-warn ha-icon{color:var(--rd-amber)}.check-line.c-bad ha-icon{color:var(--rd-red)}.check-line.c-info ha-icon{color:var(--rd-blue)}.card .card.warn{box-shadow:none;margin:8px 0 0;padding:10px}
.ok-text{color:var(--rd-green)}.tag.ai{background:rgba(156,39,176,.14);color:#8e24aa;font-size:11px;padding:1px 7px}.card.left{text-align:left;margin-top:12px}
.btns{display:flex;gap:10px;flex-wrap:wrap}
.hint{display:flex;gap:10px;align-items:flex-start;margin:14px 0 0;padding:12px;border-radius:10px;background:rgba(3,169,244,.08)}.hint ha-icon{color:var(--rd-blue);flex:none}
.chosen{border-left:4px solid var(--rd-red)}
.filters{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap}.filters select{width:auto;flex:0 1 220px}
.search{flex:1 1 240px;display:flex;align-items:center;gap:8px;padding:0 12px;border-radius:10px;border:1px solid var(--divider-color,#d0d7e0);background:var(--card-background-color,#fff)}
.search ha-icon{color:var(--secondary-text-color)}.search input{flex:1;border:0;outline:0;background:transparent;font:inherit;color:var(--primary-text-color);padding:11px 0;min-width:0}
.pick-list{display:flex;flex-direction:column;gap:8px}
.devpick{width:100%;text-align:left;display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#e3e7ec);color:var(--primary-text-color);font-weight:400}
.devpick:hover{border-color:var(--rd-blue)}.devpick .grow{display:flex;flex-direction:column;gap:2px}.devpick>ha-icon{color:var(--secondary-text-color)}
.devpick .dot{margin-top:0}.dot.green{background:var(--rd-green)}
.tags{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}.tag.green{background:rgba(67,160,71,.14);color:var(--rd-green)}
.fromto{display:flex;align-items:flex-end;gap:12px}.fromto>div{flex:1}.fromto>ha-icon{margin-bottom:12px;color:var(--rd-blue)}
.fromto label{display:block;font-size:13px;color:var(--secondary-text-color);margin-bottom:6px}
.mhead{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}.mhead>span{display:flex;gap:6px;flex:none}
.mrows{display:flex;flex-direction:column}
.mrow{display:flex;align-items:center;gap:12px;padding:10px 4px;border-bottom:1px solid var(--divider-color,#eceff3);cursor:pointer}.mrow:last-child{border:0}
.fixrow{align-items:flex-start}.fixrow .box{margin-top:2px}.fixline{margin-top:6px;overflow-wrap:anywhere;word-break:break-word}
.mrow input{display:none}.mrow .grow{display:flex;flex-direction:column;gap:2px}
.box{width:22px;height:22px;border-radius:6px;border:2px solid var(--divider-color,#b8c0ca);flex:none;position:relative}
input:checked+.box{background:var(--rd-blue);border-color:var(--rd-blue)}input:checked+.box:after{content:"";position:absolute;left:6px;top:2px;width:6px;height:11px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
.switch-row.sep{margin-top:14px;padding-top:14px;border-top:1px solid var(--divider-color,#eceff3)}
button[disabled]{opacity:.45;cursor:default}
@media (max-width:600px){
  .content{padding:12px 12px 96px}.hero{flex-direction:column}.pair{flex-direction:column;gap:0}.pair-arrow{transform:rotate(90deg);margin:-8px auto 8px}
  .row{grid-template-columns:1fr;gap:6px}.mid{display:none}.actions.sticky button{flex:1}
  .fromto{flex-direction:column;align-items:stretch;gap:4px}.fromto>ha-icon{transform:rotate(90deg);align-self:center;margin:4px 0 0}
  .filters select{flex:1 1 100%}.devpick .tags{display:none}.devpick .tags:has(.green){display:flex}
}
`;

customElements.define("replace-device-panel", ReplaceDevicePanel);
