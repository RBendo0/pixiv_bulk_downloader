# Pixiv Bulk Downloader

## Stato attuale

**Milestone corrente:** BETA PRE THREAD

---

## Completato

### Architettura dati

* [x] Introduzione `PixivMetadata`
* [x] Eliminazione dipendenza da `IllustInfo`
* [x] Eliminazione completa di `UserInfo`
* [x] Eliminazione di `NextBookmarksRequest`
* [x] Eliminazione di `NextFollowingsRequest`
* [x] Pulizia export package (`__init__.py`)

### Struttura progetto

* [x] Nuova struttura cartelle
* [x] Supporto esecuzione tramite `pbd`
* [x] Supporto esecuzione tramite `python -m pixiv_bulk_downloader`
* [x] Uniformazione codifica UTF-8

### Resume e checkpoint

* [x] Checkpoint `fetch.json`
* [x] Resume infrastrutturale
* [x] Ripristino lavori tramite `resume_pending_jobs()`
* [x] Ricostruzione indice tramite `rebuild_index()`

### Download

* [x] Download immagini
* [x] Download ugoira
* [x] Interruzione fetch tramite `Q`
* [x] Interruzione download tramite `Q`
* [x] Conservazione checkpoint in caso di download fallito
* [x] Conservazione cartelle parziali in caso di download fallito

### Bookmark

* [x] Analisi bookmark pubblici/privati
* [x] Rimozione conversione automatica a privato

### Analisi statistica Pixiv

* [x] Analisi completa distribuzione ID Pixiv
* [x] Regressione logaritmica densità HYPE
* [x] Definizione Bucketing System definitivo
* [x] Validazione Bucketing System tramite simulazioni (`bucks()`)
* [x] Introduzione classe `PixivPath` derivata da `pathlib.Path`
* [x] Implementazione Bucketing System in `PixivPath`
* [x] Implementazione bucket HYPE/STABLE
* [x] Implementazione `work_dir()`
* [x] Validazione generazione percorsi bucket-aware

---

## Bucketing System definitivo (congelato)

### Principi

* Separazione netta tra zona HYPE e zona STABLE
* Nessuna transizione continua tra le due regioni
* Presenza di una vera e propria "ghigliottina" tra i modelli
* Bucketing a densità variabile validato tramite simulazioni
* Modello considerato definitivo salvo bug implementativi

### Decisioni progettuali

* Scartato utilizzo diretto dell'inversa della regressione logaritmica
* Mantenuta separazione concettuale HYPE/STABLE
* Bucketing ricostruibile direttamente dall'ID
* Incapsulamento completo del Bucketing System in `PixivPath`
* Gestione bucket trasparente ai chiamanti

---

## Priorità immediata

### Integrazione Bucketing System

* [x] Implementazione Bucketing System in `PixivPath`
* [x] Implementazione HYPE/STABLE bucket calculation
* [x] Implementazione `work_dir()`
* [x] Validazione generazione percorsi bucket-aware
* [x] Sostituzione `create_dir()`
* [x] Eliminazione `get_bucket()`
* [x] Integrazione in `base.py`

### Validazione Bucketing System

* [x] Test reale fetch bookmark
* [x] Test reale download immagini
* [x] Test reale download ugoira
* [x] Test reale resume fetch
* [x] Verifica eliminazione checkpoint fetch
* [x] Verifica ricostruzione indice (`rebuild_index()`)
* [ ] Verifica compatibilità archivi esistenti
* [x] Verifica creazione automatica bucket HYPE
* [x] Verifica creazione automatica bucket STABLE

### Robustezza

* [ ] Revisione completa gestione eccezioni
* [x] Download resiliente agli errori
* [ ] Gestione errori `retrieve_bookmarks()`
* [ ] Definire comportamento in caso di errore API durante il fetch
* [ ] Uniformazione messaggi di errore
* [ ] Individuazione eccezioni non intercettate
* [ ] Revisione gestione eccezioni globale (`main`)
* [ ] Verifica rollback e cleanup filesystem

### Rate Limit Pixiv

* [ ] Determinare comportamento reale del rate limit
* [ ] Verificare se PixivPy3 genera `PixivError`
* [ ] Verificare eventuali risposte JSON inattese
* [ ] Gestire interruzione causata dai rate limit
* [ ] Salvare automaticamente lo stato
* [ ] Consentire resume dopo limitazione
* [ ] Distinguere errori temporanei da permanenti

### Menu e funzionalità

* [ ] Completare menu conversione privacy bookmark
* [ ] Implementare `convert_bookmarks_to_private()`
* [ ] Aggiungere menu ricerca thumbnail
* [ ] Implementare logica ricerca thumbnail

---

## Thread Release

* [ ] Introduzione `ThreadPoolExecutor`
* [ ] Download parallelo immagini
* [ ] Download parallelo ugoira
* [ ] Gestione abort con thread
* [ ] Gestione resume con thread
* [ ] Verifica race condition filesystem

---

## Miglioramenti futuri

* [ ] Logging persistente
* [ ] Configurazione tramite file `.json` o `.toml`
* [ ] Progress bar avanzata
* [ ] Retry automatico download falliti
* [ ] Verifica integrità download
* [ ] Validazione Bucketing System oltre dataset storico (`ID_MAX`)

---

## Milestone

```text
BETA PRE THREAD
        ↓
RELEASE PRE THREAD
        ↓
THREAD RELEASE
```

---

## Priorità operative attuali

1. Gestione errori `retrieve_bookmarks()`
2. Revisione gestione eccezioni globale (`main`)
3. Gestione rate limit Pixiv
4. Completamento menu privacy bookmark
5. Thumbnail search
6. ThreadPoolExecutor

---

## Note progettuali

### Gestione eccezioni

* `main()` deve rimanere una rete di sicurezza globale.
* La logica di interpretazione degli errori deve essere il più possibile vicina alle chiamate API.
* `retrieve_bookmarks()` è attualmente il principale punto da irrobustire.
* Un errore API durante `retrieve_bookmarks()` termina l'esecuzione del programma.

### Domanda aperta

Definire il comportamento corretto quando una chiamata Pixiv API fallisce durante `retrieve_bookmarks()`:

* Tornare al menu?
* Terminare il programma?
* Consentire il resume?
* Effettuare retry automatici?
* Distinguere errori temporanei da permanenti?