# Wonderland Diorama – ERP-System: Architektur- & Konzeptdokument

Stand: 09.07.2026 · Shop: [WonderlandDiorama auf Etsy](https://www.etsy.com/de/shop/WonderlandDiorama)

Dieses Dokument beantwortet deine zwei Kernfragen (Was liefert Etsy an Daten? Ist Django eine gute Wahl?) und gibt dir eine konkrete Grundlage, die du in VS Code mit Claude Code umsetzen kannst.

## 1. Analyse deiner bisherigen Excel-Datei

Ich habe `Etsy Abrechnungen.xlsx` geöffnet. Dein aktueller Workflow:

1. **Rohdaten Etsy** – hier landet 1:1 der Etsy-Zahlungskonto-CSV-Export (Spalten: Datum, Art, Titel, Info, Währung, Betrag, Gebühren & Steuern, Netto, Steuerliche Angaben) – seit 2022, ca. 3.170 Zeilen.
2. **Bearbeitet 2022–2025** – die Rohdaten, aufgeteilt und nachbearbeitet pro Jahr.
3. **Übersicht 2022–2025** – monatliche Summen (Betrag / Gebühren / Netto).
4. **Pivot-Daten / Pivot-Tabellen** – Kreuztabellen Monat × Jahr.
5. **Gesamt Übersicht** – Jahressummen inkl. Veränderung zum Vorjahr in %.

Wichtig zu verstehen: **Das ist ausschließlich Finanzbuchhaltung** (Verkäufe, Gebühren, Steuern, Auszahlungen) – Etsy liefert dir darüber keine Artikel-, Bestell- oder Kundendaten. Für "Artikelliste", "Bestellungen", "Kontakte" brauchst du zusätzliche Etsy-Exporte bzw. die API (siehe unten). Dein aktueller Bearbeitungsaufwand (manuell CSV einfügen, Kategorien pflegen, Pivots aktuell halten) ist genau der Teil, den ein ERP automatisieren soll.

## 2. Was liefert dir Etsy an Daten?

Etsy bietet drei Wege an Daten heranzukommen – für dein ERP relevant sind alle drei, in unterschiedlichen Ausbaustufen:

### 2.1 Manuelle CSV-Exporte (Shop-Manager, das, was du heute schon nutzt)

Du hast mir mittlerweile alle drei real vorliegenden Exporte deines Shops zum Prüfen gegeben – hier die **tatsächlichen, verifizierten Spalten** (keine Annahmen mehr):

- **Zahlungskonto-Abrechnung ("Statement/Bookkeeping")** – genau die Datei, die du schon importierst: `Datum, Art, Titel, Info, Währung, Betrag, Gebühren & Steuern, Netto, Steuerliche Angaben`. Jede Fee, jede Sale-Zahlung, jede USt.-Buchung, jede Überweisung aufs Bankkonto, pro Monat exportierbar. Enthält keine Bestell-Details außer der Order-Nummer im Freitext.
- **Bestellungen / "sold order items" CSV** (dein `EtsySoldOrders2023.csv`, pro Jahr exportierbar): 35 Spalten – u. a. `Sale Date, Order ID, Buyer User ID, Full Name, First Name, Last Name, Number of Items, Payment Method, Date Shipped, Street 1/2, Ship City/State/Zipcode/Country, Currency, Order Value, Coupon Code, Coupon Details, Discount Amount, Shipping Discount, Shipping, Sales Tax, Order Total, Status, Card Processing Fees, Order Net, Adjusted Order Total/Net, Order Type, Payment Type, SKU`. Das ist deine vollständige Quelle für **Bestellungen + Kontakte (Kunden)** inkl. Adresse, Rabattcode, Versandkosten und Kartengebühren pro Bestellung.
- **Listing-/Artikel-CSV** (dein `EtsyListingsDownload.csv`, 237 Zeilen, deutschsprachige Spalten weil dein Shop auf Deutsch läuft): `TITEL, BESCHREIBUNG, PREIS, WÄHRUNGSCODE, STÜCKZAHL, TAGS, MATERIALIEN, BILD1–BILD10, VARIATIONSTYP/-NAME/-WERT 1–2, BESTANDSEINHEIT`. Das ist deine Quelle für die **Artikelliste** inkl. bis zu 10 Bildern pro Artikel und Varianten (z. B. "Ausführung: A, B").

Alle drei sind manuelle Downloads (Monat/Jahr oder ganzes Jahr wählbar) – kein Live-Sync, aber ausreichend, um deine komplette Historie seit 2022 einmalig zu importieren.

> **Wichtiger Befund beim Datenabgleich:** Die Listing-CSV enthält **keine Etsy-Listing-ID** und `BESTANDSEINHEIT` (= dein SKU-Feld) ist bei den meisten Artikeln leer. Die Orders-CSV wiederum hat ein `SKU`-Feld, das bei dir aber uneinheitlich befüllt ist – teils Produktkürzel (`LIND`, `WELSCH`, `PHOENIX`, `IMPEXCO`), teils reine Zahlencodes (`1`, `5`, `16`), teils leer, teils eine Kommaliste bei Mehrfachbestellungen (`"LIND,LIND"`). Das heißt: **Artikel und Bestellpositionen lassen sich aus den CSVs allein nicht zuverlässig 1:1 verknüpfen.** Zwei Wege, das zu lösen: (a) du pflegst ab jetzt konsequent eindeutige SKUs in jedem Listing, dann matcht der Import sauber; (b) du gehst mittelfristig auf die Etsy-API, die pro Bestellung eine stabile `listing_id` mitliefert. Fürs Erste importierst du beide Quellen unabhängig (Artikel-Stammdaten separat von Bestellpositionen) und verknüpfst nur dort, wo das SKU-Matching eindeutig ist – der Rest bleibt als "Bestellposition ohne Artikel-Zuordnung" sichtbar, statt falsch zu raten.

### 2.2 Bewertungen (Reviews) – zusätzliche Datenquelle, die du bereitstellen kannst

Dein `reviews.json` (136 Bewertungszeilen zu 91 unterschiedlichen Bestellungen, Zeitraum Ende 2022 bis Juli 2026) hat die Struktur `reviewer, date_reviewed, star_rating, message, order_id`. `order_id` verknüpft sich direkt mit `Order ID` aus der Bestell-CSV. Verteilung bislang: 118× 5 Sterne, 14× 4 Sterne, 2× 3 Sterne, 2× 2 Sterne – also durchgehend sehr positiv, aber mit ein paar konkreten Kritikpunkten (Farbabweichung zum Foto taucht mehrfach auf – eventuell relevant für deine Produktfotos). Bei Mehrfachbestellungen gibt es oft mehrere Bewertungszeilen pro `order_id` (eine pro Artikel) – das Datenmodell sollte das als 1:n (Order → Reviews) abbilden, nicht 1:1.

### 2.3 Etsy Open API v3 (developers.etsy.com)

Für den Automatisierungs-Ausbau später: eine REST-API mit OAuth2, kostenloser API-Key (als Shop-Inhaber für den eigenen Shop unkompliziert zu bekommen). Relevante Ressourcen:

- **Shop / ShopListing / ListingInventory** – Artikel inkl. Bestand, Varianten, Bilder (lesend & schreibend) → ersetzt später den manuellen Listing-CSV-Import.
- **Receipts** (= Bestellungen) inkl. Transaktionen pro Artikel, Versandstatus, Käuferinfo → ersetzt später den Bestell-CSV-Import.
- **Payment Ledger Entries** – programmatischer Zugriff auf exakt die Buchungen, die heute in deiner Statement-CSV stehen → automatischer Finanz-Import statt Copy-Paste.
- **ShopSection, ShippingProfile, Reviews, Taxonomy** – ergänzende Stammdaten.

Rate-Limits und genaue Freigabe-Bedingungen ändern sich gelegentlich – das solltest du bei [developers.etsy.com/documentation](https://developers.etsy.com/documentation/) zum Zeitpunkt der Umsetzung gegenprüfen. Für den Start reicht der CSV-Import völlig; die API ist ein sauberer Ausbauschritt (Phase 6 unten), kein Blocker für den Projektstart.

**Empfehlung:** Baue den CSV-Import zuerst (deckt deine komplette Historie ab, keine Freigabe-Wartezeit), API-Sync als spätere Komfort-Stufe.

## 3. Ist Django eine gute Wahl?

**Ja – für genau dieses Profil (interne Business-Anwendung, CRUD-lastig, ein bis wenige Nutzer, Docker-Self-Hosting) ist Django eine der besten Optionen.** Begründung:

- **Django Admin ist praktisch die halbe App gratis.** Artikel, Kontakte, Aufgaben, Infothek-Einträge – all das kannst du initial über das eingebaute Admin-Interface verwalten, bevor du überhaupt eigene Formulare baust.
- **Benutzermanagement ist eingebaut** (`django.contrib.auth` + Gruppen/Permissions) – deckt deinen Punkt "Benutzermanagement" ohne Zusatzaufwand ab.
- **ORM + Migrations** passen sehr gut zu Finanz-/Bestelldaten mit klaren Beziehungen (Bestellung → Positionen → Artikel → Kontakt).
- **Reifes Ökosystem** für alles, was du brauchst: `django-import-export` (CSV-Import inkl. deiner Etsy-Exporte), `django-tables2`/HTMX für Tabellen & Dashboards, `weasyprint`/`django-weasyprint` für PDF-Berichte, `django-filter` für Monats-/Quartals-/Jahresfilter.
- **Docker-Deployment ist Standard-Terrain** – unzählige Referenz-Setups für Django + Postgres + Gunicorn + Nginx via docker-compose, das läuft problemlos auf Unraid (eigener Container oder über Unraids Docker-Compose-Manager-Plugin).
- **Claude Code kennt Django sehr gut**, weil es extrem verbreitet und gut dokumentiert ist – das macht die Zusammenarbeit in VS Code effizienter als mit exotischeren Frameworks.

Ehrliche Abwägung – wann Django *nicht* ideal wäre: wenn du eine hochinteraktive Single-Page-App mit viel Live-Client-State bräuchtest (dann eher FastAPI + React), oder wenn der Umfang wirklich nur eine Tabelle bliebe (dann würde sich Airtable/Baserow lohnen). Für dein Feature-Set (Artikel, Bestellungen, Finanzen, Kontakte, Dashboard, Aufgaben, Wissensdatenbank, Nutzerverwaltung) ist das aber klar ein Fall für ein "richtiges" Backend-Framework mit Admin-Oberfläche – Django passt.

## 4. Vorgeschlagene Architektur

```
Backend:      Django 5.x (Python 3.12)
Datenbank:    SQLite (Docker-Volume, eine Datei) – Revision, siehe unten
Web-Server:   Gunicorn + Nginx (oder Caddy) als Reverse Proxy
Frontend:     Django-Templates + HTMX + Chart.js (kein separates SPA-Framework nötig)
Reporting:    django-import-export, django-filter, weasyprint (PDF)
Deployment:   Dockerfile + docker-compose.yml, .env für Secrets
Zielplattform: Unraid (Docker-Compose-Manager-Plugin oder eigener Container-Stack)
```

### Datenbank-Revision: SQLite statt PostgreSQL

Meine ursprüngliche Empfehlung war Postgres – nach deiner Nachfrage und einem ehrlichen Blick auf deine tatsächliche Datenmenge ist **SQLite die bessere Wahl für den Start**:

- **Datenvolumen:** ~3.170 Buchungszeilen seit 2022, 237 Artikel, ein paar hundert Bestellungen/Jahr. Das ist für SQLite trivial – SQLite handhabt problemlos Millionen Zeilen; du bist Größenordnungen davon entfernt, an eine Grenze zu stoßen.
- **Nutzerprofil:** Du bist (aktuell) Einzelnutzer bzw. wenige Nutzer. SQLites historische Schwäche – nur ein Schreibzugriff gleichzeitig – spielt bei einer internen Anwendung mit gelegentlichen, nicht parallelen Schreibvorgängen praktisch keine Rolle, zumal Django/SQLite im WAL-Modus auch nebenläufige Lesezugriffe sauber unterstützt.
- **Einfacheres Deployment:** Kein separater `db`-Container, kein DB-Passwort-Management, kein Verbindungsaufbau, der schiefgehen kann. Ein Docker-Volume für eine einzelne `.sqlite3`-Datei reicht.
- **Trivialere Backups:** Backup = Datei kopieren (z. B. nächtlicher `cp`/`rsync` auf ein zweites Unraid-Share), statt `pg_dump`/`pg_restore`-Tooling zu pflegen.
- **Weniger Ressourcenverbrauch** auf deinem Unraid-Server – relevant, wenn dort noch andere Container laufen.

**Wann sich der Wechsel zu Postgres lohnt** (Django macht das später über einen Zeilenwechsel in `DATABASES` + `migrate` relativ schmerzfrei, ein Schema-Redesign ist dafür nicht nötig): sobald mehrere Personen wirklich gleichzeitig schreibend arbeiten (z. B. du erfasst Bestellungen, während gleichzeitig jemand anderes Finanzbuchungen einträgt), du sehr rechenintensive Auswertungen über die komplette Historie brauchst, oder du das System für mehr als deinen eigenen Shop einsetzen willst. Für den aktuellen Zuschnitt (Solo-Etsy-Shop, Dashboard/Berichte, Docker auf Unraid) ist das nicht in Sicht – SQLite ist hier nicht die "Einsteiger-Notlösung", sondern schlicht die passende Wahl.

### Modulaufteilung (Django-Apps), gemappt auf deine Feature-Liste

| Django-App | Deckt ab |
|---|---|
| `accounts` | Benutzermanagement (eingebaut, Gruppen/Rechte) |
| `catalog` | Artikelliste (Import aus Etsy-Listing-CSV/API), Varianten, Bestand |
| `wishlist` | Wunschliste (zukünftige Artikel), eigenständiges Modell mit Verweis auf `catalog` |
| `orders` | Bestellungen anlegen (aus Etsy-Bestell-CSV/API importierbar + manuell erfassbar) |
| `finance` | Einnahmen/Ausgaben – Ledger-Modell, gespeist aus der Statement-CSV (dein heutiges Kernstück), inkl. manueller Ausgaben (Material, Werkzeug, Verpackung) |
| `contacts` | Kontakte – Kunden (aus Bestell-CSV) + Lieferanten/Großhändler (manuell) |
| `reports` / `dashboard` | Berichte + Dashboard mit Monats-/Quartals-/Jahresfilter (aggregiert über `finance` + `orders` + Bewertungsschnitt) |
| `reviews` (Teil von `orders`) | Bewertungen (aus `reviews.json`), 1:n mit Order verknüpft, Trend im Dashboard |
| `knowledge` | Infothek/Toolbox – einfache Notiz-/Wiki-Einträge |
| `tasks` | Aufgaben – einfaches To-Do-/Kanban-Modell, optional verknüpft mit Bestellungen |

### Kern-Datenmodelle (Skizze, keine vollständige Implementierung)

- `Article` (Titel, Beschreibung, Preis, Währung, Stückzahl, Tags, Materialien, bis zu 10 Bild-URLs, Varianten [Typ/Name/Wert 1–2], SKU optional – Felder 1:1 aus der Listing-CSV; **keine** garantiert eindeutige Etsy-ID, SKU-Pflege ist Voraussetzung für sauberes Matching)
- `WishlistItem` (Titel, Notizen, geschätzter Preis, Status)
- `Order` (Etsy-Order-ID, Sale Date, Date Shipped, Buyer FK, Anzahl Artikel, Order Value, Coupon Code/Discount, Shipping, Sales Tax, Order Total, Card Processing Fees, Order Net, Status) → `OrderItem` (Article FK optional/nullable falls Matching nicht eindeutig, SKU-Rohwert, Menge, Preis)
- `Review` (Reviewer-Name, Datum, Sternebewertung, Text, Order FK) – 1:n zu `Order`
- `Contact` (Typ: Kunde/Lieferant, Name, Adresse [Straße 1/2, Stadt, Bundesland/Region, PLZ, Land], Etsy-Buyer-User-ID optional)
- `LedgerEntry` (Datum, Art [Sale/Fee/USt./Überweisung], Titel, Info, Betrag, Gebühren, Netto, Quelle: Etsy-Import/manuell) – bildet 1:1 deine bisherige Excel-Logik ab
- `Expense` (für manuelle Ausgaben außerhalb der Etsy-Abrechnung: Material, Werkzeug, Fahrtkosten etc.)
- `Task` (Titel, Fälligkeit, Status, verknüpfte Order/Contact optional)
- `KnowledgeEntry` (Titel, Inhalt/Markdown, Tags)

### CSV-Import-Strategie

Ein `management command` (`python manage.py import_etsy_statement <file>.csv`) pro Exporttyp (Statement, Orders, Listings), das:

- deine bereits bekannten Eigenheiten behandelt (Beträge mit `--`-Platzhalter, deutsche Zahlenformate, deutsche Datumsangaben wie "30. Oktober 2023", USD-Beträge in Klammern im Titel bei Einstellgebühren),
- idempotent ist (Re-Import derselben Datei erzeugt keine Duplikate, z. B. über eine Kombination aus Datum+Titel+Betrag als natürlichen Schlüssel oder Etsy-interne IDs, sofern vorhanden),
- deine komplette Historie 2022–2025 aus der vorhandenen Excel-Datei einmalig migrieren kann (Rohdaten-Sheet als Ausgangspunkt).

## 5. Docker/Unraid-Deployment

```
docker-compose.yml
├── web (Django + Gunicorn, gebaut aus eigenem Dockerfile, SQLite-Datei im Volume)
└── nginx (Reverse Proxy, Volume für Static/Media)
```

- `.env`-Datei für `SECRET_KEY`, `ALLOWED_HOSTS` etc. – nicht ins Repo committen.
- Ein Docker-Volume für die SQLite-Datenbankdatei und eines für hochgeladene Medien (Artikelbilder) auf ein Unraid-Share mappen, damit sie Container-Neustarts überleben.
- Auf Unraid entweder als eigener Compose-Stack über das "Docker Compose Manager"-Plugin oder als einzelne Container über die Unraid-Docker-UI.
- Backup-Routine: nächtlicher `cp`/`sqlite3 .backup` der DB-Datei plus Medien-Ordner auf ein zweites Unraid-Share (deutlich einfacher als bei Postgres).

## 6. Infothek/Toolbox – konkrete Tool-Ideen

Du hattest nach eingebauten Rechnern/Nachschlage-Tools gefragt (Verpackungslizenz, Versandpreise Post/DHL, Zollinfos). Passend zu deinem Profil (Edelstein-/Heilstein-Versand aus Deutschland, laut deinen Bestelldaten auch international – ich sehe in deiner Orders-CSV Lieferungen nach Frankreich, Schweiz, Österreich und in die USA) hier konkrete, sinnvolle Bausteine für die `knowledge`-App:

- **Verpackungslizenz-Rechner (LUCID/Verpackungsgesetz):** Du hinterlegst deine üblichen Versandverpackungen (Typ, Material, Gewicht – z. B. "gepolsterter Umschlag klein: Papier 15g + Luftpolster 5g") als Stammdaten. Das Tool multipliziert das mit deiner Jahres-Versandmenge (aus `orders`) und zeigt dir die für die LUCID-Meldung/Systembeteiligung relevante Gesamtmenge pro Material. Die eigentlichen Lizenzentgelte der dualen Systeme (z. B. Landbell, Interseroh) ändern sich regelmäßig – die solltest du als Preis-/Tarif-Tabelle mit Gültigkeitsdatum pflegen statt fest im Code zu verdrahten, dann bleibt das Tool über Jahre hinweg korrekt nutzbar. Link-Sammlung zu verpackungsregister.org als Ausgangspunkt gehört mit in die Infothek.
- **Versand-Rechner (Post/DHL):** Eine Tabelle deiner genutzten Produkte (Warenpost, Päckchen, Paket, Einschreiben, internationale Zonen) mit Gewicht/Maßen → Preis, ebenfalls mit Gültigkeitsdatum, weil Post/DHL die Preise meist jährlich zum Jahreswechsel anpassen. Rechner nimmt Artikelgewicht(e) aus einer Bestellung, schlägt Verpackungsgewicht drauf und zeigt dir die passende Versandoption + ob dein verlangter Versandpreis (aus der Order) die tatsächlichen Kosten deckt.
- **Zoll-Infothek (Tarifnummern):** Eine kleine Referenztabelle mit den für dein Sortiment relevanten Zolltarifnummern (z. B. Positionen für rohe/bearbeitete Halbedelsteine, Schmuck aus Naturstein, Mineralien) inkl. Kurzbeschreibung und Link zum offiziellen "Elektronischer Zolltarif" (EZT-Online) für Detailrecherche. Besonders nützlich, weil deine Bestelldaten zeigen, dass du auch **außerhalb der EU** versendest (Schweiz, USA) – dort brauchst du eine Zollinhaltserklärung (CN22/CN23) mit korrekter Tarifnummer und Warenwert. Ein Baustein könnte pro Bestellung mit Nicht-EU-Zielland automatisch daran erinnern, dass eine Zollerklärung nötig ist.
- **Etsy-Gebühren-/Preiskalkulator:** Da du die Gebührenstruktur aus deiner Statement-Historie schon kennst (Einstellgebühr 0,20 USD, Transaktionsgebühr ca. 6,5 %, Zahlungsabwicklungsgebühr ca. 4 % + Fixbetrag), lohnt sich ein Rechner: Einkaufspreis/Materialkosten + Zeitaufwand + Verpackung eingeben → Vorschlag für Verkaufspreis bei gewünschter Zielmarge, inkl. Simulation "was bleibt netto übrig". Praktisch direkt verknüpft mit der Wunschliste, bevor du einen neuen Artikel einstellst.
- **Edelstein-/Heilstein-Nachschlagewerk:** Referenztabelle deiner verwendeten Steine (Mohshärte, Herkunft, traditionelle Bedeutung/Wirkung laut Überlieferung, Pflege-/Reinigungshinweise) – nützlich sowohl als internes Nachschlagewerk als auch als Textbaustein-Quelle für neue Artikelbeschreibungen.
- **Einheiten-Umrechner:** Karat ↔ Gramm, mm ↔ Zoll – kleine, aber im Steinhandel ständig gebrauchte Umrechnung.

Wichtig bei allen "Rechnern mit echten Preisen/Sätzen" (Verpackungslizenz, Versand, Zoll): Die Zahlen selbst gehören als **von dir pflegbare Datensätze mit Gültigkeitsdatum** in die Datenbank (über das Django-Admin editierbar), nicht hart in den Code – Preise/Sätze ändern sich regelmäßig, und ein Update sollte kein Redeploy erfordern.

## 7. Vorgeschlagene Roadmap

1. **Phase 0** – Projekt-Grundgerüst: Django-Projekt, `accounts`-App, Docker-Compose (web+nginx, SQLite), CI-freier lokaler Dev-Workflow.
2. **Phase 1** – `finance`: Datenmodell + CSV-Import für die Statement-Historie (ersetzt direkt deine Excel-Datei, weil die Daten schon vorliegen).
3. **Phase 2** – `contacts` + `orders`: Import aus Bestell-CSV, manuelle Erfassung.
4. **Phase 3** – `catalog` + `wishlist`: Import aus Listing-CSV.
5. **Phase 4** – `dashboard`/`reports`: Filter nach Monat/Quartal/Jahr, Charts (Chart.js), PDF-Export.
6. **Phase 5** – `knowledge` + `tasks`.
7. **Phase 6** – Etsy-API-Anbindung (OAuth, automatischer Sync statt CSV-Copy-Paste) – jetzt lohnt sich der Aufwand, weil die Datenmodelle schon stehen.
8. **Phase 7** – Rechte-Feinschliff (falls du z. B. später jemanden für Buchhaltung/Versand mit eingeschränktem Zugriff einbindest), Feinschliff, Backups, Monitoring.
9. **Phase 8** – `knowledge`-Toolbox: Verpackungslizenz-/Versand-/Zoll-Rechner, Etsy-Gebührenkalkulator, Edelstein-Nachschlagewerk (siehe Abschnitt 6) – baut auf `orders`/`finance` auf, deshalb bewusst spät in der Roadmap.

## 8. Offene Entscheidungen für dich

- **Umfang Etsy-API:** Direkt mit einplanen oder bewusst erstmal weglassen und nur CSV-Import bauen?
- **Multi-User:** Nur du, oder sollen später z. B. Familienmitglieder/Mitarbeiter mit eingeschränkten Rechten (z. B. nur Bestellungen, kein Finanzzugriff) arbeiten?
- **SKU-Pflege:** Bist du bereit, ab jetzt jedem Listing eine eindeutige SKU zu geben (löst das Matching-Problem aus Abschnitt 2.1 sauber), oder soll das ERP von Anfang an auf unsauberes Matching mit manueller Nachpflege ausgelegt sein?
- **Kleinunternehmerregelung/USt.-Status:** Relevant für die Ausgestaltung der `finance`-Berichte (z. B. ob eine USt.-Voranmeldungs-Ansicht gebraucht wird) – sag kurz Bescheid, wie du aktuell umsatzsteuerlich aufgestellt bist.

---

*Dieses Dokument ist als Ausgangspunkt für deine Coding-Session mit Claude Code in VS Code gedacht. Sag Bescheid, wenn ich zusätzlich schon ein lauffähiges Django-Grundgerüst (Projektstruktur, Modelle, Docker-Compose, CSV-Import) hier anlegen soll, das du dann direkt weiterentwickelst.*
