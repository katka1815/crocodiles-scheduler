# Turnajový scheduler – Prague Crocodiles

Tenhle nástroj ti pomůže připravit rozvrh služeb na dodgeballový turnaj.
Automaticky přiřadí rozhodčí a podávající ke každému zápasu, spravedlivě
a bez konfliktů (nikdo nemůže být na dvou místech najednou).

---

## Co budeš potřebovat

- Počítač s Windowsem (nebo Mac/Linux)
- Připojení k internetu
- Přihlašovací údaje do Spondu (email + heslo)
- Group ID skupiny Prague Crocodiles ve Spondu

---

## Instalace (jenom jednou)

### Krok 1 – Nainstaluj Python

**Windows:**
1. Jdi na https://python.org/downloads
2. Stáhni nejnovější verzi (velké žluté tlačítko)
3. Spusť instalátor – **zaškrtni "Add Python to PATH"** (důležité!)
4. Klikni Install Now

**Mac:**
- Python je většinou už nainstalovaný. Zkus v Terminálu napsat `python3 --version`

### Krok 2 – Nainstaluj knihovnu pro Spond

Otevři terminál (na Windows: zmáčkni Win + R, napiš `cmd`, Enter) a napiš:

```
pip install spond
```

Počkej až se doinstaluje, pak terminál nech otevřený.

---

## Jak spustit

1. Rozbal ZIP se soubory někam na plochu (třeba složka `spond_scheduler`)
2. V terminálu přejdi do té složky:
   ```
   cd C:\Users\TvojeJmeno\Desktop\spond_scheduler
   ```
3. Spusť server:
   ```
   py server.py
   ```
   (Pokud `py` nefunguje, zkus `python server.py` nebo `python3 server.py`)

4. Uvidíš hlášku že server běží. **Terminál nech otevřený!**
5. Otevři prohlížeč a jdi na adresu: **http://localhost:8765**

---

## Jak to používat

### Krok 1 – Načti rozpis z Tournify

- URL turnaje je předvyplněná, stačí kliknout **Načíst z Tournify**
- Stáhne se celý letošní rozvrh automaticky (žádné CSV, žádný export)

### Krok 2 – Zjisti kdo přijde

Máš dvě možnosti:

**Možnost A – přes Spond (doporučeno):**
1. Zadej svůj Spond email a heslo
2. Group ID je předvyplněné, nemusíš měnit
3. Klikni **Zkontrolovat účast**
4. Zobrazí se seznam akcí – vyber tu správnou (zvýrazněné jsou ty co sedí na datum z Tournify)
5. Uvidíš kdo potvrdil, kdo odmítl, kdo neodpověděl
6. Zaškrtávátky uprav seznam (někdo se zapomněl přihlásit apod.)
7. Klikni **Potvrdit tento seznam**

**Možnost B – bez Spondu:**
1. Klikni **Použít všechny členy**
2. Vyber datum herního dne ze seznamu tlačítek

### (Volitelně) Nastav preference hráčů

Pod sekcí účasti je **Preference hráčů** – rozbal ji a nastav každému:
- **rozhodčí** – radši píská
- **podavač** – radši podává
- **je mi to jedno** – výchozí stav

Preference ovlivní výběr při stejném počtu služeb, ale nepřebíjí spravedlnost –
každý bude mít přibližně stejný počet služeb bez ohledu na preferenci.

### Krok 3 – Vygeneruj rozvrh

- Klikni **Vygenerovat rozvrh**
- Zobrazí se tabulka se všemi zápasy kde Prague Crocodiles něco dělají
  (zápasy cizích týmů bez naší účasti jsou skryté)

### Jak přečíst tabulku

| Sloupec | Co znamená |
|---|---|
| Hrají | Který náš tým hraje (je celý zaneprázdněný) |
| Rozhodčí | 4 lidi co pískají (název týmu nad jmény) |
| Podávání | 3 lidi co podávají (název týmu nad jmény) |

### Nahradit hráče

Pokud někdo nemůže (zranil se, odjel...), klikni na jeho jméno v tabulce.
Otevře se okno se seznamem dostupných náhradníků – vyber jiného, tabulka
se okamžitě přepíše.

### Stažení PNG

Klikni **PNG** – stáhne se obrázek tabulky, který můžeš sdílet v Messengeru.

---

## Pravidla přiřazování

- **Hraní** je uvedeno v rozpisu – celý tým hraje, nikdo z něj nemůže nic dalšího
- **Pískání** je taky z rozpisu – přiřadí se 4 lidi z toho týmu
- **Podávání** se určuje podle hrajícího týmu:
  - Prague Crocodiles A MIX hraje → podává Mix B
  - Prague Crocodiles B MIX hraje → podává Mix A
  - Prague Crocodiles M hraje → podávají Ženy
  - Prague Crocodiles Ž hraje → podávají Muži
- Nikdo nemůže dělat dvě věci najednou (ani v různých zápasech ve stejný čas)
- Pokud je tým ve stejnou hodinu rozhodčí i podávající, 4 rozhodčí se vyberou první,
  podávající se volí ze zbytku
- Celkový počet služeb je co nejrovnoměrnější

---

## Něco nefunguje?

**"Server nedostupný"**
→ Zkontroluj že terminál s `py server.py` stále běží. Pokud ne, spusť znovu.

**pip install spond nefunguje**
→ Zkus `pip3 install spond` nebo `python -m pip install spond`

**Chyba přihlášení do Spondu**
→ Zkontroluj email a heslo. Group ID musí být přesně zkopírované z URL skupiny:
spond.com/client/groups/TOTO_JE_GROUP_ID/

**Tournify nenačte data**
→ Zkontroluj připojení k internetu. URL turnaje musí obsahovat /live/cdbl2526/

**Server běží ale v prohlížeči nic není**
→ Zkus adresu http://127.0.0.1:8765 místo localhost:8765

**Chceš změnit seznam hráčů nebo týmů**
→ Otevři server.py v poznámkovém bloku, najdi sekci MEMBERS_BY_TEAM a uprav jména.
  Po uložení restartuj server (Ctrl+C a znovu py server.py).

---

Vytvořeno pro Prague Crocodiles dodgeball tým 🐊
