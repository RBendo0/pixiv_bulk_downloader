# ROADMAP – Pixiv Bulk Downloader

## 1. ERRS – Error Recovery System

Stato attuale:

* definita la gerarchia `PBDError`;
* introdotti `PBDError.cast()` e `PBDError.hierarchy()`;
* introdotto `PageNotFoundError`;
* introdotta la distinzione tra errori generici e `RateLimitError`;
* introdotto `RecoveryControl.Action`;
* `PBDError.handle()` implementa il menu ARC;
* `RateLimitError.handle()` implementa `wait_rate_limit()`.

Da completare:

* migrare progressivamente tutti i blocchi `except`;
* portare il porting di `base.py`;
* eliminare `ContinueShortcut`;
* valutare l'introduzione delle control exception (`Abort`, `Retry`, `Continue`) nel flusso di esecuzione;
* completare l'inventario degli use case prima di stabilizzare definitivamente ERRS.

## 2. `bookmarks.py`

### `retrieve_bookmarks()`

Stato attuale:

* flusso paginazione normalizzato;
* eliminato `next_json`;
* eliminato il look-ahead della modalità `chrono`;
* `res_json` rappresenta nuovamente la pagina corrente;
* `chrono` termina al primo artwork già presente in locale;
* il blocco fetch pagina è ora compatibile con la futura gestione ERRS.

Da fare:

* riallineare `RateLimitError` ad `ApiRateLimitError`;
* convertire i blocchi `except` al modello `PBDError.cast()` / `PBDError.hierarchy()`.
* applicare `handle()` e `RecoveryAction`;
* rivalutare l'utilità di `page_number`.

### `add_list_to_bookmarks()`

Da riprogettare prima del porting ERRS.

Nuove funzionalità previste:

* aggiungere un menu per scegliere la privacy:
  * pubblico;
  * privato.
* rendere il file lista una coda persistente di lavoro:
  * gli URL processati vengono rimossi;
  * il file rimane esistente anche se vuoto.
* introdurre interruzione utente durante il processo.
* produrre file separati per gli esiti non completati:
  * fallimenti retryable;
  * opere rimosse / non disponibili.
* classificare il payload API:
  * `error.user_message == "Page not found"`
  * come errore definitivo, non retryable.

## 3. Refactoring dei moduli

Analizzare e migrare progressivamente:

* `main.py`
* `bookmarks.py`
* `base.py`

Obiettivi:

* utilizzo sistematico di `caapi`;
* utilizzo sistematico di `PBDError`;
* centralizzazione della recovery policy.

## 4. Download subsystem

* Rifattorizzazione del flusso download.
* Integrazione completa di `DownloadRateLimitError`.
* Conservazione dei pending jobs e dei checkpoint.
* Verifica della politica Retry / Skip / Abort.

## 5. Thread Pool System (TPS)

Implementazione successiva al completamento di ERRS e Download.

Obiettivi:

* parallelizzare esclusivamente il download;
* mantenere seriale il fetch dei bookmark;
* garantire recovery e checkpoint consistenti;
* definire il comportamento dei worker in caso di errore.

## 6. Valutazioni future

* Evoluzione di `RecoveryAction`.
* Possibile sostituzione di `ContinueShortcut`.
* Eventuale introduzione di policy di recovery più sofisticate.
* Eventuale eliminazione di `GenericOperationError` se ritenuto ridondante.