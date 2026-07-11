# Pixiv Bulk Downloader

## Architectural Decision Log

Questo documento raccoglie le principali decisioni architetturali del progetto.

Il suo scopo non è descrivere il funzionamento del codice, ma spiegare **perché esistono i principali moduli e sottosistemi dell'applicazione**.

Il codice può evolvere nel tempo attraverso refactoring e nuove implementazioni; le motivazioni che hanno portato alla nascita di questi componenti, invece, dovrebbero cambiare molto raramente.

---

# Decisione 001 - Introduzione di caapi come unica facciata verso le librerie esterne

## Problema

L'applicazione dipendeva direttamente da `pixivpy3` e dagli altri componenti esterni, distribuendo le chiamate API in numerosi punti del codice.

Questo aumentava l'accoppiamento e rendeva difficile modificare il comportamento comune delle chiamate.

## Decisione

Introdurre `caapi` come unico punto di accesso verso le librerie esterne.

## Motivazioni

* isolare le dipendenze esterne;
* fornire un'interfaccia uniforme al resto dell'applicazione;
* centralizzare il comportamento comune delle API;
* facilitare eventuali future sostituzioni delle librerie sottostanti.

## Conseguenze

I moduli applicativi non dipendono più direttamente dalle librerie esterne, ma esclusivamente da `caapi`.

---

# Decisione 002 - Tradurre le eccezioni alla frontiera dell'applicazione

## Problema

Le eccezioni generate dalle librerie esterne propagavano dettagli implementativi all'interno dell'applicazione.

## Decisione

La traduzione delle eccezioni deve avvenire nel punto di frontiera, cioè all'interno di `caapi`.

## Motivazioni

* separare il dominio applicativo dai dettagli delle librerie;
* uniformare gli errori gestiti dall'applicazione;
* evitare che i moduli conoscano eccezioni appartenenti a componenti esterni.

## Conseguenze

L'applicazione lavora principalmente con la propria gerarchia di errori (`PBDError` e derivate), indipendentemente dall'implementazione sottostante.

---

# Decisione 003 - Introduzione di ERRS come sistema centralizzato di gestione degli errori e delle strategie di recupero

## Problema

La gestione degli errori era distribuita nei moduli applicativi.

Ogni modulo implementava autonomamente blocchi `try/except`, menu di recovery, messaggi, countdown e controllo del flusso.

## Decisione

Realizzare ERRS (Error System) come sottosistema dedicato alla gestione completa degli errori dell'applicazione.

## Motivazioni

ERRS ha il compito di centralizzare:

* la gerarchia degli errori;
* la gestione delle eccezioni;
* la presentazione degli errori all'utente;
* i menu di recovery (Abort, Retry, Continue);
* la gestione dei Rate Limit;
* il controllo del flusso successivo alla gestione dell'errore.

## Conseguenze

I moduli applicativi devono progressivamente limitarsi a svolgere la propria logica funzionale, delegando ad ERRS l'intera gestione degli errori.

---

# Decisione 004 - Introduzione di PixivPath come astrazione del layout dell'archivio

## Problema

La struttura delle cartelle dell'archivio era conosciuta da numerosi moduli dell'applicazione.

Qualunque modifica al layout richiedeva interventi distribuiti nel codice.

## Decisione

Centralizzare in `PixivPath` tutta la conoscenza relativa all'organizzazione dell'archivio locale.

## Motivazioni

* separare la logica dell'applicazione dalla struttura del filesystem;
* eliminare la duplicazione nella costruzione dei percorsi;
* consentire future modifiche del layout senza impatti sul resto del codice.

## Conseguenze

L'organizzazione fisica dell'archivio è conosciuta esclusivamente da `PixivPath`.

---

# Decisione 005 - Introduzione del sottosistema Metadata

## Problema

L'archivio locale è destinato a contenere un numero molto elevato di artwork.

L'analisi della distribuzione degli ID Pixiv ha mostrato la necessità di organizzare il filesystem e di mantenere un indice dell'archivio locale.

## Decisione

Introdurre un sottosistema Metadata incaricato di descrivere e indicizzare il contenuto dell'archivio.

## Motivazioni

* organizzare gli artwork in bucket coerenti;
* evitare scansioni complete del filesystem;
* mantenere informazioni persistenti sull'archivio;
* velocizzare le operazioni di ricerca, verifica e ricostruzione.

## Conseguenze

Il filesystem rappresenta il contenuto dell'archivio, mentre Metadata ne costituisce la descrizione logica.

---

# Decisione 006 - Introduzione del sottosistema UI

## Problema

