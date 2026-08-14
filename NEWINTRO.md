# PIXIV BULK DOWNLOADER — STATO DEL PROGETTO
## Riepilogo di passaggio — 12/08/2026

## 1. Stato generale

La sessione ha concluso un refactoring sostanziale della gestione dei metadata Pixiv e della struttura dell'archivio.

La nuova architettura stabilisce una separazione netta tra:

- scansione dei bookmark;
- acquisizione del metadata completo dell'opera;
- acquisizione del metadata dell'autore;
- rappresentazione tramite `PixivMetadata`;
- determinazione dei percorsi tramite `PixivPath`.

Il codice è stato modificato ma il nuovo flusso completo deve ancora essere sottoposto al test integrato finale.

---

# 2. Metadata artwork

## Situazione precedente

`retrieve_bookmarks()` utilizzava direttamente l'oggetto `illust` restituito da:

`user_bookmarks_illust()`

come metadata dell'opera.

Un confronto sperimentale tra:

- `user_bookmarks_illust()`;
- `illust_detail()`;

ha mostrato che i dati delle opere valide sono sostanzialmente equivalenti, salvo alcuni campi aggiuntivi presenti in `illust_detail()` relativi principalmente ai commenti.

È stato comunque deciso di utilizzare `illust_detail()` come sorgente canonica del metadata artwork completo.

## Nuovo flusso

L'oggetto `illust` proveniente dalla scansione dei bookmark viene utilizzato soltanto per ottenere l'ID dell'opera.

Per ogni opera viene quindi eseguita:

`caapi.illust_detail(illust.id)`

La risposta viene inserita in:

`artwork_data: PixivMetadata`

Da quel momento `artwork_data` è il metadata canonico dell'opera utilizzato dal resto della pipeline.

Il vecchio `image_data` non viene più costruito, perché sarebbe stato soltanto un contenitore temporaneo inutile.

---

# 3. Struttura definitiva del metadata artwork

È stato deciso di NON eliminare l'envelope `illust` restituito da Pixiv.

La struttura diventa quindi:

metadata
└── illust
    ├── id
    ├── title
    ├── type
    ├── user
    ├── tags
    ├── meta_pages
    └── ...

La scelta è intenzionale: `PixivMetadata` conserva il payload restituito da `illust_detail()` senza appiattirne artificialmente la struttura.

Gli accessor di `PixivMetadata` sono stati aggiornati di conseguenza.

Tra questi:

- `artw_id`
- `artw_title`
- `artw_type`
- `artw_get_links`
- `author_id`
- `author_name`

Per gestire la diversa posizione del blocco `user` nei metadata artwork e author è stato introdotto `_author_data`.

Per un artwork:

metadata
└── illust
    └── user

Per un author metadata:

metadata
└── user

`author_id` e `author_name()` utilizzano `_author_data` e non devono quindi conoscere direttamente la differenza strutturale.

---

# 4. Opere cancellate / autore ID 0

L'indagine sulle cosiddette "opere orfane" ha chiarito definitivamente il problema.

Le opere che nella lista bookmark risultavano associate a:

`author_id == 0`

non sono vere opere senza autore.

Sono opere eliminate da Pixiv.

Aprendo la relativa pagina Pixiv restituisce:

`Page not found`

Il test delle API ha mostrato che:

`user_bookmarks_illust()`

mantiene nella lista bookmark un oggetto degradato, con caratteristiche come:

- `user.id = 0`;
- titolo vuoto;
- `visible = false`;
- immagini placeholder;
- dimensioni 100×100;
- contatori azzerati.

Invece:

`illust_detail()`

restituisce direttamente una risposta contenente `error`.

La discriminante definitiva è quindi il metadata dell'opera, NON l'autore.

Il nuovo flusso è:

illust dalla lista bookmark
        ↓
illust_detail(id)
        ↓
artwork_data
        ↓
artwork_data.has_error?
        ↓
    sì → scarta opera
    no → continua

In questo modo un'opera cancellata viene eliminata dalla pipeline PRIMA di:

