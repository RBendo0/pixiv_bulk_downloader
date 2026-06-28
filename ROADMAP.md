# Pixiv Bulk Downloader - Roadmap

## Stato attuale

Completato il porting del sottosistema UI e della gestione errori nelle routine principali.

La CLI usa ora in modo coerente:

- `ui.line()`
- `ui.menu()`
- `ui.input_key()`
- `ui.confirm()`
- `ui.poll_key()`
- `InputPending`

Sono stati completati:

- download interattivo dei pending jobs;
- resume dei pending jobs;
- rebuild index;
- gestione rate limit;
- preservazione checkpoint;
- gestione errori con menu Abort / Retry / Continue;
- distinzione tra righe di progresso e storico console.

---

## Priorità 1 - Refactoring `pixiv_errors.py`

Obiettivo: trasformare `pixiv_errors.py` nel centro della politica di recovery.

### Da progettare

- Gerarchia definitiva degli errori.
- Metodi virtuali per la gestione degli errori.
- Centralizzazione dei menu di recovery.
- Centralizzazione dei messaggi utente.
- Centralizzazione della logica:
  - Abort;
  - Retry;
  - Continue;
  - Rate limit wait;
  - Resume;
  - Checkpoint preservation.
- Riduzione della duplicazione in `base.py` e `bookmarks.py`.
- Valutazione di una piccola macchina a stati per i flussi di recovery.

### Classi / concetti da valutare

- `PixivDownloaderError`
- `PixivApiError`
- `RateLimitError`
- `DownloadRateLimitError`
- `StorageError`
- `ContinueShortcut`
- `RecoveryAction`
- `RecoveryPolicy`

---

## Priorità 2 - Refactoring del download

Obiettivo: preparare `download()` al futuro Thread Pool System senza introdurre ancora concorrenza.

### Da fare

- Separare meglio le fasi logiche:
  - preparazione opera;
  - metadata ugoira;
  - serializzazione metadata;
  - download file;
  - completamento opera;
  - gestione checkpoint.
- Ridurre i blocchi `try/except` duplicati.
- Delegare a `pixiv_errors.py` la scelta della recovery.
- Rendere più esplicito il concetto di pending job.
- Chiarire la semantica di opera completa / opera incompleta.

---

## Priorità 3 - Thread Pool System

Il TPS verrà implementato solo nella fase di download.

`retrieve_bookmarks()` rimane seriale, perché i test hanno mostrato che il fetch API è già sufficientemente veloce.

Architettura confermata:

```text
retrieve completo
    ↓
lista pending jobs
    ↓
download completo