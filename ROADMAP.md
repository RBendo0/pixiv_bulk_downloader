# ROADMAP – Pixiv Bulk Downloader

## Stato architetturale

È stata completata una nuova milestone strutturale del progetto.

### ERRS

L’architettura ERRS è stata stabilizzata.

Responsabilità attuali:

* le classi derivate da `PBDError` classificano gli errori;
* `PBDError.info()` descrive sinteticamente la categoria dell’errore;
* `PBDError.cast()` normalizza genericamente le eccezioni;
* `PBDError.hierarchy()` preserva le categorie specializzate;
* `RecoveryControl` contiene le strategie comuni di recupero:

  * `wait_rate_limit()`;
  * `prompt_error_menu()`;
  * `Action`;
  * control exception.

I workflow mantengono la responsabilità di scegliere la strategia di recovery adatta al proprio contesto.

### Interfacce applicative

I principali sottosistemi unici dell’applicazione sono ora esposti tramite alias di classe:

```python
ui
rcc
caapi
pbd
```

Questi componenti sono trattati come interfacce e controller unici del sistema, non come oggetti replicabili.

### `caapi`

`caapi` è diventato l’unica interfaccia verso Pixiv e verso il sistema di autenticazione.

Responsabilità attuali:

* apertura della sessione tramite `open_session()`;
* conservazione interna di:

  * `AppPixivAPI`;
  * `LoginInfo`;
* integrazione di `PixivAuth`;
* esecuzione delle chiamate API;
* traduzione delle eccezioni esterne;
* gestione distinta delle chiamate:

  * API;
  * download;
  * autenticazione.

I moduli applicativi non ricevono e non conservano più `aapi` o `login_info`.

### Downloader

`PixivBaseDownloader` e `PixivBookmarksDownloader` non possiedono più stato di istanza.

I loro metodi sono esposti come metodi di classe e il downloader principale è disponibile tramite:

```python
pbd
```

Il `main` si limita ora a:

```python
caapi.open_session()
interact()
```

### UI

I messaggi conclusivi dei principali workflow sono stati normalizzati.

Sono stati introdotti messaggi specifici per:

* completamento naturale del fetching;
* interruzione del fetching;
* conclusione della modalità `chrono`;
* completamento del download;
* interruzione del download;
* completamento dell’aggiunta dei bookmark.

Il generico `Finish!` del dispatcher principale è stato eliminato.

---

## 1. `add_list_to_bookmarks()`

Questa è la prossima revisione principale.

Il metodo deve diventare il gestore di una coda persistente di URL.

### Coda principale

File:

```text
pending_urls.txt
```

Comportamento previsto:

* contiene gli URL ancora da elaborare;
* ogni URL completato con successo viene rimosso;
* il file rimane presente anche quando la coda è vuota;
* gli errori temporanei lasciano l’URL nella coda;
* la coda deve essere aggiornata prima di passare all’URL successivo.

### URL non disponibili

File:

```text
not_found_urls.txt
```

Comportamento previsto:

* riceve gli URL che producono `PageNotFoundError`;
* tali URL vengono rimossi definitivamente dalla coda principale;
* il file conserva lo storico delle opere rimosse o non più disponibili.

### Privacy

Aggiungere un menu iniziale per scegliere:

* bookmark pubblico;
* bookmark privato.

La scelta deve essere applicata a tutta la coda elaborata nella singola esecuzione.

### Interruzione utente

Introdurre `InputPending` per consentire l’interruzione tramite `Q`.

L’interruzione deve avvenire tra un URL e il successivo, dopo aver persistito l’esito dell’URL appena elaborato.

### Gestione degli errori

Distinguere almeno:

* `PageNotFoundError`

  * errore definitivo;
  * spostamento in `not_found_urls.txt`;

* `ApiRateLimitError`

  * attesa e retry;
  * possibilità di abort;

* `ApiError` e altri errori temporanei

  * menu di recovery;
  * conservazione dell’URL nella coda in caso di uscita o fallimento non risolto;

* URL non validi

  * definire se rimuoverli dalla coda;
  * definire se conservarli in un file separato o includerli nella reportistica.

### Reportistica finale

Il riepilogo dovrà distinguere almeno:

* bookmark aggiunti;
* URL non validi;
* opere non disponibili;
* errori temporanei;
* URL ancora presenti nella coda.

---

## 2. Verifica della nuova architettura `caapi`

Completare il collaudo dei workflow dopo l’internalizzazione della sessione.

Verificare:

* login;
* fetching completo;
* fetching interrotto;
* modalità `chrono`;
* download di illustrazioni singole;
* download multipagina;
* download ugoira;
* rate limit API;
* rate limit download;
* `resume_pending_jobs()`;
* aggiunta bookmark;
* refresh della sessione, quando applicabile.

Valutare successivamente se `_aapi()` debba rimanere una semplice interfaccia tipologica o acquisire una validazione esplicita dello stato della sessione.

---

## 3. Pulizia architetturale

Dopo il completamento di `add_list_to_bookmarks()`:

* verificare gli import e la direzione delle dipendenze;
* rimuovere import, costanti e metodi non più utilizzati;
* controllare la coerenza degli alias di classe;
* aggiornare `DECISIONLOG`;
* verificare che nessun modulo applicativo acceda direttamente alle librerie esterne;
* verificare che non rimangano riferimenti obsoleti a:

  * `self.aapi`;
  * `self.login_info`;
  * istanze del downloader.

---

## 4. Download subsystem

Dopo la stabilizzazione della coda bookmark:

* verificare la conservazione dei checkpoint in tutti i casi di errore;
* riesaminare la politica Retry / Continue / Abort;
* verificare il comportamento delle opere multipagina;
* verificare il recupero delle ugoira;
* valutare eventuali semplificazioni residue nel flusso di download.

---

## 5. Thread Pool System – TPS

L’implementazione del TPS rimane successiva alla completa stabilizzazione dei workflow seriali.

Obiettivi:

* parallelizzare esclusivamente il download;
* mantenere seriale il fetching dei bookmark;
* preservare checkpoint e recovery;
* definire il comportamento dei worker in caso di errore;
* coordinare rate limit e interruzione utente;
* evitare che più worker modifichino contemporaneamente lo stesso stato persistente.

---

## 6. Valutazioni future

* gestione esplicita dello stato della sessione in `caapi`;
* eventuale revisione di `refresh()`;
* possibile introduzione di ulteriori interfacce interne per l’accesso alla sessione;
* evoluzione della reportistica della coda persistente;
* revisione finale delle control exception;
* eventuale ripresa del TPS dopo un periodo di collaudo della versione seriale.
