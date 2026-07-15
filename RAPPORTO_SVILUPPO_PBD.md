# Rapporto di sviluppo — Pixiv Bulk Downloader (PBD)

**Periodo analizzato:** 1 giugno – 13 luglio 2026  
**Corpus:** 26 conversazioni concluse, da *Scaricare progetto PyPI 1* a *PBD 26 – TPS 3*  
**Nota:** la conversazione corrente costituisce la n. 27, ma non era ancora inclusa nell’esportazione analizzata.

---

## 1. Scopo del rapporto

Questo rapporto prova a stimare la quantità e soprattutto la natura del lavoro svolto sul Pixiv Bulk Downloader. L’obiettivo non è misurare la produttività mediante le sole righe di codice, ma ricostruire quanto effort sia stato assorbito da:

- progettazione;
- implementazione;
- refactoring;
- debugging e sperimentazione;
- definizione del metodo di collaborazione uomo–IA.

Le statistiche derivano dalle conversazioni di sviluppo esportate da ChatGPT e dai dati Git citati all’interno delle stesse chat. Le percentuali relative alla distribuzione dell’effort sono stime interpretative, non misure cronometriche.

---

## 2. Statistiche generali

| Indicatore | Valore |
|---|---:|
| Conversazioni di sviluppo concluse | 26 |
| Intervallo di calendario | 43 giorni |
| Giorni con attività registrata nelle chat | 27 |
| Giorni distinti con commit Git già rilevati | 19 |
| Messaggi complessivi | 9.273 |
| Messaggi dell’utente | 4.345 |
| Messaggi dell’assistente | 4.928 |
| Parole complessive stimate | circa 891.000 |
| Media messaggi per conversazione | 357 |
| Riferimenti ad allegati nelle chat | 1.071 |

Il numero degli allegati non corrisponde a 1.071 file diversi: comprende molte revisioni successive degli stessi moduli. Proprio questa ripetizione rende però il dato utile come indicatore dell’intensità della revisione.

### Moduli più frequentemente ripresentati o revisionati

| Modulo | Occorrenze indicative negli allegati |
|---|---:|
| `base.py` | 94 |
| `bookmarks.py` | 78 |
| `main.py` | 53 |
| `ui.py` | 47 |
| `tester.py` | 40 |
| `const.py` | 17 |
| `metadata.py` | 15 |
| `ROADMAP.md` | 15 |
| `pixiv_path.py` | 12 |
| `pixiv_errors.py` | 12 |
| `pixiv_call_api.py` | 10 |
| `errors.py` | 9 |

Questi numeri non misurano le modifiche Git, ma quante versioni o revisioni sono state portate nelle conversazioni. Evidenziano con chiarezza i punti su cui si è concentrato il lavoro: flusso di download, gestione dei bookmark, UI, test, metadata ed errori.

---

## 3. Evoluzione del progetto

### 3.1 Avvio e trasformazione del pacchetto originario

Le prime conversazioni partono dal download di un progetto da PyPI e dalla comprensione di un codice preesistente. Il lavoro iniziale è prevalentemente esplorativo e operativo:

- ricostruzione della struttura del pacchetto;
- comprensione dei flussi di fetch e download;
- correzione di errori immediati;
- riorganizzazione dei moduli;
- introduzione di checkpoint e ripresa dei lavori interrotti;
- primi interventi sul salvataggio dei bookmark.

Questa fase presenta molto codice, molti test e numerosi tentativi successivi. È il periodo con il rapporto più alto fra implementazione e progettazione.

### 3.2 Prime fondamenta architetturali

Tra le chat PyPI 4 e PyPI 10 il progetto smette progressivamente di essere una semplice modifica del pacchetto originario e acquisisce una propria architettura. Emergono:

- gestione degli Ugoira;
- `PixivMetadata` come interfaccia ai dati dell’API;
- checkpoint e persistenza dei metadata;
- `PixivPath`;
- Bucketing System HYPE/STABLE;
- revisione della struttura delle cartelle;
- maggiore tolleranza agli errori di download;
- progressivo distacco dai tipi e dalle convenzioni legacy.

Il Bucketing System è uno degli esempi più chiari di progettazione con ritorno immediato: risolve un problema concreto di scalabilità del filesystem e diventa parte stabile dell’organizzazione dei dati.

### 3.3 UI e gestione dell’interazione

Tra PyPI 11 e PyPI 15 il lavoro si concentra molto sulla console:

