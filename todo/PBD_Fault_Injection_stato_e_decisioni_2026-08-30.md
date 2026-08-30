# PBD — Stato Simulation, Debug Trace Binding e Fault Injection

## Punto di ripartenza

Questo documento riassume lo stato raggiunto nello sviluppo dell'infrastruttura di test di **Pixiv Bulk Downloader (PBD)** e raccoglie soprattutto le decisioni emerse prima dell'implementazione del Fault Injection vero e proprio.

```text
Simulation                  ✓
Debug Trace Binding (DTB)   ✓
Fault Injection             ← prossimo passo
```

## 1. Architettura generale del Debug

La vecchia idea di una singola modalità `testing` è stata superata. Sono stati separati tre concetti:

```text
Debug
├── Simulation
└── Fault Injection
```

`Debug` è lo stato generale. `Simulation` e `Fault Injection` sono funzionalità distinte, entrambe subordinate all'attivazione di Debug.

L'interfaccia attuale comprende:

```python
debug.enabled()
debug.simulation()
debug.fault_injection()
```

### Dipendenza tra Fault Injection e Simulation

È stata valutata la possibilità di subordinare Fault Injection anche a Simulation. Per il momento questa soluzione è stata scartata.

Simulation decide se determinate operazioni costose vengono realmente eseguite; Fault Injection decide se vengono deliberatamente provocati dei fallimenti. La combinazione normalmente più utile sarà probabilmente `Debug = True`, `Simulation = True`, `Fault Injection = True`, ma deve rimanere possibile usare Fault Injection con Simulation disattivata.

**Decisione attuale:** Fault Injection rimane indipendente da Simulation e dipende soltanto da Debug.

## 2. Simulation — conclusa

La Simulation è implementata e verificata. Il principio adottato è mantenere reale tutto ciò che interessa verificare e simulare soltanto le operazioni pesanti.

Restano reali Pixiv, API, metadata, costruzione dei job, filesystem, renderer, gestione errori e recovery. Vengono simulate le operazioni multimediali costose.

### Immagini statiche

Il download effettivo viene intercettato nel downloader. In Simulation non viene trasferito il media e viene introdotto un ritardo artificiale.

### Ugoira

È stato introdotto `DebuggedZipFile`. Lo ZIP non viene realmente scaricato; la struttura dei frame continua però a derivare dai metadata reali.

### Encoder

Il refactoring dell'encoder ha prodotto:

```text
animation
    ↓
Encoder
    ↓
DebuggedFFmpegProcess
    ↓
FFmpeg
```

`DebuggedFFmpegProcess` espone l'interfaccia specializzata `write(data)`, `close_input()`, `abort()`, `wait() -> MediaToolResult`. In Simulation FFmpeg non viene realmente eseguito.

### Filesystem

Il filesystem rimane intenzionalmente reale. I bookmark della Simulation vengono deviati sotto `<default_root>\debug\bookmarks`. La Simulation completa senza fault è stata provata con successo.

## 3. Debug Trace Binding — concluso

Il DTB permette di seguire un'eccezione provocata artificialmente attraverso PBD.

È contenuto in `Debug.DTB` e offre:

```python
debug.DTB.register(...)
debug.DTB.inherit(...)
debug.DTB.error_info(...)
```

### Binding

L'implementazione attuale di `register()` genera ancora un Debug ID progressivo e associa all'istanza dell'eccezione una stringa diagnostica tramite l'attributo privato `_debug_info`.

La discussione successiva sul logging persistente ha però portato a una nuova decisione architetturale: **il Debug ID progressivo verrà sostituito da un timestamp generato al momento della registrazione**.

Il timestamp avrà un doppio ruolo:

- identificare temporalmente l'evento di Debug/Fault Injection;
- correlare tutte le registrazioni successive che derivano dalla stessa eccezione.

Il principio del DTB non cambia: il binding continua ad appartenere a Debug e continua a seguire l'eccezione attraverso `inherit()`. Cambia soltanto l'identificatore usato dal binding.

Il messaggio associato rimane **libero**, senza struttura obbligatoria o campi semantici predefiniti. L'unico dato strutturato aggiuntivo previsto, quando disponibile, è l'ID dell'opera interessata (`artwork_id`), necessario per le analisi successive dell'archivio e del checkpoint.

### Propagazione

Quando PBD traduce un'eccezione in una nuova istanza, il DTB viene trasferito mediante `debug.DTB.inherit(new_error, old_error)`. Il meccanismo è stato applicato a `PBDError.hierarchy()`, `PBDError.cast()`, `ConfigError.hierarchy()`, `MediaToolExecutableError.hierarchy()` ed `EncoderStreamError.hierarchy()`.