- recuperare il metadata autore;
- creare directory;
- creare checkpoint;
- aggiungerla alla lista dei download;
- scaricare media.

Di conseguenza non viene più effettuato `user_detail(0)`.

---

# 5. Metadata autore

Per ogni artwork valido viene eseguita:

`caapi.user_detail(artwork_data.author_id)`

e costruito:

`author_data: PixivMetadata`

Il metadata autore viene salvato separatamente dal metadata artwork.

La precedente protezione:

`author_data if not author_data.has_error else None`

è stata eliminata dal normale flusso.

Era stata introdotta principalmente per gestire `user_detail(0)` derivante dalle opere cancellate.

Poiché ora queste vengono intercettate prima attraverso `artwork_data.has_error`, quella protezione non è più necessaria per il caso che l'aveva originata.

---

# 6. PixivCallAPI

È stato aggiunto il wrapper per:

`illust_detail()`

seguendo lo stesso modello degli altri wrapper della classe.

La responsabilità di `PixivCallAPI` rimane invariata:

- interfaccia verso PixivPy3;
- normalizzazione/traduzione delle eccezioni previste.

NON deve interpretare semanticamente i payload Pixiv.

La distinzione tra metadata valido e risposta contenente errore rimane responsabilità di `PixivMetadata` e del livello chiamante.

---

# 7. Ugoira nel nuovo flusso

La verifica Ugoira viene ora effettuata sul metadata canonico:

`artwork_data.artw_is_ugoira`

Se necessario viene richiesto:

`ugoira_metadata()`

e il risultato viene aggiunto ad `artwork_data`.

Quindi anche la pipeline Ugoira utilizza ormai il metadata completo proveniente da `illust_detail()`.

---

# 8. Nuova struttura dell'archivio

La struttura definitiva è:

bookmarks/
└── <bucket primo livello>/
    └── <author_id>_<author_name>/
        └── <artwork_id>_<artwork_title>/

Il bucket viene calcolato tramite:

`author_id % 256`

`PixivPath.author_dir()` è ora responsabile esclusivamente di:

1. calcolare il bucket dell'autore;
2. costruire la directory autore.

`PixivPath.artwork_dir()` costruisce quindi la directory dell'opera sotto quella dell'autore.

---

# 9. Eliminato il bucketing di secondo livello

Il precedente sistema prevedeva un caso speciale per:

`author_id == 0`

con:

- `_SECOND_LEVEL_BUCKET_COUNT`;
- bucket derivato dall'ID dell'opera;
- directory `0_<bucket>`.

Tutta questa logica è stata eliminata.

Sono stati rimossi:

- `_SECOND_LEVEL_BUCKET_COUNT`;
- discriminazione `author_id == 0`;
- secondo `_get_bucket()`;
- directory `0_<bucket>`.

`PixivPath` non conosce più il concetto di opera cancellata.

Questo è intenzionale: la validità dell'opera viene stabilita prima, durante `retrieve_bookmarks()`.

---

# 10. Stato del porting storage/metadata

Dal punto di vista dell'implementazione il refactoring è sostanzialmente completo.

MANCA PERÒ IL TEST INTEGRATO.

Prima di considerare definitivamente chiuso il porting bisogna verificare:

- chiamata `illust_detail()` per ogni opera;
- corretta costruzione di `artwork_data`;
- corretto funzionamento degli accessor con `metadata["illust"]`;
- esclusione delle opere cancellate;
- assenza di `user_detail(0)`;
- corretta acquisizione del metadata autore;
- salvataggio artwork metadata;
- salvataggio author metadata;
- gestione Ugoira;
- struttura bucket → autore → opera;
- assenza della directory autore `0`;
- checkpoint;
- download effettivo dei media;
- assenza di regressioni.

Questo dovrebbe essere il PRIMO lavoro della prossima sessione.

---

# 11. Renderer — slot di stato / temporizzatore

È stata decisa una futura estensione del renderer.

Il renderer dovrà aggiungere una riga permanente IN FONDO alla lista degli slot dei worker.

Questa riga sarà uno:

`status slot`

Lo status slot sarà distinto dagli slot dei singoli thread.

