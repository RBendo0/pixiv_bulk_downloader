# Pixiv Bulk Downloader - Roadmap

## Priorità 1 - Completamento UI

### Test e validazione

- Verificare menu temporanei
- Verificare messaggi temporanei
- Verificare input_key()
- Verificare clear(keep)
- Verificare gestione CTRL+C
- Individuare e correggere bug UI residui

### Migrazione

- Migrare bookmarks.py verso ui.message()
- Migrare base.py verso ui.message()
- Eliminare output legacy residui

---

## Priorità 2 - Gestione errori

### Audit retrieve_bookmarks()

- Mappare chiamate API
- Mappare accessi JSON
- Mappare punti di salvataggio
- Individuare eccezioni non intercettate

### Audit download()

- Mappare operazioni filesystem
- Mappare download
- Individuare eccezioni non intercettate

### Classificazione errori

- Fatal
- Abort / Retry
- Abort / Retry / Continue
- Rate Limit

---

## Priorità 3 - Test

### Simulazioni

- PixivApiError
- StorageError
- Errori filesystem
- Rate limit

### Compatibilità archivi

- Archivi pre-bucketing
- Archivi bucket legacy
- Archivi correnti

---

## Priorità 4 - Funzionalità mancanti

- Bookmark Privacy
- Thumbnail Search

---

## Priorità 5 - Thread Release

- ThreadPoolExecutor
- Download paralleli
- Resume thread-safe
- Abort thread-safe