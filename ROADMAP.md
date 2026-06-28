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

# ROADMAP

## Gestione errori e resilienza

- [x] Porting completo del sottosistema UI in `base.py`
- [x] Introduzione di `DownloadRateLimitError`
- [x] Normalizzazione di `RemoteDisconnected`
- [x] Gestione del rate limit nei download con retry e possibilità di interruzione
- [x] Introduzione di `ContinueShortcut` per il controllo del flusso
- [x] Separazione della gestione errori tra:
  - metadata opera
  - metadata ugoira
  - download dei singoli file
- [x] Preservazione automatica dei checkpoint in caso di download incompleto

## Da completare

- [ ] Rifinire le routine rimanenti di `base.py`
- [ ] Porting UI di `rebuild_index()` e `resume_pending_jobs()`
- [ ] Rifattorizzare la gestione errori tramite metodi virtuali
- [ ] Progettare l'architettura del Thread Pool System (TPS)
- [ ] Definire il coordinamento dei worker in presenza di `DownloadRateLimitError`
- [ ] Definire il modello di completamento di un'opera nel TPS
- [ ] Rivalutare l'architettura fetch/download dopo i test sul TPS