### Osservazione finale

`PBDError.notify()` rimane il punto finale di osservazione del normale sistema errori.

Con la futura conversione al timestamp, la diagnostica potrà assumere indicativamente una forma del tipo:

```text
[#]: 2026-08-30T12:54:31.481234: ...
[!]: normale messaggio PBD
```

La presenza della riga continua a essere determinata esplicitamente tramite `if debug.enabled()` e non attraverso la truthiness del risultato di `error_info()`.

Il colore Debug dedicato rimane arancione e `tag_color=ui.COLOR_DEFAULT` resta disponibile per evidenziare eventuali parti strutturali tramite markup.

**Stato:** la propagazione DTB è conclusa e verificata; resta da sostituire il Debug ID progressivo con il timestamp e integrare il DTB con il logging persistente descritto nelle sezioni successive.

## 4. Punto raggiunto nel piano di Fault Injection

Siamo all'inizio della fase di introduzione progressiva del Fault Injection. L'infrastruttura preparatoria è pronta, ma non sono ancora stati inseriti veri provocatori di errori.

## 5. Dove collocare i provocatori

La prima idea naturale è collocare i provocatori nei blocchi `try`, perché identificano normalmente zone nelle quali PBD riconosce esplicitamente la possibilità di un fallimento e possiede già un percorso di gestione.

Tuttavia **non è stato deciso di inserire meccanicamente un provocatore in ogni `try`**. Un singolo `try` può racchiudere operazioni semanticamente differenti. Il punto migliore d'iniezione dovrebbe corrispondere, quando possibile, al luogo nel quale quell'errore potrebbe realmente nascere.

Principio: usare punti minimi e significativi di intercettazione, senza costruire una seconda pipeline di PBD.

## 6. Ipotesi di un thread esterno

È stata considerata la possibilità di creare un thread parallelo incaricato di lanciare eccezioni sull'applicazione principale, così da provocare errori anche al di fuori dei punti esplicitamente strumentati.

La conclusione attuale è che **probabilmente non verrà usato**.

Un'eccezione sollevata normalmente da un thread rimane nel thread che l'ha sollevata e non viene trasferita automaticamente al main thread. CPython dispone di meccanismi di basso livello capaci di iniettare asincronamente un'eccezione in un altro thread, ma l'eccezione potrebbe interrompere PBD in un punto completamente arbitrario, anche durante la modifica di uno stato interno o mentre è detenuto un lock.

Si finirebbe quindi per testare un'interruzione asincrona arbitraria anziché il fallimento realistico di una determinata operazione seguito dalla normale propagazione e gestione PBD.

Un simile meccanismo potrebbe eventualmente diventare in futuro uno stress test separato, ma non appartiene al modello principale del Fault Injection previsto.

## 7. Catalogo delle eccezioni

È stata proposta una raccolta complessiva dei tipi di eccezione disponibili, dalla quale poter effettuare estrazioni casuali:

```text
Fault disponibili
├── OSError
├── FileNotFoundError
├── ValueError
├── KeyError
├── RemoteDisconnected
├── ...
```

Non sarebbe però corretto estrarre indiscriminatamente qualunque eccezione in qualunque punto del programma. Operazioni differenti hanno insiemi differenti di fault plausibili.

Il modello emerso è:

```text
catalogo complessivo
        ↓
punto d'iniezione
        ↓
sottoinsieme di fault ammessi
        ↓
random.choice(...)
        ↓
nuova Exception
```

Il contesto rimane locale al punto d'iniezione e non viene imposto un contesto universale del Fault Injection.

### Istanze o tipi

Nel catalogo non dovrebbero probabilmente essere conservate istanze già costruite. Ogni fault deve produrre una nuova istanza, perché quella specifica occorrenza riceverà il proprio timestamp/DTB e traceback.

Il catalogo potrà quindi contenere classi oppure, nei casi che richiedono argomenti specifici, piccole factory. La forma concreta è ancora da decidere.

## 8. Probabilità di fallimento

Non ogni passaggio attraverso un provocatore deve produrre un errore. Ogni punto d'iniezione rappresenta una **opportunità di fault**.

Per esempio `probability = 0.40` significa approssimativamente 40% fault e 60% normale esecuzione.

Il meccanismo naturale è:

```python
if random.random() < probability:
    # genera fault
else:
    # normale prosecuzione
```

Poiché `random.random()` produce valori nell'intervallo `[0, 1)`, non è necessario costruire intervalli artificiali come `0–0.40` e `0.41–1`.

