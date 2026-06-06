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

### Download

* [x] Download immagini
* [x] Download ugoira
* [x] Interruzione fetch tramite `Q`
* [x] Interruzione download tramite `Q`

### Bookmark

* [x] Analisi bookmark pubblici/privati
* [x] Rimozione conversione automatica a privato

### Analisi statistica Pixiv

* [x] Analisi completa distribuzione ID Pixiv
* [x] Regressione logaritmica densità HYPE
* [x] Definizione Bucketing System definitivo
* [x] Validazione Bucketing System tramite simulazioni (`bucks()`)

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

---

## Priorità immediata

### Nuovo Bucketing System

* [ ] Implementare nuovo `get_bucket()`
* [ ] Validare `create_dir()`
* [ ] Validare `save_index()`
* [ ] Validare `rebuild_index()`
* [ ] Validare `resume_pending_jobs()`
* [ ] Verificare compatibilità con archivi esistenti

---

## Robustezza e gestione errori

* [ ] Passare al setaccio tutta la gestione delle eccezioni
* [ ] Uniformare i messaggi di errore
* [ ] Individuare eccezioni non intercettate
* [ ] Verificare cleanup e rollback in caso di errore
* [ ] Verificare gestione errori filesystem

---

## Gestione limitazioni Pixiv

* [ ] Gestire l'interruzione causata dai rate limit Pixiv
* [ ] Salvare automaticamente lo stato in caso di limitazione
* [ ] Consentire resume dopo limitazione
* [ ] Distinguere errori temporanei da errori permanenti
* [ ] Migliorare riconoscimento risposte API anomale

---

## Menu e funzionalità

* [ ] Rifattorizzazione menu principale
* [ ] Completare menu conversione privacy bookmark
* [ ] Implementare `convert_bookmarks_to_private()`
* [ ] Aggiungere menu ricerca thumbnail
* [ ] Implementare logica ricerca thumbnail

---

## Validazione pratica

* [ ] Test reale download immagini
* [ ] Test reale download ugoira
* [ ] Test reale resume fetch
* [ ] Test reale resume download
* [ ] Test compatibilità nuovo Bucketing System

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

1. Nuovo Bucketing System
2. Gestione rate limit Pixiv
3. Revisione completa delle eccezioni
4. Completamento menu
5. Validazione resume e ugoira
6. ThreadPoolExecutor
