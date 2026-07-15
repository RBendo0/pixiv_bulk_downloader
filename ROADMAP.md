# ROADMAP – Pixiv Bulk Downloader

## Stato del progetto

L'architettura principale del progetto può ormai considerarsi stabilizzata.

### Milestone completate

- refactoring ERRS;
- introduzione di `caapi` come unico punto di accesso alle API Pixiv;
- alias applicativi (`ui`, `rcc`, `caapi`, `pbd`);
- refactoring dei downloader a metodi di classe;
- coda persistente di `add_list_to_bookmarks()`;
- introduzione del modulo `iofile`;
- uniformazione dei workflow di recovery;
- completamento del Thread Pool System (TPS);
- introduzione del renderer concorrente della console;
- separazione del workflow di download in:
  - `download()`;
  - `_download_artwork()`;
  - `_download_media()`;
- introduzione del nuovo sistema di rendering:
  - calcolo della larghezza effettiva delle colonne;
  - gestione dei caratteri Unicode a larghezza variabile;
  - troncamento automatico con ellissi (`…`);
  - eliminazione del padding tramite `ESC[K`;
  - troncamento semantico nei downloader;
  - nuova formattazione delle righe di progresso.

Da questo punto in avanti il lavoro sarà concentrato soprattutto sul consolidamento, sul collaudo finale e sulla rifinitura dell'architettura.

---

# 1. Consolidamento delle dipendenze

Stabilizzare definitivamente i confini architetturali del progetto.

Attività previste:

- revisione delle dipendenze interne;
- eliminazione degli import inutilizzati;
- consolidamento delle responsabilità dei package;
- verifica della direzione delle dipendenze;
- eliminazione del codice obsoleto;
- consolidamento degli alias applicativi;
- revisione dell'integrazione di `wcwidth`;
- valutazione dell'inclusione locale delle dipendenze critiche.

Obiettivo finale:

- tutto il codice applicativo dovrà dipendere esclusivamente dalle API interne del progetto.

---

# 2. Revisione del sistema di login

Riorganizzare completamente il workflow di autenticazione.

Argomenti:

- browser Playwright;
- gestione del profilo utente;
- acquisizione del token;
- refresh del token;
- riutilizzo della sessione;
- traduzione uniforme degli errori tramite ERRS;
- revisione delle dipendenze con `my_gppt`.

---

# 3. Revisione delle librerie esterne

Riesaminare i punti di integrazione con:

- `pixivpy3`;
- `my_gppt`;
- Playwright.

Obiettivi:

- ridurre l'accoppiamento;
- uniformare la traduzione delle eccezioni;
- introdurre eventuali wrapper mancanti;
- impedire la propagazione dei dettagli implementativi delle librerie;
- consolidare il blocco delle versioni.

---

# 4. Collaudo generale

Verifica completa dei workflow applicativi.

Test previsti:

- login;
- retrieve bookmarks;
- download;
- resume pending jobs;
- add bookmarks;
- convert bookmarks;
- gestione checkpoint;
- rate limit API;
- rate limit download;
- recovery;
- interruzione utente;
- Thread Pool System;
- renderer concorrente.

---

# 5. Documentazione

Aggiornare progressivamente:

- DecisionLog;
- documentazione architetturale;
- roadmap;
- note progettuali;
- commenti dei principali moduli.

---

# 6. Evoluzioni future

Da rivalutare dopo il completamento del collaudo.

## UI

- eventuale evoluzione di `UI.Renderer.write()`;
- costruzione incrementale della riga;
- builder di stringhe;
- gestione automatica dei marcatori (`[+]`, `[i]`, `[!]`, `[?]`);
- uniformazione definitiva tra `ui.line()` e `UI.Renderer.write()`.

## Architettura

- ulteriori semplificazioni dell'architettura interna;
- evoluzione di `caapi`;
- eventuale revisione del sistema di sessione;
- nuove astrazioni nate dall'esperienza maturata durante lo sviluppo.

## Prestazioni

- ottimizzazione del download;
- eventuali miglioramenti del renderer;
- ottimizzazioni del Thread Pool System.