- eliminazione della dipendenza da Rich;
- introduzione e successiva revisione di `UI`;
- unificazione di output, menu e input;
- `InputPending`;
- gestione delle righe temporanee;
- porting dei `print()` esistenti;
- studio dei casi d’uso reali prima di proseguire con l’astrazione.

Questa fase è importante perché mostra sia il valore sia il costo della progettazione. L’idea iniziale della UI tendeva a ricostruire una parte della flessibilità già offerta da `print()`. Il progetto ha dovuto fermarsi, censire i casi d’uso e ridurre l’astrazione. Non è stato tempo inutile: ha prodotto una UI più aderente al dominio reale. Tuttavia è uno dei punti in cui si può parlare di **sovraprogettazione iniziale corretta tramite esperienza**.

### 3.4 Studio del rate limit e nascita di ERRS

Le chat PBD 16–20 segnano una seconda grande maturazione:

- tester specifici per il comportamento del rate limit;
- distinzione tra errori API e download;
- normalizzazione delle eccezioni;
- nascita di `DownloadRateLimitError`;
- trasformazione di `pixiv_errors.py` nel sottosistema ERRS;
- separazione tra identificazione dell’errore, traduzione e politica di recovery;
- centralizzazione dell’abort e delle azioni di recupero.

ERRS ha richiesto molte discussioni, ma il risultato si propaga su più aree: autenticazione, chiamate Pixiv, download, recupero, UI e controllo del flusso. Il suo costo progettuale risulta quindi ampiamente ammortizzato.

### 3.5 Metodo di sviluppo: Modalità Architettura, ICR e CSE

Durante PBD 20–23 viene formalizzato un metodo di collaborazione nato dai problemi incontrati nel lavoro concreto:

- **Modalità Architettura:** piccoli passi, prima modello e poi codice, niente decisioni anticipate;
- **ICR – Instant Code Review:** panoramica sintetica dei problemi dell’intero modulo, poi una modifica alla volta;
- **CSE – Complete Specification Engineering:** il codice viene completato solo quando la specifica del componente è sufficiente; se emergono nuove responsabilità o decisioni, la generazione si interrompe.

Queste direttive non aggiungono funzioni al programma, ma riducono due costi ricorrenti della collaborazione con l’IA:

1. produzione prematura di codice basato su assunzioni implicite;
2. sovraccarico cognitivo dovuto alla presentazione simultanea di troppe decisioni.

Una parte notevole della conversazione è stata necessaria per calibrare il metodo stesso. Questo effort non può essere attribuito interamente al software PBD: una quota rappresenta la costruzione di un processo riutilizzabile nei progetti futuri.

### 3.6 TPS e rifattorizzazione del download

Le chat PBD 24–26 introducono e stabilizzano il Thread Pool System:

- abbandono di `Condition`, contatori condivisi e `wait_until_ready()`;
- `ThreadPoolExecutor` più `BoundedSemaphore`;
- `submit()` bloccante;
- rilascio del semaforo tramite callback del `Future` anche in caso di errore;
- nessuna traduzione delle eccezioni all’interno del TPS;
- TPS reso istanziabile e indipendente dal dominio Pixiv;
- separazione tra pool persistente dei download e pool per la singola opera;
- console lock nella UI;
- scomposizione di `download()` in responsabilità più piccole;
- avvio della revisione di metadata e Ugoira prima del download.

Il TPS è un caso di progettazione intensa ma produttiva. La prima architettura viene scartata, ma la versione finale è più semplice, più generale e con meno stato condiviso. Il ripensamento non è un refactoring accidentale: è il risultato dell’emersione di requisiti di sincronizzazione che non erano visibili all’inizio.

---

## 4. Distribuzione stimata dell’effort

La distribuzione seguente non deriva dal tempo cronometrato. È una stima basata sulla natura delle conversazioni, sul numero di revisioni e sul tipo di attività documentata.

| Attività | Stima centrale | Intervallo plausibile |
|---|---:|---:|
| Progettazione e decisioni architetturali | 37% | 33–42% |
| Implementazione di nuove funzioni | 25% | 22–30% |
| Refactoring e integrazione | 22% | 18–26% |
| Debugging, tester ed esperimenti | 9% | 7–12% |
| Metodo, documentazione e coordinamento | 7% | 5–10% |

