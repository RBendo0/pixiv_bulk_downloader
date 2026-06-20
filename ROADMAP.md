# Pixiv Bulk Downloader

## Milestone corrente

**BETA PRE THREAD**

---

## Priorità 1 - Completamento UI

### Migrazione moduli

* [ ] Migrare `bookmarks.py` verso `ui.message()`
* [ ] Migrare `base.py` verso `ui.message()`
* [ ] Eliminare output legacy residui

---

## Priorità 2 - Gestione errori

### Audit retrieve_bookmarks()

* [ ] Mappare tutte le chiamate API
* [ ] Mappare tutti gli accessi JSON
* [ ] Mappare tutti i punti di salvataggio
* [ ] Individuare eccezioni non intercettate
* [ ] Classificare errori livello pagina
* [ ] Classificare errori livello opera

### Audit download()

* [ ] Mappare tutte le operazioni filesystem
* [ ] Mappare tutti i download
* [ ] Individuare eccezioni non intercettate
* [ ] Classificare errori filesystem

### Definizione strategie di gestione

* [ ] Fatal
* [ ] Abort / Retry
* [ ] Abort / Retry / Continue
* [ ] Rate Limit

### Eccezioni

* [ ] Completare utilizzo di `PixivApiError`
* [ ] Completare utilizzo di `StorageError`
* [ ] Uniformare i menu di errore
* [ ] Revisione rete di sicurezza globale (`main.py`)

---

## Priorità 3 - Test

### Test eccezioni

* [ ] Simulare `PixivApiError`
* [ ] Simulare `StorageError`
* [ ] Simulare errori filesystem
* [ ] Simulare rate limit

### Test funzionali

* [ ] Verificare fetch bookmark
* [ ] Verificare resume fetch
* [ ] Verificare download immagini
* [ ] Verificare download ugoira
* [ ] Verificare rebuild index

---

## Priorità 4 - Compatibilità archivi

* [ ] Verificare archivi pre-bucketing
* [ ] Verificare archivi bucket legacy
* [ ] Verificare archivi correnti
* [ ] Valutare eventuale migrazione

---

## Priorità 5 - Funzionalità mancanti

### Bookmark Privacy

* [ ] Completare menu conversione privacy
* [ ] Implementare `convert_bookmarks_to_private()`

### Thumbnail Search

* [ ] Aggiungere voce di menu
* [ ] Implementare ricerca thumbnail

---

## Priorità 6 - Thread Release

* [ ] Introduzione `ThreadPoolExecutor`
* [ ] Download parallelo immagini
* [ ] Download parallelo ugoira
* [ ] Gestione abort con thread
* [ ] Gestione resume con thread
* [ ] Verifica race condition filesystem

---

## Ordine di lavoro

1. Migrazione `bookmarks.py`
2. Migrazione `base.py`
3. Audit `retrieve_bookmarks()`
4. Audit `download()`
5. Gestione errori
6. Test eccezioni
7. Compatibilità archivi
8. Bookmark Privacy
9. Thumbnail Search
10. Thread Release

## Funzionalità future

### Refresh Metadata

- [ ] Aggiornamento metadata da Pixiv
- [ ] Timestamp ultimo aggiornamento
- [ ] Refresh selettivo
- [ ] Refresh archivio completo
- [ ] Rilevazione opere eliminate/private
- [ ] Aggiornamento con rispetto del rate limit