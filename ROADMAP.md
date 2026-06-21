# Pixiv Bulk Downloader - Roadmap

## Priorità 1 - Completamento UI

### Completato

- Implementata ui.line()
- Eliminata ui.message()
- Implementato supporto:
  - history
  - home
  - clear
  - colori
- Implementato sistema pending
- Integrato winsound.MessageBeep()
- Integrato menu()
- Integrato main_menu()
- Implementata cancellazione menu tramite clear=True
- Completata migrazione main.py
- Completata migrazione interact() in bookmarks.py

### Da completare

- Migrare prompt_error_menu()
- Migrare wait_rate_limit()
- Migrare retrieve_bookmarks()
- Migrare base.py
- Eliminare output legacy residui

### Test

- Verificare menu temporanei
- Verificare countdown rate limit
- Verificare gestione CTRL+C
- Individuare e correggere bug UI residui

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