La progettazione è quindi la singola voce più grande, ma non assorbe da sola la maggioranza assoluta. Sommando progettazione e refactoring, circa il **59%** dell’effort è stato dedicato a decidere o migliorare la struttura del software, mentre circa un quarto è attribuibile alla produzione diretta di nuove funzioni.

### Interpretazione

Questo non significa che sia stato scritto poco codice. Significa che il codice è stato ripetutamente sottoposto a un processo di comprensione, verifica e ristrutturazione. La quantità di revisioni di `base.py`, `bookmarks.py`, `ui.py` e `main.py` conferma che il progetto è maturato per iterazioni, non attraverso una progettazione completa iniziale.

---

## 5. Abbiamo pensato troppo?

La risposta complessiva è: **in alcuni punti sì, ma non in modo generalizzato**.

### Progettazione con ritorno elevato

#### Bucketing System

Ha risolto un problema reale di organizzazione di decine di migliaia di opere e ha fornito una struttura stabile al salvataggio locale.

#### Metadata e persistenza

L’introduzione di un’interfaccia dedicata ha ridotto la dipendenza dai dizionari grezzi dell’API. Il modello è stato corretto più volte, ma il bisogno era reale e ricorrente. La successiva estensione a collection, checkpoint e Ugoira conferma che non si trattava di un’astrazione ornamentale.

#### ERRS

Ha unificato traduzione degli errori, recovery e abort. Il riuso attraverso più flussi rende giustificato l’investimento iniziale.

#### TPS

La progettazione è stata lunga e ha comportato lo scarto di un modello precedente, ma il risultato finale riduce lo stato condiviso e separa chiaramente capacità, esecuzione e dominio. Il componente è generalizzabile e serve più pool.

### Progettazione con ritorno misto

#### UI

La UI ha prodotto vantaggi concreti: uniformità, menu, input, gestione delle righe e lock della console. Tuttavia l’astrazione iniziale ha cercato di sostituire troppo direttamente `print()` e ha richiesto un censimento dei casi d’uso per essere riportata a una forma più naturale. Qui una fase iniziale più empirica avrebbe probabilmente ridotto il lavoro.

#### Metodo di collaborazione

ICR, CSE e Modalità Architettura hanno migliorato le fasi finali del progetto, ma una parte consistente del tempo è stata spesa per definire come interagire con l’assistente. Per il solo PBD il ritorno è parziale; su più progetti il costo può invece essere ammortizzato e diventare molto vantaggioso.

### Progettazione inevitabilmente esplorativa

Nei sistemi di error recovery e concorrenza alcuni requisiti sono emersi solo dopo tester, errori reali e prime implementazioni. In questi casi non era possibile evitare completamente il ripensamento progettando più a lungo all’inizio. Il lavoro ha seguito un ciclo legittimo:

**ipotesi → implementazione → osservazione → revisione del modello**.

---

## 6. Corrispondenza tra effort e risultato

Il risultato ottenuto appare proporzionato all’effort sotto tre aspetti.

### 6.1 Crescita funzionale

Il progetto è passato dall’adattamento di un pacchetto scaricato da PyPI a un’applicazione con:

- recupero e indicizzazione dei bookmark;
- checkpoint e resume;
- supporto a immagini, manga e Ugoira;
- organizzazione scalabile del filesystem;
- modalità chrono e missing;
- coda persistente per importazioni massive;
- gestione dei bookmark pubblici e privati;
- UI console dedicata;
- gestione strutturata degli errori;
- pool di thread con capacità controllata;
- renderer e avanzamento verso un download concorrente strutturato.

### 6.2 Crescita architetturale

Sono nati sottosistemi distinti e con responsabilità riconoscibili:

- metadata;
- path e bucketing;
- UI;
- ERRS e recovery control;
- chiamate API normalizzate;
- TPS;
- persistenza CSV e checkpoint.

Il progetto finale non è semplicemente più grande: è più separato e leggibile rispetto al punto di partenza.

### 6.3 Crescita delle competenze e del metodo

Il lavoro ha anche prodotto apprendimento su:

- progettazione delle eccezioni;
- separazione fra dominio e infrastruttura;
- sincronizzazione e thread pool;
- gestione del rate limit;
- persistenza e recovery;
- limiti delle astrazioni;
- collaborazione iterativa con un assistente IA.

Questa parte non è visibile nel repository ma costituisce un risultato reale. Riduce il costo dei progetti futuri e modifica il modo in cui vengono affrontate le decisioni.

---