Dovrà mostrare informazioni globali sull'esecuzione, a partire dal:

- tempo trascorso dall'inizio dell'operazione.

Concettualmente:

worker 1  [...]
worker 2  [...]
worker 3  [...]
...
----------------
status    elapsed: ...

Successivamente si potrà valutare quali altre informazioni globali mostrare.

Questa modifica NON è ancora implementata.

---

# 12. Ugoira — stato

La pipeline FFmpeg streaming è già stata integrata.

Protocollo Encoder:

`start()` → `add()` → `stop()`

Sono già stati implementati:

- streaming progressivo dei frame;
- gestione GIF;
- gestione WEBM;
- gestione MP4;
- validazione frame;
- apertura ZIP una sola volta;
- context manager dello ZIP;
- `AnimationError`;
- distinzione errori fatal/per-format;
- `stop(ignore_errors=True)`;
- recovery;
- integrazione renderer;
- integrazione `PBDError.notify()`;
- gestione checkpoint;
- gestione reale del rate limit durante il download.

Rimane da effettuare il test end-to-end finale della pipeline Ugoira:

- GIF;
- WEBM;
- MP4;
- renderer;
- messaggi finali;
- checkpoint;
- opere non-Ugoira.

---

# 13. Debug rapido / fault injection

È ancora da progettare e implementare un sistema semplice per provocare artificialmente gli errori nei diversi punti della pipeline.

Scopo:

evitare di dover riprodurre manualmente condizioni reali rare o difficili.

Dovrà permettere di testare rapidamente:

- frames non validi;
- frame mancante nello ZIP;
- ZIP mancante/corrotto;
- `archive.read()` fallita;
- avvio FFmpeg fallito;
- `Encoder.add()` fallita;
- FFmpeg con return code != 0;
- errori filesystem;
- errori API;
- rate limit;
- errori download;
- errori salvataggio;
- checkpoint;
- recovery;
- strategie Fatal / Retry / Continue / Rate Limit.

Questo sistema servirà soprattutto alla successiva revisione generale dell'error handling.

---

# 14. Refactoring generale error handling

Rimane uno dei principali lavori strutturali.

Da effettuare:

- audit completo della gerarchia `PBDError`;
- audit dei vecchi `PBDError.cast()`;
- sostituzione con `PBDError.hierarchy()` dove appropriato;
- revisione delle responsabilità dei vari livelli;
- eliminazione di traduzioni/intercettazioni duplicate;
- audit `base.py`;
- audit `retrieve_bookmarks()`;
- audit `download()`;
- audit pipeline Ugoira/Encoder;
- mappatura errori filesystem;
- mappatura errori API;
- revisione delle strategie:
  - Fatal;
  - Retry;
  - Continue;
  - Rate Limit;
- verifica sistematica dei checkpoint nei failure path.

---

# 15. Refactoring del flusso UI degli errori

Da riesaminare globalmente il modo in cui gli errori vengono presentati.

Principio già stabilito:

renderer
= stato operativo sintetico

storico console
= contesto + diagnosi persistente

`PBDError.notify()` è già stato introdotto e utilizzato nella pipeline concorrente, ma deve essere integrato sistematicamente nel resto dell'applicazione.

Da verificare:

- eliminazione messaggi duplicati;
- uniformità dei messaggi;
- colori;
- livello di dettaglio;
- errori provenienti dai worker;
- sospensione/ripristino renderer;
- integrazione con il futuro status slot.

---

# 16. Login / autenticazione

Il login necessita ancora di un refactoring dedicato.

Dovranno essere riesaminati:

- acquisizione credenziali/token;
- autenticazione;
- persistenza;
- refresh;
- gestione degli errori;
- rapporti tra login, configurazione e `PixivCallAPI`.

Esiste inoltre una questione specifica relativa a `my_gppt`.

In passato `my_gppt` è stata modificata localmente.

È stata avanzata l'ipotesi di:

1. ripristinare la versione originale di `my_gppt`;
2. adattare il codice di login PBD all'interfaccia originale;
3. evitare quindi, se possibile, di mantenere modifiche locali alla libreria.