## 9. Due randomizzazioni distinte

Sono state individuate due decisioni casuali concettualmente differenti:

1. **Stabilire se il passaggio deve fallire:** `random.random() < probability`.
2. **Stabilire quale fault deve verificarsi:** soltanto se la prima estrazione decide di produrre un errore, `random.choice(faults)`.

```text
raggiunto punto d'iniezione
        ↓
deve fallire?
        │
        ├── no → normale prosecuzione
        │
        ↓ sì
quale fault?
        ↓
random.choice(...)
```

Per ora non è necessario introdurre pesi differenti fra le singole eccezioni. In futuro sarebbe eventualmente possibile farlo, ma non fa parte dell'implementazione iniziale.

## 10. Prima proposta di interfaccia del Fault Injection

Dalla discussione è emersa una prima forma considerata promettente. Non è ancora una firma definitiva, ma concettualmente potrebbe essere:

```python
debug.FaultInjection.inject(
    faults=(...),
    probability=0.4,
    message="...",
)
```

Il comportamento interno sarebbe:

```text
Fault Injection attivo?
        │
        ├── no ───────────────→ return
        │
        ↓ sì

random.random() < probability?
        │
        ├── no ───────────────→ return
        │
        ↓ sì

seleziona casualmente un fault ammesso
        ↓
crea una nuova Exception
        ↓
debug.DTB.register(error, message, artwork_id=...)
        ↓
scrive la registrazione DEBUG sul log persistente
        ↓
raise error
```

Questa costituisce la **base di discussione per la prossima sessione**.

Non sono ancora stati fissati il nome definitivo della classe, il nome definitivo di `inject()`, la firma precisa, la rappresentazione del catalogo, il modo di indicare il sottoinsieme delle eccezioni ammesse, la posizione e il valore della probabilità di default e il primo catalogo concreto dei fault.

La firma non deve quindi essere implementata astrattamente prima di verificarla su un primo caso reale.

## 11. Campione e rotazione delle opere

Rimane aperta la parte del piano che prevede, per test lunghi, l'acquisizione di un campione limitato di opere reali e il successivo riutilizzo ciclico dello stesso campione:

```text
campione reale limitato
        ↓
metadata reali
        ↓
riutilizzo ciclico
        ↓
Simulation
        ↓
Fault Injection
```

Questo permetterebbe di sottoporre ripetutamente il codice interno agli stessi dati senza aumentare proporzionalmente il traffico verso Pixiv e senza confondere i fault artificiali con eventuali rate limit reali.

Questa parte non è ancora implementata e diventerà soprattutto importante quando il Fault Injection passerà dalle prove locali a campagne prolungate di stress.

## 12. Obiettivi successivi del Fault Injection

A regime il Fault Injection dovrà permettere di esercitare sistematicamente gestione delle eccezioni, notifiche UI, renderer, storico, stati di discard, continuazione dopo errori recuperabili, interruzione dopo errori non recuperabili, recovery, checkpoint, resume, concorrenza, diversi formati Ugoira e rate limit.

Non è però opportuno progettare preventivamente un framework capace di risolvere tutti questi casi.

## 13. Punto preciso da cui ripartire

La prossima sessione dovrebbe partire da **un primo punto reale del codice**:

```text
scegliere un punto reale di possibile fallimento
        ↓
identificare le eccezioni sensate in quel punto
        ↓
definire il sottoinsieme dei fault ammessi
        ↓
verificare sul caso reale la proposta inject(...)
        ↓
implementare soltanto l'infrastruttura necessaria
        ↓
estendere progressivamente agli altri casi
```

In particolare va verificata sul primo caso concreto la proposta:

```python
debug.FaultInjection.inject(
    faults=...,
    probability=...,
    message=...,
)
```

L'obiettivo è lasciare emergere l'interfaccia del Fault Injection dai casi d'uso reali di PBD, evitando di costruire anticipatamente un framework universale.

## 14. Logging persistente — nuovo requisito

È emerso un requisito ulteriore: **Fault Injection deve poter essere usato anche con Simulation disattivata**.

In una configurazione come:

```text
Debug = True
Simulation = False
Fault Injection = True
```

PBD lavora sull'archivio reale. Un fault può quindi influenzare realmente download, metadata, checkpoint e successivo resume. Per verificare a posteriori che il sistema abbia mantenuto correttamente lo stato, non è sufficiente osservare il renderer o la console durante l'esecuzione: serve una traccia persistente.

