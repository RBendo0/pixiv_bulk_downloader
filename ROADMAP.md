# ROADMAP – Pixiv Bulk Downloader

## Stato del progetto

L'architettura principale del progetto può ormai considerarsi stabilizzata.

### Milestone completate

* refactoring ERRS;
* introduzione di `caapi` come unico punto di accesso alle API Pixiv;
* alias applicativi (`ui`, `rcc`, `caapi`, `pbd`);
* refactoring dei downloader a metodi di classe;
* coda persistente di `add_list_to_bookmarks()`;
* introduzione del modulo `iofile`;
* uniformazione dei workflow di recovery;
* completamento del Thread Pool System (TPS);
* introduzione del renderer concorrente della console;
* separazione del workflow di download in:

  * `download()`;
  * `_download_artwork()`;
  * `_download_media()`;
* introduzione del nuovo sistema di rendering:

  * calcolo della larghezza effettiva delle colonne;
  * gestione dei caratteri Unicode a larghezza variabile;
  * troncamento automatico con ellissi (`…`);
  * eliminazione del padding tramite `ESC[K`;
  * troncamento semantico nei downloader;
  * nuova formattazione delle righe di progresso;
* introduzione del sistema di configurazione persistente del percorso dell'archivio:

  * distinzione tra root statica dell'applicazione e root dinamica scelta dall'utente;
  * mantenimento del file di configurazione nella root statica;
  * supporto all'argomento CLI dedicato alla root;
  * configurazione interattiva del percorso dal menu principale;
  * salvataggio persistente della root scelta dall'utente;
  * cambio dinamico della root durante l'esecuzione;
  * normalizzazione automatica del percorso con aggiunta della directory finale `pbd`, quando assente;
  * ricostruzione dei percorsi dipendenti dopo ogni modifica della configurazione;
  * risoluzione dei percorsi al momento dell'esecuzione delle azioni del menu;
  * creazione automatica della directory `lists` destinata ai file di URL;
  * backup automatico del file di configurazione;
  * ripristino del file di configurazione in caso di errore;
  * gestione tollerante dell'assenza del file sorgente o del relativo backup;
  * collaudo completato con esito positivo.

Da questo punto in avanti il lavoro sarà concentrato soprattutto sul consolidamento, sul collaudo finale e sulla rifinitura dell'architettura.

---

# 1. Consolidamento delle dipendenze

Stabilizzare definitivamente i confini architetturali del progetto.

Attività previste:

* revisione delle dipendenze interne;
* eliminazione degli import inutilizzati;
* consolidamento delle responsabilità dei package;
* verifica della direzione delle dipendenze;
* eliminazione del codice obsoleto;
* consolidamento degli alias applicativi;
* revisione dell'integrazione di `wcwidth`;
* valutazione dell'inclusione locale delle dipendenze critiche.

Obiettivo finale:

* tutto il codice applicativo dovrà dipendere esclusivamente dalle API interne del progetto.

---

# 2. Revisione del sistema di login

Riorganizzare completamente il workflow di autenticazione.

Argomenti:

* browser Playwright;
* gestione del profilo utente;
* acquisizione del token;
* refresh del token;
* riutilizzo della sessione;
* traduzione uniforme degli errori tramite ERRS;
* revisione delle dipendenze con `my_gppt`;
* verifica dell'attuale errore di autenticazione restituito da `my_gppt`.

---

# 3. Revisione delle librerie esterne

Riesaminare i punti di integrazione con:

* `pixivpy3`;
* `my_gppt`;
* Playwright.

Obiettivi:

* ridurre l'accoppiamento;
* uniformare la traduzione delle eccezioni;
* introdurre eventuali wrapper mancanti;
* impedire la propagazione dei dettagli implementativi delle librerie;
* consolidare il blocco delle versioni.

---

# 4. Collaudo generale

Verifica completa dei workflow applicativi ancora da validare nel loro insieme.

Test previsti:

* login;
* retrieve bookmarks;
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

### Collaudi completati

* configurazione persistente del percorso dell'archivio;
* cambio dinamico della root durante l'esecuzione;
* rilettura della configurazione salvata;
* normalizzazione automatica del suffisso `pbd`;
* download nella root configurata;
* creazione automatica della directory `lists`.

---

# 5. Documentazione e reportistica

Aggiornare progressivamente:

* DecisionLog;
* documentazione architetturale;
* roadmap;
* note progettuali;
* commenti dei principali moduli, privilegiando la motivazione delle decisioni rispetto alla sola descrizione del funzionamento;
* riepiloghi delle milestone completate.

La manutenzione della documentazione e della reportistica accompagna lo sviluppo e non costituisce una fase separata da rinviare alla conclusione del progetto.

---

# 6. Pubblicazione e verifica del repository

Dopo il consolidamento della configurazione e della gestione degli argomenti CLI:

* verificare il repository online per individuare eventuali segnali di utilizzo o download dell'applicazione;
* aggiornare le informazioni pubbliche sullo stato del progetto;
* aggiungere un avviso che chiarisca lo stato di sviluppo e gli eventuali limiti della versione corrente.

---

# 7. Evoluzioni future

Da rivalutare dopo il completamento del collaudo.

## UI

* eventuale evoluzione di `UI.Renderer.write()`;
* costruzione incrementale della riga;
* builder di stringhe;
* gestione automatica dei marcatori (`[+]`, `[i]`, `[!]`, `[?]`);
* uniformazione definitiva tra `ui.line()` e `UI.Renderer.write()`.

## Architettura

* ulteriori semplificazioni dell'architettura interna;
* evoluzione di `caapi`;
* eventuale revisione del sistema di sessione;
* nuove astrazioni nate dall'esperienza maturata durante lo sviluppo.

## Affidabilità dei dati

* introduzione di copie di backup automatiche dei file operativi usati dall'applicazione, comprese le liste di URL impiegate per aggiungere opere ai preferiti;
* definizione delle politiche di rotazione, conservazione e ripristino dei backup.

## Ugoira

* conversione degli archivi ZIP delle ugoira in animazioni;
* definizione del formato di destinazione e della strategia di conversione;
* integrazione della conversione nel workflow senza compromettere il salvataggio dei dati originali.

## Prestazioni

* ottimizzazione del download;
* eventuali miglioramenti del renderer;
* ottimizzazioni del Thread Pool System.
