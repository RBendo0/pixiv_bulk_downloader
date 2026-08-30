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

`register()` genera un Debug ID progressivo e associa all'istanza dell'eccezione una stringa diagnostica del tipo `Debug ID 00017: <messaggio>`.

Rispetto al progetto iniziale è stata scelta una soluzione più semplice: nessun registro globale degli ID, nessun `Debug Section ID` per ora e nessun ID separato memorizzato sull'eccezione. L'eccezione conserva direttamente la stringa diagnostica finale tramite l'attributo privato `_debug_info`.

### Propagazione

Quando PBD traduce un'eccezione in una nuova istanza, il DTB viene trasferito mediante `debug.DTB.inherit(new_error, old_error)`. Il meccanismo è stato applicato a `PBDError.hierarchy()`, `PBDError.cast()`, `ConfigError.hierarchy()`, `MediaToolExecutableError.hierarchy()` ed `EncoderStreamError.hierarchy()`.

### Osservazione finale

`PBDError.notify()` è il punto finale di osservazione. Con Debug attivo può produrre:

```text
[#]: Debug ID 00017: ...
[!]: normale messaggio PBD
```

Se l'eccezione non possiede un binding: `[#]: Debug ID: not associated`.

La presenza della riga viene determinata esplicitamente tramite `if debug.enabled()` e non attraverso la truthiness del risultato di `error_info()`.

Il colore Debug dedicato è arancione. Sulla riga Debug è stato mantenuto `tag_color=ui.COLOR_DEFAULT` in previsione della possibilità di evidenziare in bianco parti strutturali del messaggio, per esempio il Debug ID, mediante il markup `@@...@@.`.

**Stato: DTB concluso.**

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

Nel catalogo non dovrebbero probabilmente essere conservate istanze già costruite. Ogni fault deve produrre una nuova istanza, perché quella specifica occorrenza riceverà il proprio Debug ID, DTB e traceback.

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
debug.DTB.register(error, message)
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
├── DTB                                   ✓
│   ├── register()                        ✓
│   ├── inherit()                         ✓
│   ├── error_info()                      ✓
│   ├── propagazione nelle gerarchie      ✓
│   └── visualizzazione in notify()       ✓
│
└── Fault Injection                       ← PROSSIMA FASE
    ├── scelta punti d'iniezione
    ├── catalogo dei fault
    ├── sottoinsiemi locali
    ├── probabilità di iniezione
    ├── scelta casuale dell'eccezione
    ├── integrazione DTB
    └── campagne di stress
```