Il log dovrà permettere di rispondere almeno a domande come: quale opera è stata colpita, quale fault è stato provocato, se l'eccezione è arrivata al normale sistema errori, se l'opera è rimasta nel checkpoint, se al resume è stata recuperata e qual è lo stato finale dei relativi metadata.

## 15. Timestamp come identificatore di correlazione

Il precedente Debug ID progressivo viene sostituito, a livello progettuale, da un **timestamp generato al momento della registrazione dell'evento**.

```text
register()
    ↓
genera timestamp
    ↓
lega timestamp + messaggio libero + artwork_id eventuale all'Exception
    ↓
scrive DEBUG
    ↓
raise
    ↓
hierarchy() / cast() / inherit()
    ↓
notify()
    ↓
recupera lo stesso timestamp dall'Exception
    ↓
scrive ERRSYS
```

Il timestamp viene quindi trasportato dal DTB. La precisione dovrà essere sufficiente a evitare collisioni anche in presenza di concorrenza; un timestamp ISO con frazioni di secondo è un candidato naturale.

## 16. Struttura del record

Il contenuto diagnostico principale rimane intenzionalmente **un messaggio libero**. Non vengono imposti campi semantici come `operation`, `exception_type`, `section`, `context` o `status`.

L'unico dato strutturato aggiuntivo previsto è `artwork_id`, quando disponibile. Questo consentirà a una futura routine di analisi di raccogliere tutte le opere coinvolte, recuperare i relativi metadata e verificare checkpoint, resume e stato finale.

## 17. Formato del file: JSON Lines

Il formato scelto è **JSON Lines (`.jsonl`)**: ogni evento è un oggetto JSON autonomo su una singola riga.

```json
{"timestamp":"2026-08-30T12:54:31.481234","source":"DEBUG","message":"Fault during artwork download","artwork_id":12345678}
{"timestamp":"2026-08-30T12:54:31.481234","source":"ERRSYS","message":"FileOperationError: access denied","artwork_id":12345678}
```

Schema minimo:

```text
timestamp
source       DEBUG | ERRSYS
message      stringa libera
artwork_id   opzionale
```

Il formato è append-only, robusto in caso di interruzione e facilmente analizzabile a posteriori.

## 18. Sorgenti del log: DEBUG ed ERRSYS

Le due sorgenti sono `DEBUG` ed `ERRSYS`.

- `DEBUG` viene prodotto dal sistema Debug/Fault Injection quando il fault viene creato e registrato, **prima del `raise`**.
- `ERRSYS` viene prodotto dal normale sistema errori quando l'eccezione arriva a `PBDError.notify()`. Deve contenere almeno il testo concreto dell'eccezione arrivata a quel punto.

La presenza della coppia:

```text
timestamp X
    DEBUG   presente
    ERRSYS  presente
```

conferma che il fault è stato provocato ed è arrivato a `notify()`. Se esiste solo `DEBUG`, il fault è stato lanciato ma non è transitato dal normale punto finale del sistema errori: questa assenza è già informazione diagnostica.

## 19. Architettura proposta del writer

Il logging rimane responsabilità di Debug. La struttura proposta prevede un metodo di base che scrive un record e un wrapper specializzato per `notify()`. I nomi sono provvisori; conta la separazione delle responsabilità.

```python
Debug.Log.write(
    timestamp,
    source,
    message,
    artwork_id=None,
)
```

e:

```python
Debug.Log.update(error)
```

`write()` non conosce `PBDError` né `notify()`: riceve i dati del record e li serializza nel JSONL. Sarà usato direttamente dalle future routine di Fault Injection per produrre la riga `DEBUG`.

`update(error)` è il wrapper destinato al sistema errori. Riceve soltanto l'istanza dell'eccezione, recupera dal DTB timestamp e `artwork_id`, costruisce il messaggio `ERRSYS` dal tipo e dal testo dell'eccezione e richiama `write()`.

In questo modo `PBDError.notify()` non deve conoscere il formato del log, il path, il JSON o la struttura interna del binding.

## 20. Apertura, scrittura e chiusura del file

La soluzione preferita è **non mantenere un file handle aperto per tutta la vita dell'applicazione**.

Ogni `write()`:

```text
acquisisce lock
    ↓
apre il file in append
    ↓
serializza una riga JSON
    ↓
scrive newline
    ↓
chiusura automatica del context manager
    ↓
rilascia lock
```

Questa soluzione elimina la necessità di `open()` e `close()` globali, riduce il rischio di perdere dati in caso di terminazione anomala e si presta bene a un log diagnostico. Poiché PBD usa thread, le scritture dovranno essere serializzate mediante un lock interno a Debug.