La decisione definitiva richiede l'analisi del login attuale.

---

# 17. Dipendenze — decisione architetturale presa

È stata presa una decisione importante sulla conservazione delle dipendenze strategiche.

PBD NON dovrà necessariamente dipendere dall'esistenza futura dei relativi package/repository esterni.

L'intenzione è incorporare nel progetto almeno le dipendenze strategiche:

- `my_gppt`;
- `pixivpy3`.

Non come semplici snapshot inutilizzati, ma come codice effettivamente utilizzato dal progetto.

Possibile struttura:

src/
├── pbd/
│   └── ...
│
└── third_party/
    ├── my_gppt/
    └── pixivpy3/

oppure struttura equivalente da definire.

Obiettivo:

- il codice necessario a PBD rimane sotto il controllo del progetto;
- una futura scomparsa da PyPI/GitHub non rende impossibile ricostruire PBD;
- le versioni utilizzate sono versionate insieme al progetto;
- se PixivPy3 viene abbandonata, il codice rimane disponibile e modificabile localmente.

Va mantenuta una separazione netta tra codice PBD e codice third-party.

Per ogni dipendenza incorporata andranno conservati:

- licenza;
- versione upstream di origine;
- provenienza;
- eventuali modifiche locali.

Il problema della DISPONIBILITÀ futura della libreria viene così separato dal problema della COMPATIBILITÀ futura con Pixiv.

Se Pixiv cambierà API/autenticazione/protocollo, sarà un problema da affrontare quando accadrà.

---

# 18. Distribuzione

La strategia complessiva di distribuzione deve ancora essere discussa.

PyInstaller incorpora già nella build le dipendenze Python utilizzate al momento della compilazione.

Rimangono però da decidere:

- struttura definitiva delle dipendenze incorporate nel repository;
- sorgente Python;
- EXE standalone;
- eventuale package installabile;
- eventuale pubblicazione PyPI;
- gestione FFmpeg;
- riproducibilità delle build;
- separazione dipendenze runtime/development;
- comportamento in ambiente pulito.

La discussione sulle dipendenze NON deve quindi essere ridotta a un semplice `requirements.txt`: riguarda anche la conservazione a lungo termine del progetto.

---

# 19. Archivio locale

Non esiste ancora un archivio locale definitivo da migrare.

Di conseguenza:

NON È PREVISTA ALCUNA MIGRAZIONE DELL'ARCHIVIO.

Il nuovo sistema bucket → autore → opera verrà utilizzato direttamente per la costruzione del futuro archivio.

---

# 20. Ordine di lavoro consigliato

### Immediato

1. Test integrato del nuovo sistema metadata/storage.
2. Correzione di eventuali regressioni emerse dal test.

### Breve termine

3. Implementazione status slot / temporizzatore nel renderer.
4. Test end-to-end Ugoira.
5. Implementazione debug rapido / fault injection.

### Medio termine

6. Refactoring generale error handling.
7. Refactoring del flusso UI degli errori.
8. Refactoring login/autenticazione.
9. Ripristino, se possibile, dell'interfaccia originale di `my_gppt`.

### Medio/lungo termine

10. Integrazione locale delle dipendenze strategiche (`my_gppt`, `pixivpy3`).
11. Audit generale delle dipendenze.
12. Definizione della strategia di distribuzione.
13. Revisione packaging/PyInstaller.
14. Eventuale preparazione alla distribuzione pubblica/PyPI.

---

# 21. Punto esatto da cui ripartire

La prossima sessione dovrebbe iniziare dal TEST.

Il codice appena modificato introduce contemporaneamente:

- `illust_detail()` come fonte canonica;
- nuovo envelope `metadata["illust"]`;
- nuovi accessor `PixivMetadata`;
- metadata autore;
- esclusione preventiva delle opere cancellate;
- nuova struttura storage;
- eliminazione completa del secondo livello di bucketing.

Prima di iniziare altri refactoring è opportuno verificare che l'intera pipeline funzioni realmente end-to-end.

Se il test passa, il porting metadata/storage può essere considerato definitivamente concluso e si può passare allo status slot del renderer.