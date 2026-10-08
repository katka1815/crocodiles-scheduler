# Prague Crocodiles – rozvrh služeb

Nástroj, který pro ligový den rozdělí pískání a podávání mezi hráče Prague
Crocodiles: vezme rozpis z Tournify a docházku ze Spondu a ke každému zápasu
přiřadí rozhodčí a podávající tak, aby nikdo nebyl na dvou místech najednou a
aby měli všichni zhruba stejně služeb.

Stav popsaný v tomhle dokumentu platí od října 2026. Co se tehdy opravovalo a
proč, je v kapitole [Co nefungovalo dřív](#co-nefungovalo-dřív).

## Z čeho se to skládá

| Část | Kde je | K čemu je |
|---|---|---|
| Server | tenhle repozitář, `server.py`, běží na Fly.io | Stahuje Tournify a Spond, počítá rozvrh, pamatuje si poslední rozvrh |
| Mobilní appka | repozitář `crocodiles-mobile` (Expo / React Native, Android) | Tady se rozvrh připravuje: týmy, docházka, preference, generování, výměny |
| Veřejná stránka | `frontend.html`, servíruje ji server | Jen pro čtení, pro spoluhráče: https://crocodiles-scheduler.fly.dev |

Rozvrh se vždy **počítá na serveru**. Appka je ovladač: pošle serveru týmy,
docházku, vocasy a preference a zobrazí výsledek. Veřejná stránka ukazuje
poslední vygenerovaný rozvrh a sama se každých 30 vteřin obnovuje.

## Jak se to používá (appka)

1. **Složení týmů.** Kdo je v jakém týmu (Mix A, Mix B, Muži, Ženy). Hráč může
   být ve více týmech. Každá změna se hned uloží do telefonu. V nabídce jsou
   všichni členové Spond skupiny, nové jméno jde i napsat ručně (musí být
   stejně jako ve Spondu, jinak se nespáruje s docházkou).
2. **Tournify + Spond.** Zadá se Tournify „live link" (letos `cdbl2627`),
   načte se rozpis a vybere se Spond event. Appka ukáže, kdo jde, kdo ne a kdo
   neodpověděl; neodpovězené jde zaškrtnout ručně. Herní den se vybere sám,
   pokud na event sedí, jinak se vybírá ručně. Spond jde i přeskočit, pak se
   počítá se všemi členy.
3. **Vocasové a preference.** Vocas = někdo, kdo má službu přednostně.
   Preference = kdo radši píská a kdo radši podává. Preference se ukládají.
4. **Výsledky.** Rozvrh s filtry, přehled po hráčích, přehled spravedlnosti,
   výměna hráče za volného a sdílení obrázku.

## Pravidla přiřazování

- **Hraní** je dané rozpisem. Kdo je v hrajícím týmu, nemůže v tom čase dělat
  nic jiného, a to ani na jiném kurtu.
- **Pískání** je taky z rozpisu: když Tournify určí jako rozhodčí náš tým,
  vyberou se z něj 4 lidi.
- **Podávání** se řídí hrajícím týmem, vybírají se 3 lidi:
  - hraje A MIX → podává Mix B
  - hraje B MIX → podává Mix A
  - hrají Muži → podávají Ženy
  - hrají Ženy → podávají Muži
- Nikdo nemá dvě služby ve stejný čas.
- Když je jeden tým ve stejnou hodinu rozhodčí i podávající, vyberou se nejdřív
  4 rozhodčí a podávající ze zbytku.

## Jak se rozvrh počítá

Výpočet je ve funkci `assign_duties` v `server.py` a má tři fáze.

1. **První rozdělení.** Zápasy se projdou v čase a na každou službu se vezmou
   ti, kdo jsou volní a mají zatím nejméně služeb (vocasové mají přednost,
   při shodě rozhoduje preference). Ještě před tím se všem hrajícím zablokují
   časy jejich zápasů pro celý den.
2. **Dorovnání.** První rozdělení je krátkozraké: neví, že někdo později skoro
   nebude volný. Proto se potom hledají řetězy předání: služba se přesune od
   nejvytíženějšího k někomu, kdo má aspoň o dvě méně, případně přes
   prostředníky (A předá B, B jinou službu předá C). Opakuje se, dokud to jde.
   Cíl je, aby rozdíl mezi nejvíc a nejmíň vytíženým byl nejvýš 1.
3. **Preference.** Nakonec se zkouší výměny, které zlepší splnění preferencí a
   přitom nezmění rozložení služeb: dva lidé si prohodí služby, nebo službu
   převezme někdo, kdo má přesně o jednu méně. Preference je tedy měkká: kdo
   radši píská, dostane přednostně pískání, ale když vychází místo jen na
   podávání, podává.

Vocasové si svou přednost drží a do dorovnávání se nezapočítávají.

**Proč rozdíl někdy vyjde větší než 1:** služby se berou jen z týmu, který
podle rozpisu píská nebo podává. Když něčí tým v daný den nepíská ani
nepodává, nedostane ten člověk nic, a to se dorovnat nedá.

## Kde jsou která data

| Co | Kde | Poznámka |
|---|---|---|
| Složení týmů | telefon (`custom_teams`) | Přežije aktualizaci appky, ne odinstalování |
| Známí hráči | telefon (`known_players`) | Plní se ze Spondu |
| Poslední Tournify odkaz | telefon (`tournify_link`) | |
| Preference | telefon (`saved_preferences`) | |
| Poslední rozvrh v appce | telefon (`saved_schedule`) | |
| Poslední rozvrh pro web | server, soubor `/data/schedule.json` | Přežije restart serveru |
| Načtený rozpis, docházka | paměť serveru | Po restartu serveru se ztratí, appka je pošle znovu |
| Přihlášení do Spondu | Fly.io secrets | `SPOND_USERNAME`, `SPOND_PASSWORD`, volitelně `SPOND_GROUP_ID` |

Týmy zapsané v `server.py` (`MEMBERS_BY_TEAM`) jsou jen výchozí hodnota pro
případ, že by appka žádné neposlala. Platí vždy to, co pošle appka.

## Nová sezóna a jiné změny

- **Nový rozpis:** v appce na druhé stránce zadej nový Tournify odkaz. Appka si
  ho zapamatuje. Nic v kódu se měnit nemusí.
- **Nový hráč:** objeví se v nabídce sám, jakmile je ve Spond skupině. Stačí ho
  na první stránce přidat do týmů.
- **Tým se v Tournify jmenuje jinak nebo přibyl nový:** tohle je jediná věc,
  která chce úpravu kódu. Názvy se párují na dvou místech:
  - `server.py`: `TOURNIFY_TO_SUBGROUP` (název v Tournify → náš tým) a
    `PLAYING_SERVED_BY` (kdo komu podává),
  - appka, `app/index.tsx`: `tournifyToTeamKey`, `DEFAULT_TEAMS`, `TEAM_COLORS`.

## Nasazení

**Server:** push do větve `main` spustí GitHub Action (`.github/workflows/fly-deploy.yml`),
která nasadí na Fly.io. Trvá to pár minut.

**Appka:** v repozitáři `crocodiles-mobile`:

```
npx eas-cli build --platform android --profile preview
```

Výsledkem je odkaz na APK, který se nainstaluje přes stávající appku. Na free
tarifu EAS může build čekat ve frontě i přes hodinu.

**Lokální spuštění serveru:**

```
pip install -r requirements.txt
python server.py
```

Server poběží na http://localhost:8765. Bez proměnných `SPOND_USERNAME` a
`SPOND_PASSWORD` funguje všechno kromě Spondu.

## API serveru

Všechno kromě prvních tří řádků je `POST` s JSON tělem.

| Cesta | Co dělá |
|---|---|
| `GET /` | Veřejná stránka s rozvrhem |
| `GET /api/assignments` | Poslední rozvrh |
| `GET /api/status` | Stav serveru (počet načtených zápasů, docházka) |
| `/api/load_tournify` | Načte rozpis podle `live_link` |
| `/api/spond_events` | Nadcházející Spond eventy |
| `/api/spond_attendance` | Docházka na event: jdou, nejdou, neodpověděli |
| `/api/spond_members` | Všichni členové Spond skupiny |
| `/api/set_teams` | Složení týmů z appky |
| `/api/set_attending` | Kdo je přítomen a který den se počítá |
| `/api/set_vocas` | Vocasové |
| `/api/set_preferences` | Preference rozhodčí / podávající |
| `/api/assign` | Spočítá rozvrh a uloží ho |
| `/api/replace_player` | Vymění jednoho člověka ve službě |

## Co nefungovalo dřív

Opravy z října 2026, od příznaku k příčině.

**1. Hráč nešel přidat do týmu.**
Jakub Kopáč se nenabízel pro Mix B. Výběr totiž po načtení Spond eventu
nabízel jen lidi, kteří na ten event potvrdili účast.
*Teď:* nabízí se všichni známí hráči (týmy + celá Spond skupina) a jméno jde
napsat i ručně.

**2. Hrající dostali podávání.**
Týmy upravené v appce se ukládaly jen do telefonu. Server, který rozvrh počítá,
je nikdy nedostal a jel podle svých výchozích týmů. Kdo byl v appce přesunutý
do jiného mixu, byl pro server pořád v tom původním, a mohl tak dostat službu
v čase, kdy hraje.
*Teď:* appka před každým generováním pošle týmy serveru (`/api/set_teams`).

**3. Načítal se loňský rozvrh (neděle 17. 5.).**
V appce byl natvrdo loňský odkaz `cdbl2526`. Ke Spond eventu se pak tiše
vybral nejbližší hrací den, což byl poslední den loňské sezóny.
*Teď:* výchozí je `cdbl2627`, appka si pamatuje poslední zadaný odkaz, a když
event na žádný hrací den nesedí, řekne to a nechá den vybrat ručně.

**4. Chyběl první hrací den sezóny.**
Tournify ukládá první den jinak než ostatní: jeho zápasy mají den `0` a datum
je jen u turnaje samotného. Server takové zápasy zahazoval. Letos tak chyběla
sobota 10. 10. (31 zápasů), loni stejně vypadl 9. 11.
*Teď:* den `0` se bere z data turnaje.

**5. Hraní na jiném kurtu ve stejný čas.**
Hrající se blokovali až ve chvíli, kdy výpočet došel k jejich zápasu. Zápas na
jiném kurtu ve stejný čas, který přišel na řadu dřív, jim tak mohl přidělit
službu. Tohle se našlo při čtení kódu, v reálném rozvrhu nahlášené nebylo.
*Teď:* časy hraní se zablokují předem pro celý den.

**6. Nerovnoměrné služby a slabé preference.**
Výpočet končil prvním rozdělením (fáze 1 výše), takže někdo mohl mít o dvě
služby víc než jiný, i když to šlo rozdělit líp, a preference rozhodovala jen
při shodě počtu služeb.
*Teď:* přibyly fáze dorovnání a preferencí.

**7. Pořadí stránek v appce.**
Dřív: 1. Tournify (týmy schované za tlačítkem), 2. Spond, 3. preference.
*Teď:* 1. týmy, 2. Tournify + Spond, 3. vocasové a preference.

## Známá omezení

- Čtyři týmy jsou dané a párují se na názvy „Prague Crocodiles A MIX / B MIX /
  M / Ž" (viz Nová sezóna).
- Server drží rozpracovaný stav v paměti a počítá s tím, že rozvrh připravuje
  jeden člověk. Dva lidé generující naráz by si ho přepisovali.
- Když se vybere hrací den, server vezme zápasy do 1,5 dne od něj. Sobota a
  neděle jednoho víkendu se proto generují dohromady a služby se vyrovnávají
  přes celý víkend.
- Týmy jsou uložené v telefonu, ne na serveru. Po odinstalování appky nebo na
  novém telefonu se začíná z výchozích.

---

Vytvořeno pro Prague Crocodiles dodgeball tým 🐊