## 21. Posizione del log

Il log appartiene all'area Debug e dovrà risiedere sotto la root di default, indipendentemente dal percorso dei bookmark simulati.

```text
<default_root>\
└── debug\
    ├── bookmarks\
    └── logs\
        └── <debug-report>.jsonl
```

Il nome esatto del file e l'eventuale criterio di separazione per sessione sono ancora da decidere. È preferibile che ogni sessione sia distinguibile. La directory può essere creata alla prima scrittura, evitando inizializzazioni inutili.

## 22. Integrazione futura con Fault Injection

```text
raggiunto punto d'iniezione
        ↓
Fault Injection attivo?
        │
        ├── no → return
        ↓ sì
estrazione probabilità
        │
        ├── nessun fault → return
        ↓ fault
seleziona eccezione ammessa
        ↓
crea nuova Exception
        ↓
DTB.register(error, message, artwork_id=...)
        ↓
Debug.Log.write(... source="DEBUG" ...)
        ↓
raise error
        ↓
normale propagazione PBD
        ↓
notify()
        ↓
Debug.Log.update(error)
        ↓
Debug.Log.write(... source="ERRSYS" ...)
```

Le responsabilità restano separate:

```text
Fault Injection   decide se e quale fault provocare
DTB               lega l'identità diagnostica all'eccezione
Log               persiste gli eventi
```

## 23. Analisi successiva del report

Una futura routine di audit dovrà poter ricevere un `.jsonl`, raggruppare gli eventi per timestamp, verificare la presenza di `ERRSYS`, raccogliere gli `artwork_id`, interrogare i metadata relativi e verificare checkpoint, resume e stato finale.

La routine di analisi è una fase successiva e non deve essere implementata insieme al writer iniziale.

## 24. Nuove decisioni fissate

1. Fault Injection deve poter funzionare anche con Simulation disattivata.
2. Il Fault Injection reale richiede un log persistente.
3. Il Debug ID progressivo verrà sostituito da un timestamp usato come identificatore di correlazione.
4. Il messaggio del log rimane libero e senza schema semantico obbligatorio.
5. `artwork_id` è l'unico campo strutturato aggiuntivo previsto al momento ed è opzionale.
6. Il formato scelto è JSON Lines.
7. Le sorgenti dei record sono `DEBUG` ed `ERRSYS`.
8. `DEBUG` viene scritto prima del `raise`.
9. `ERRSYS` viene scritto da `notify()` quando l'eccezione arriva al normale sistema errori.
10. Le due righe condividono lo stesso timestamp tramite il DTB.
11. Il writer di base è generico; il metodo usato da `notify()` è un wrapper che accetta soltanto l'eccezione e ricava da essa il binding.
12. Il file viene preferibilmente aperto in append per ogni record e richiuso subito.
13. Le scritture devono essere serializzate con un lock.
14. Il report servirà successivamente a raccogliere gli ID delle opere coinvolte e verificare metadata, checkpoint e resume.

## Stato finale della sessione

```text
Debug
├── configurazione                         ✓
├── Simulation                            ✓
│   ├── static media                      ✓
│   ├── Ugoira / DebuggedZipFile          ✓
│   ├── FFmpeg / DebuggedFFmpegProcess    ✓
│   └── test completo senza fault         ✓
│
├── DTB
│   ├── register()                        ✓
│   ├── inherit()                         ✓
│   ├── error_info()                      ✓
│   ├── propagazione nelle gerarchie      ✓
│   ├── visualizzazione in notify()       ✓
│   └── Debug ID → timestamp              ← DA IMPLEMENTARE
│
├── Logging persistente                   ← PROSSIMA INFRASTRUTTURA
│   ├── JSONL
│   ├── record DEBUG
│   ├── record ERRSYS
│   ├── artwork_id opzionale
│   ├── writer append-only
│   ├── wrapper per notify()
│   └── lock per scritture concorrenti
│
└── Fault Injection
    ├── scelta punti d'iniezione
    ├── catalogo dei fault
    ├── sottoinsiemi locali
    ├── probabilità di iniezione
    ├── scelta casuale dell'eccezione
    ├── integrazione DTB / logging
    └── campagne di stress
```

### Prossimo passo consigliato

Prima di disseminare i provocatori nel codice, implementare il **minimo nucleo di logging persistente** e convertire il DTB dal Debug ID progressivo al timestamp.

Solo dopo, scegliere il primo punto reale di Fault Injection e verificare sul caso concreto la futura interfaccia `inject(...)`.
