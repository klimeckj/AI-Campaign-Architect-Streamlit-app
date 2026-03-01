# AI Campaign Architect

> ⚠️ **Proof of Concept** — tato aplikace demonstruje integraci AI do procesu tvorby marketingových kampaní. Použitý jazykový model (`gemma-3-1b-it`) je záměrně nejlevnější dostupnou variantou Google Gemini, proto kvalita generovaných výstupů není produkční — jde o ukázku možností, nikoli hotový nástroj.

---

## O čem to je

AI Campaign Architect je nástroj, který marketérovi pomáhá projít celým procesem přípravy kampaně — od zadání briefinku až po finální copy připravené k odeslání — bez nutnosti přepínat mezi různými systémy.

Aplikace propojuje tři světy:
- **CDP (Bloomreach)** — zdrojová data o zákaznících a segmentech (DEMO účet)
- **Generativní AI (Google Gemini)** — tvorba strategie a obsahu
- **Marketingový workflow** — strukturovaný postup od briefinku po export

---

## Jak to funguje

### 1. Brief
Marketér zadá produkt, popis cílové skupiny a ID segmentu přímo z Bloomreach. Žádné ruční přepisování dat mezi systémy.

### 2. AI strategie
Na základě briefinku Gemini navrhne marketingovou strategii — analýzu situace, komunikační angle a tone of voice. Výstup lze iterativně upřesňovat přirozeným feedbackem v češtině.

### 3. Generování copy
Automaticky vzniknou texty pro tři kanály: **Email** (předmět + tělo), **SMS** (s validací délky) a **Push notifikace**. Každý kanál lze samostatně doladit dalším iterativním kolem s AI.

### 4. Export a integrace
Výsledky lze stáhnout jako CSV nebo odeslat přímo do **Bloomreach katalogu** přes REST API — připravené k použití v kampaních.

---

## Technologie

Aplikace je postavená na **Streamlit** (Python), komunikuje s **Google Gemini API** a s **Bloomreach Engagement REST API**. Celý workflow běží v prohlížeči bez nutnosti instalace čehokoli na straně uživatele.

---

## Kam to může vést

Proof of concept ukazuje, že propojení CDP + generativní AI zkracuje čas od briefinku k hotovému obsahu z hodin na minuty. S kvalitnějším modelem (např. Gemini 1.5 Pro nebo Flash) a napojením na reálná zákaznická data by výstupy mohly být personalizované na úrovni jednotlivých segmentů nebo zákazníků.
