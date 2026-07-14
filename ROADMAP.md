# ROADMAP – Pixiv Bulk Downloader

## Stato del progetto

L'architettura principale del progetto è ormai stabilizzata.

Milestone completate:

* refactoring ERRS;
* introduzione di `caapi` come unico punto di accesso alle API Pixiv;
* alias applicativi (`ui`, `rcc`, `caapi`, `pbd`);
* refactoring dei downloader a metodi di classe;
* coda persistente di `add_list_to_bookmarks()`;
* introduzione del modulo `iofile`;
* uniformazione dei workflow di recovery;
* completamento del Thread Pool System;
* introduzione del renderer concorrente della console;
* separazione del workflow di download in:
  * `download()`;
  * `_download_artwork()`;
  * `_download_media()`.

Da questo punto in avanti il lavoro si concentrerà principalmente sul consolidamento dell'architettura, sul collaudo e sulle rifiniture delle API interne.

---

# 1. Rifinitura della UI

Consolidare l'interfaccia della console rendendola più uniforme e semplice da utilizzare.

Obiettivi:

* evoluzione di `UI.Renderer.write()` verso un'interfaccia compatibile con `ui.line()`;
* costruzione incrementale della riga;
* gestione interna di colori e concatenazione;
* eliminazione della manipolazione diretta delle sequenze ANSI da parte del chiamante.

Revisione generale dell'API di output:

* introduzione automatica dei marcatori di inizio riga (`[+]`, `[i]`, `[!]`, `[?]`);
* il chiamante dovrà fornire solamente il testo del messaggio;
* la UI costruirà automaticamente:
  * marcatore;
  * colore;
  * formattazione;
* uniformazione dell'interfaccia tra:
  * `ui.line()`;
  * `UI.Renderer.write()`;
  * eventuali future routine di output.

---

# 2. Consolidamento delle dipendenze

Stabilizzare definitivamente i confini architetturali.

Verificare:

* direzione delle dipendenze;
* import inutilizzati;
* responsabilità dei package;
* eliminazione del codice obsoleto;
* coerenza degli alias applicativi;
* separazione definitiva tra codice applicativo e librerie esterne.

Obiettivo finale:

* tutti gli accessi a Pixiv dovranno transitare esclusivamente attraverso `caapi`.

---

# 3. Revisione del sistema di login

Riorganizzare completamente il workflow di autenticazione.

Argomenti da affrontare:

* analisi del workflow attuale;
* browser utilizzato da Playwright;
* gestione del browser indipendente dal browser predefinito;
* gestione del profilo utente;
* revisione dell'acquisizione del token di autenticazione;
* gestione del refresh del token;
* apertura e riutilizzo della sessione API;
* traduzione uniforme degli errori di login tramite ERRS;
* eliminazione delle dipendenze inutili tra login e browser.

---

# 4. Revisione delle librerie esterne

Riesaminare i punti di integrazione con:

* `pixivpy3`;
* `my_gppt`;
* Playwright.

Obiettivi:

* ridurre l'accoppiamento;
* uniformare la traduzione delle eccezioni;
* valutare eventuali wrapper mancanti;
* impedire che dettagli implementativi delle librerie si propaghino nel codice applicativo;
* consolidare il blocco delle versioni delle dipendenze.

---

# 5. Collaudo generale

Verifica completa dei workflow principali.

Test previsti:

* login;
* fetching;
* download;
* resume pending jobs;
* add bookmarks;
* convert bookmarks;
* gestione checkpoint;
* rate limit API;
* rate limit download;
* recovery;
* interruzione utente;
* Thread Pool System;
* renderer concorrente.

---

# 6. Documentazione

Aggiornare progressivamente:

* `DECISIONLOG`;
* documentazione architetturale;
* roadmap;
* note progettuali;
* commenti dei principali moduli.

---

# Valutazioni future

Da rivalutare dopo il completamento del collaudo:

* ottimizzazione delle prestazioni del download;
* evoluzione di `caapi`;
* eventuale revisione del sistema di sessione;
* ulteriori semplificazioni dell'architettura interna;
* nuove astrazioni nate dall'esperienza maturata durante lo sviluppo.# Valutazioni future

Da riesaminare dopo il completamento del TPS:

* ottimizzazione del download;
* evoluzione di `caapi`;
* eventuale revisione del sistema di sessione;
* ulteriori semplificazioni dell'architettura interna.

* evoluzione di `UI.Renderer.write()`:

  * interfaccia compatibile con `ui.line()`;
  * costruzione incrementale della riga;
  * gestione interna di colori e concatenazione;
  * eliminazione della manipolazione diretta delle sequenze ANSI da parte del chiamante.

* revisione dell'API di output della UI:

  * introduzione automatica dei marcatori di inizio riga (`[+]`, `[i]`, `[!]`, `[?]`);
  * il chiamante dovrà fornire solo il testo del messaggio;
  * la UI costruirà automaticamente il prefisso, il colore e la formattazione;
  * uniformazione dell'interfaccia tra `ui.line()`, `UI.Renderer.write()` e le altre routine di output.