## 7. Indicatori di produttività

Valutare la produttività con le sole righe di codice sarebbe fuorviante. Per il PBD risultano più utili quattro indicatori combinati.

### 7.1 Densità di attività

Ventisette giorni con messaggi di sviluppo nell’arco di quarantatré giorni di calendario indicano un’attività frequente, pur compatibile con il lavoro ordinario e le interruzioni. I diciannove giorni Git confermano che non tutte le sessioni di discussione hanno prodotto immediatamente un commit.

### 7.2 Profondità di revisione

La ripresentazione ripetuta dei moduli principali mostra che il lavoro non è stato superficiale. `base.py` e `bookmarks.py`, in particolare, sono stati il centro di più cicli di revisione.

### 7.3 Produzione di componenti stabili

Il valore maggiore non è il numero delle modifiche, ma la permanenza delle decisioni. Bucketing, checkpoint, path abstraction, ERRS e TPS continuano a sostenere più parti dell’applicazione.

### 7.4 Riduzione progressiva delle decisioni implicite

Nelle prime chat l’assistente propone spesso soluzioni complete che vengono poi adattate. Nelle ultime, il processo separa esplicitamente decisione, specifica, codice e review. Questo rallenta il singolo passo ma riduce il rischio di introdurre responsabilità non concordate.

---

## 8. Valutazione critica finale

### Punti di forza

- Elevata continuità dello sviluppo.
- Capacità di fermarsi quando l’astrazione non corrispondeva ai casi d’uso.
- Uso sistematico di tester per comprendere fenomeni reali, in particolare il rate limit.
- Progressiva separazione delle responsabilità.
- Documentazione frequente tramite roadmap, decision log e riassunti di passaggio.
- Trasformazione dell’IA da generatore di soluzioni a interlocutore progettuale controllato.

### Costi e debolezze

- Alcune conversazioni sono diventate molto grandi, con dispersione e ripetizioni.
- La UI ha richiesto più iterazioni del necessario prima di essere ricondotta ai casi reali.
- Parte del metodo di collaborazione è stata definita durante il progetto, generando attrito e lavoro non direttamente funzionale.
- L’architettura è stata talvolta discussa prima che tutti i requisiti empirici fossero emersi.
- I moduli centrali hanno accumulato molte revisioni, segno sia di attenzione sia di instabilità iniziale.

### Giudizio

Il progetto **non appare vittima di una sovraprogettazione sistematica**. Appare piuttosto come un progetto esplorativo nel quale la progettazione è stata resa esplicita e registrata, mentre normalmente resterebbe nella testa dello sviluppatore o verrebbe compressa.

Una quota di tempo è stata certamente spesa in discussioni che non hanno prodotto un ritorno immediato. Tuttavia le principali aree ad alto costo progettuale hanno generato componenti riutilizzati e una riduzione della complessità locale. Il saldo è quindi positivo, con un margine di miglioramento soprattutto nella rapidità con cui verificare le astrazioni contro casi d’uso concreti.

---

## 9. Conclusioni

Lo sviluppo del PBD mostra un modello di produttività diverso da quello basato esclusivamente sulla quantità di codice. Il lavoro principale non è consistito soltanto nell’aggiungere funzioni, ma nel trasformare progressivamente un progetto preesistente in un’applicazione dotata di una propria architettura.

Il dato più significativo è che circa tre quinti dell’effort stimato sono stati assorbiti da progettazione e refactoring. Questa proporzione sarebbe preoccupante se il risultato fosse rimasto una collezione di astrazioni poco utilizzate. Nel PBD, invece, le decisioni principali si sono tradotte in sottosistemi concreti e trasversali.

Non tutto il tempo di progettazione è stato ugualmente produttivo. La UI dimostra che un’astrazione può essere anticipata eccessivamente; ERRS e TPS mostrano invece che una progettazione estesa può essere giustificata quando governa errori, concorrenza e più flussi applicativi.

La lezione più utile non è quindi “progettare di più”, ma:

> **progettare abbastanza da rendere esplicite le responsabilità, quindi verificare presto il modello contro il codice e i casi d’uso reali.**

Nel complesso, il risultato ottenuto è coerente con la quantità di lavoro registrata. Il PBD non rappresenta soltanto circa venti giornate effettive di sviluppo: rappresenta anche la costruzione di un metodo personale di progettazione assistita che potrà ridurre il costo cognitivo e gli errori nei progetti successivi.
