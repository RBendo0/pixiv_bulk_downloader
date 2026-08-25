# PBD --- Piano di simulazione e Fault Injection Testing

## Scopo

Introdurre in **Pixiv Bulk Downloader (PBD)** una modalità di testing
dedicata alla verifica sistematica dei percorsi di errore, evitando il
costo e il tempo di download e conversioni reali.

L'obiettivo non è creare un debugger, ma una **modalità operativa di
simulazione e fault injection** che permetta di esercitare il più
possibile il normale flusso dell'applicazione, sostituendo soltanto le
operazioni pesanti che non è necessario eseguire realmente.

La modalità dovrà consentire esecuzioni rapide e ripetibili nelle quali
il programma possa essere sottoposto intenzionalmente a numerosi
fallimenti, rendendo immediatamente visibili il comportamento del
renderer, dello storico, dei checkpoint e delle routine di recovery.

## 1. Modalità `testing`

La modalità non sarà implementata come costante interna in `const.py` né
come equivalente Python di una macro di compilazione C/C++. Sarà invece
una **opzione di configurazione avanzata**, modificabile manualmente
dall'utente.

``` text
testing = False
    → funzionamento normale

testing = True
    → modalità di simulazione / fault injection
```

L'opzione sarà inserita nelle **Advanced settings** e rilevata durante
l'inizializzazione.

## 2. Segnalazione esplicita all'avvio

Quando `testing` è attivo, PBD dovrà comunicarlo chiaramente durante
l'inizializzazione, indicativamente con:

``` text
Testing mode active
```

La modalità non deve poter essere confusa accidentalmente con
un'esecuzione produttiva. Anche il percorso dei bookmark mostrato nelle
normali informazioni di inizializzazione renderà visibile che
l'applicazione sta lavorando nell'area di debug.

## 3. Principio generale della simulazione

La modalità di testing deve mantenere **reale tutto ciò che interessa
verificare** e simulare soltanto le operazioni pesanti che non
aggiungono valore al fault injection.

``` text
Pixiv reale
    ↓
recupero informazioni online reale
    ↓
metadata reali
    ↓
costruzione dei job reale
    ↓
filesystem di test reale
    ↓
download simulato
    ↓
conversione simulata
    ↓
renderer reale
    ↓
gestione errori / recovery reale
```

Non si vuole creare una seconda implementazione parallela di PBD. La
simulazione dovrà inserirsi nei punti minimi necessari e lasciare che il
resto dell'applicazione continui a funzionare attraverso i normali
percorsi.

## 4. Operazioni online

Le operazioni necessarie a recuperare le informazioni da Pixiv
rimarranno **reali**. Questo comprende, per quanto necessario al normale
flusso:

-   recupero dei bookmark;
-   interrogazioni API;
-   recupero dei metadata;
-   informazioni sulle opere;
-   metadata Ugoira;
-   numero e struttura dei frame disponibili online.

La modalità di testing non deve quindi simulare l'origine dei dati che
alimentano il programma. Lo scopo è esercitare PBD con dati realistici,
evitando soltanto il trasferimento effettivo dei media e la loro
elaborazione.

## 5. Download delle immagini statiche

Per le immagini statiche il punto di simulazione sarà il punto in cui
normalmente viene effettuato il download vero e proprio.

``` text
modalità normale:
download → trasferimento reale del file

modalità testing:
download → simulazione temporale → risultato simulato
```

Non verrà scaricato il contenuto multimediale. La routine dovrà tuttavia
continuare a produrre verso il resto dell'applicazione le informazioni
necessarie affinché il flusso e il renderer si comportino come durante
un download normale.

## 6. Ugoira

Le Ugoira richiedono una simulazione diversa dalle immagini statiche.

Nel funzionamento reale:

``` text
download ZIP
    ↓
lettura dei frame
    ↓
conversione
    ↓
GIF / WebM / MP4
```

In modalità testing:

-   lo ZIP non deve essere realmente scaricato;
-   non è necessario creare uno ZIP artificiale;
-   FFmpeg non deve essere invocato;
-   non devono essere prodotti realmente GIF, WebM o MP4.

I metadata Ugoira ottenuti online contengono già le informazioni sui
frame. Di conseguenza **non è necessario inventare il numero dei
frame**.

``` text
metadata Ugoira reali
    ↓
download ZIP simulato
    ↓
frame reali ricavati dai metadata
    ↓
conversione simulata
    ↓
aggiornamenti renderer
```

## 7. Simulazione temporale

Download e conversioni non dovranno risultare istantanei. Per mantenere
un comportamento utile alla verifica del renderer, dei thread e della
concorrenza, verranno introdotti **ritardi artificiali randomizzati**.

Sarà definito un tempo massimo di simulazione e il tempo effettivo sarà
scelto casualmente fra zero e tale limite.

``` python
delay = random.uniform(0, MAX_SIMULATION_DELAY)
```

Per le Ugoira sarà possibile simulare l'elaborazione progressiva dei
frame utilizzando il numero reale di frame ricavato dai metadata. Il
tempo, e non la struttura dell'opera, sarà quindi l'elemento
artificiale.

## 8. Separazione concettuale tra simulazione e fault injection

La modalità `testing` comprende due aspetti distinti:

``` text
TESTING
├── simulazione del lavoro
└── fault injection
```

### Simulazione

Serve a sostituire download reali, download ZIP Ugoira e conversioni
FFmpeg con operazioni leggere che mantengano il normale flusso
applicativo.

### Fault injection

Serve a provocare deliberatamente errori durante tale flusso.

Prima di affidarsi al fault injection sarà opportuno verificare che la
**sola simulazione senza errori** riproduca correttamente il
comportamento di una normale esecuzione. Questo permetterà di
distinguere eventuali problemi introdotti dal simulatore dai problemi
della gestione degli errori che si vuole effettivamente testare.