La gestione della console era distribuita nell'applicazione tramite chiamate dirette a `print()`, `input()` e logiche locali.

Questo rendeva difficile uniformare il comportamento dell'interfaccia e implementare funzionalità avanzate.

## Decisione

Realizzare un sottosistema UI incaricato della gestione completa dell'interazione con la console.

## Motivazioni

UI centralizza:

* la gestione dell'output;
* la gestione dell'input;
* la costruzione dei menu;
* la distinzione tra output storico e output temporaneo;
* il polling della tastiera;
* la gestione degli input asincroni.

## Conseguenze

L'interazione con la console avviene attraverso un'unica interfaccia, rendendo uniforme il comportamento dell'applicazione e semplificando l'evoluzione futura del sistema di interfaccia.

---

# Decisione 007 - Separazione tra classificazione dell'errore e strategia di recovery

## Problema

L'analisi dei casi d'uso (`retrieve_bookmarks()`, `add_list_to_bookmarks()`, `base.py`) ha mostrato che il tipo di errore non determina sempre la stessa strategia di recupero.

La stessa eccezione può richiedere comportamenti differenti a seconda del contesto applicativo.

## Decisione

Separare la classificazione degli errori dalla loro gestione.

ERRS fornisce:

* una gerarchia di errori (`PBDError`);
* due modalità di conversione:
  * `PBDError.hierarchy()`;
  * `PBDError.cast()`;
* metodi `handle()` che implementano esclusivamente le strategie di recovery comuni.

La decisione di invocare `handle()` rimane responsabilità del chiamante.

## Motivazioni

* evitare una gestione degli errori eccessivamente centralizzata;
* mantenere la flessibilità dei casi d'uso;
* eliminare la duplicazione dei menu ARC e della gestione del Rate Limit;
* consentire recovery differenti pur condividendo la stessa gerarchia di errori.

## Conseguenze

I moduli applicativi possono:

* utilizzare `PBDError.cast()` per ottenere una recovery generica;
* utilizzare `PBDError.hierarchy()` per preservare le recovery specializzate;
* scegliere liberamente se utilizzare o meno `handle()`.

---

# Decisione 008 - Evoluzione di caapi in gestore della sessione Pixiv

## Problema

`caapi` centralizza già tutte le chiamate verso le librerie esterne, ma la sessione Pixiv (`AppPixivAPI` e `LoginInfo`) continua ad essere mantenuta dai downloader e passata ad ogni invocazione.

Questo introduce dipendenze inutili tra i workflow applicativi e l'implementazione della sessione.

## Decisione

Trasformare `caapi` da semplice facciata delle API a gestore della sessione Pixiv.

La sessione verrà aperta esplicitamente tramite:

```python
caapi.open_session(PixivAuth())
```

e mantenuta internamente da `caapi`.

## Motivazioni

* assegnare ad un unico componente la responsabilità della sessione Pixiv;
* eliminare la propagazione di `AppPixivAPI` e `LoginInfo` nei moduli applicativi;
* semplificare le firme dei metodi pubblici;
* rendere i downloader semplici orchestratori dei workflow.

## Conseguenze

Le chiamate API non riceveranno più `self.aapi` come parametro.

`PixivBaseDownloader` non dovrà più mantenere lo stato della sessione e potrà essere ulteriormente semplificato, demandando completamente a `caapi` la gestione del collegamento con Pixiv.

---

# Decisione 009 - Uniformare la nomenclatura degli identificatori alle convenzioni Python
Problema

Nel corso dell'evoluzione del progetto sono stati introdotti identificatori con convenzioni eterogenee, derivanti da fasi diverse dello sviluppo e da successive rifattorizzazioni.

Questa mancanza di uniformità riduce la leggibilità del codice e rende meno immediata l'individuazione del ruolo dei vari componenti.

## Decisione

Tutti gli identificatori del progetto devono essere progressivamente uniformati alle convenzioni di nomenclatura raccomandate dalle linee guida Python (PEP 8 e convenzioni consolidate del linguaggio).

L'adeguamento verrà effettuato durante i normali refactoring, evitando modifiche massive dedicate esclusivamente alla rinomina.

## Motivazioni

mantenere uno stile coerente in tutto il progetto;
migliorare la leggibilità del codice;
facilitare la manutenzione e la navigazione del codice sorgente;
rendere immediatamente riconoscibile il ruolo di moduli, classi, metodi, costanti e variabili.

## Conseguenze

Ogni nuovo componente dovrà rispettare fin dalla sua introduzione le convenzioni Python.

Gli identificatori preesistenti verranno progressivamente uniformati durante le future attività di refactoring, senza introdurre modifiche funzionali.

---
