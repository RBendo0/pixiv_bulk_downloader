# Pixiv Bulk Downloader - Roadmap

## Priorità 1 - Stabilizzazione UI

### Completare

* Migrare `base.py`
* Eliminare output legacy residui (`print`)
* Verificare tutti gli usi specializzati di `ui.line()`
* Audit completo dei messaggi temporanei
* Verificare uniformità di menu e prompt
* Eseguire test end-to-end della nuova UI
* Individuare e correggere bug UI residui

### Test

* Menu temporanei
* Countdown rate limit
* Gestione CTRL+C
* `InputPending`
* Gestione delle righe temporanee

---

## Priorità 2 - Gestione errori

### Audit

* Mappare operazioni filesystem in `download()`
* Mappare punti di download
* Individuare eccezioni non intercettate
* Classificare i punti di recovery

### Refactoring `pixiv_errors.py`

* Introdurre gestione polimorfica degli errori tramite metodi virtuali
* Centralizzare:

  * menu di errore;
  * azioni consentite;
  * azione di default;
  * messaggi di resume/interruzione;
  * logica `Abort / Retry / Continue`
* Ridurre il codice duplicato nei moduli chiamanti
* Valutare eventuale macchina a stati per i flussi di recovery

### Classificazione errori

* Fatal
* Abort / Retry
* Abort / Retry / Continue
* Rate Limit

---

## Priorità 3 - Test

### Simulazioni

* PixivApiError
* StorageError
* Errori filesystem
* Rate limit

### Compatibilità archivi

* Archivi pre-bucketing
* Archivi bucket legacy
* Archivi correnti

---

## Priorità 4 - Funzionalità mancanti

* Bookmark Privacy
* Thumbnail Search

---

## Priorità 5 - Thread Release

* ThreadPoolExecutor
* Download paralleli
* Resume thread-safe
* Abort thread-safe