## 9. Fault injection randomizzato

Una volta verificata la modalità di simulazione, il sistema potrà
iniziare a generare deliberatamente errori.

L'obiettivo è sottoporre a stress:

-   gestione delle eccezioni;
-   notifiche UI;
-   renderer;
-   stati di discard;
-   continuazione dopo errori recuperabili;
-   interruzione dopo errori non recuperabili;
-   checkpoint;
-   resume;
-   concorrenza;
-   gestione dei singoli formati Ugoira;
-   rate limit e relativi percorsi di recovery.

Gli errori potranno essere iniettati in punti e momenti differenti. La
modalità dovrà permettere al programma di assumere contemporaneamente
numerosi stati differenti: da qui l'idea informale della modalità
**"albero di Natale"**, nella quale renderer e storico mostrano
intenzionalmente una grande varietà di stati, warning ed errori.

## 10. Filesystem reale

La modalità testing **non simulerà il filesystem**. Le directory
verranno realmente create.

Questo permette di continuare a esercitare:

-   costruzione dei path;
-   naming delle opere;
-   creazione delle directory;
-   salvataggio dei metadata;
-   scansione dell'archivio;
-   checkpoint;
-   resume dei job;
-   eventuali errori filesystem.

Regola:

> **Testing simula media e conversioni, non il filesystem.**

## 11. Area `debug`

La modalità testing non introdurrà una seconda root applicativa. PBD
continuerà a utilizzare la propria **root di default**.

All'interno di questa verrà creata una directory dedicata:

``` text
<default_root>\
└── debug\
```

Le opere simulate non verranno collocate direttamente in `debug`. La
struttura prevista è:

``` text
<default_root>\
└── debug\
    └── bookmarks\
        ├── <opera 1>\
        ├── <opera 2>\
        └── ...
```

Questo mantiene una struttura semanticamente chiara e lascia `debug`
disponibile in futuro per eventuali altri artefatti di testing.

## 12. Reinizializzazione del percorso `bookmarks`

La deviazione verso l'area di debug dovrà avvenire **durante
l'inizializzazione dei percorsi**, non nelle singole routine di
download.

``` text
normale:
<root>\bookmarks

testing:
<root>\debug\bookmarks
```

Quando viene rilevato `testing = True`, la directory `bookmarks` viene
reinizializzata aggiungendo il livello `debug`.

Da quel momento il resto del programma continuerà a ricevere e
utilizzare normalmente il percorso risultante. Questo evita di
disseminare controlli `if testing:` nelle routine che operano
sull'archivio.

La modalità speciale viene quindi assorbita il più a monte possibile.

## 13. Visibilità del percorso durante l'inizializzazione

Poiché il percorso `bookmarks` viene normalmente mostrato durante
l'inizializzazione, la deviazione sarà immediatamente visibile.

``` text
Testing mode active
...
Bookmarks .... : C:\...\pbd\debug\bookmarks
```

Avremo quindi due indicatori:

1.  messaggio esplicito di modalità testing;
2.  percorso `debug\bookmarks` nelle normali informazioni di
    inizializzazione.

## 14. Principio architetturale

L'implementazione dovrà cercare **punti minimi di intercettazione**.

Non vogliamo costruire un secondo downloader, un secondo encoder, una
seconda pipeline o una versione parallela del renderer.

Vogliamo invece intercettare le operazioni reali nel punto appropriato e
sostituire esclusivamente ciò che è costoso o inutile ai fini del test.
Il resto del programma dovrà continuare a percorrere, per quanto
possibile, gli stessi cammini utilizzati in produzione.

## 15. Sequenza prevista di implementazione

1.  aggiungere l'opzione `testing` alle Advanced settings;
2.  caricarla durante l'inizializzazione;
3.  mostrare chiaramente `Testing mode active`;
4.  reinizializzare `bookmarks` come `<default_root>\debug\bookmarks`;
5.  intercettare il download delle immagini statiche;
6.  introdurre la simulazione temporale dei download;
7.  intercettare il download ZIP delle Ugoira;
8.  intercettare la conversione Ugoira;
9.  utilizzare i frame reali dei metadata per simulare l'elaborazione;
10. verificare un'intera esecuzione **in simulazione senza fault**;
11. introdurre progressivamente il fault injection;
12. randomizzare errori, punti di fallimento e tempi;
13. verificare renderer, storico, recovery, checkpoint e resume;
14. utilizzare la modalità per l'audit sistematico dei percorsi di
    errore.

## 16. Decisioni ancora da prendere

Non sono ancora state definite nel dettaglio:

-   struttura esatta del campo `testing` nelle Advanced settings;
-   valori massimi dei ritardi simulati;
-   granularità temporale della simulazione Ugoira;
-   probabilità di generazione degli errori;
-   distribuzione degli errori fra le diverse operazioni;
-   eventuale possibilità futura di separare `simulation` e
    `fault injection` in due opzioni configurabili;
-   catalogo preciso degli errori da iniettare;
-   eventuale riproducibilità tramite seed casuale.

Questi aspetti verranno decisi dopo aver esaminato i punti reali del
codice nei quali inserire la modalità di simulazione.

## Obiettivo finale

La modalità testing dovrà permettere di eseguire PBD su dati reali
provenienti da Pixiv, attraversando realmente la propria architettura,
ma senza sostenere il costo dei media e delle conversioni.

``` text
dati reali
+ filesystem isolato
+ operazioni pesanti simulate
+ tempi artificiali
+ errori iniettati
= fault injection testing di PBD
```

La modalità servirà principalmente alla fase finale di verifica e
consolidamento della gestione degli errori.
