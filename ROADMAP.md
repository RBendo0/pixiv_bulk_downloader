# ROADMAP – Pixiv Bulk Downloader

## 1. ERRS – Error Recovery System

* Completare l'implementazione dei metodi `handle()`.
* Definire la convenzione di recovery (Abort / Retry / Continue).
* Integrare il menu ARC nel sistema a classi.
* Portare gradualmente tutti i blocchi `except` sotto `PBDError`.
* Eliminare la gestione errori duplicata dai moduli.

## 2. Refactoring dei moduli

Analizzare e migrare progressivamente:

* `main.py`
* `bookmarks.py`
* `base.py`

Obiettivi:

* utilizzo sistematico di `caapi`;
* utilizzo sistematico di `PBDError`;
* centralizzazione della recovery policy.

## 3. Download subsystem

* Rifattorizzazione del flusso download.
* Integrazione completa di `DownloadRateLimitError`.
* Conservazione dei pending jobs e dei checkpoint.
* Verifica della politica Retry / Skip / Abort.

## 4. Thread Pool System (TPS)

Implementazione successiva al completamento di ERRS e Download.

Obiettivi:

* parallelizzare esclusivamente il download;
* mantenere seriale il fetch dei bookmark;
* garantire recovery e checkpoint consistenti;
* definire il comportamento dei worker in caso di errore.

## 5. Valutazioni future

* Evoluzione di `RecoveryAction`.
* Possibile sostituzione di `ContinueShortcut`.
* Eventuale introduzione di policy di recovery più sofisticate.
* Eventuale eliminazione di `GenericOperationError` se ritenuto ridondante.
