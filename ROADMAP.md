# ROADMAP – Pixiv Bulk Downloader

## Stato del progetto

L'architettura principale dell'applicazione è ormai stabilizzata.

Completati:

* refactoring ERRS;
* introduzione di `caapi` come unica interfaccia verso Pixiv;
* alias applicativi (`ui`, `rcc`, `caapi`, `pbd`);
* refactoring dei downloader a metodi di classe;
* completamento della coda persistente di `add_list_to_bookmarks()`;
* introduzione del modulo `iofile` (`CsvFile`);
* uniformazione dei workflow di recovery e delle control exception.

Le prossime attività riguardano prevalentemente consolidamento, pulizia architetturale e parallelizzazione del download.

---

# 1. Thread Pool System (TPS)

Prima milestone della prossima fase.

Obiettivi:

* parallelizzare esclusivamente il download;
* mantenere seriali login, fetching e gestione bookmark;
* definire il modello dei worker;
* coordinare checkpoint e recovery;
* integrare il sistema con ERRS;
* preservare la consistenza dello stato persistente;
* evitare condizioni di gara sui file condivisi;
* verificare l'impatto del rate limit con più worker.

---

# 2. Riordino delle dipendenze

Completato il refactoring funzionale, procedere al consolidamento dei confini architetturali.

Verificare:

* direzione delle dipendenze tra i moduli;
* import inutilizzati;
* responsabilità dei package;
* eliminazione del codice obsoleto;
* coerenza degli alias applicativi;
* eventuale semplificazione di `__init__.py`;
* separazione definitiva tra codice applicativo e librerie esterne.

In particolare verificare che i moduli applicativi accedano a Pixiv esclusivamente tramite `caapi`.

---

# 3. Revisione delle librerie esterne

Riesaminare i punti di integrazione con:

* `my_gppt`;
* `pixivpy3`.

Obiettivi:

* ridurre l'accoppiamento;
* uniformare la traduzione delle eccezioni;
* valutare eventuali wrapper mancanti;
* verificare che nessun dettaglio implementativo delle librerie si propaghi oltre gli strati di integrazione.

---

# 4. Collaudo generale

Eseguire una verifica completa dei principali workflow:

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
* interruzione utente.

---

# 5. Documentazione

Aggiornare progressivamente:

* `DECISIONLOG`;
* documentazione dell'architettura;
* note progettuali;
* commenti dei principali moduli.

---

# Valutazioni future

Da riesaminare dopo il completamento del TPS:

* ottimizzazione del download;
* evoluzione di `caapi`;
* eventuale revisione del sistema di sessione;
* ulteriori semplificazioni dell'architettura interna.
