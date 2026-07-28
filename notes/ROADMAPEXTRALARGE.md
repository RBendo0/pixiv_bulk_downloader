\# ROADMAP



\## Stato attuale del progetto



L’architettura principale di Pixiv Bulk Downloader è sostanzialmente completata.



Il progetto dispone ormai di:



\* architettura applicativa modulare;

\* sistema concorrente basato sul Thread Pool System;

\* renderer dedicato e thread-safe;

\* workflow di download multi-thread;

\* gerarchia unificata degli errori;

\* sistema di configurazione persistente;

\* configurazione avanzata separata;

\* gestione completa della Storage Root;

\* supporto alla selezione dei formati multimediali;

\* struttura dei metadata e dei checkpoint;

\* workflow per download, resume, missing, chrono e importazione di liste;

\* struttura iniziale per il supporto alle ugoira.



La fase corrente è dedicata al completamento del porting alla nuova gestione degli errori, all’implementazione della conversione delle ugoira e al successivo consolidamento generale dell’applicazione.



\---



\# Milestone completate



\## Architettura e concorrenza



\* Architettura applicativa principale.

\* Thread Pool System.

\* Pool separati per opere e media.

\* Renderer concorrente dedicato.

\* Gestione degli slot e del troncamento delle righe.

\* Workflow di download multi-thread.

\* Arresto e sincronizzazione ordinata dei pool.

\* Gestione delle interruzioni richieste dall’utente.



\## Download e archivio locale



\* Download delle opere Pixiv.

\* Modalità download completa.

\* Modalità missing.

\* Modalità chrono.

\* Ripresa dei download lasciati in sospeso.

\* Checkpoint persistenti.

\* Scansione dell’archivio locale.

\* Ricostruzione dell’indice dei lavori pendenti.

\* Salvataggio dei metadata.

\* Suddivisione delle opere in bucket.



\## Gestione dei bookmark



\* Recupero dei bookmark pubblici e privati.

\* Aggiunta di bookmark da liste CSV.

\* Coda persistente FIFO.

\* Gestione delle opere non trovate.

\* Gestione degli URL scartati.

\* Produzione delle statistiche finali.

\* Gestione del rate limit e delle interruzioni.



\## Configurazione



\* Sistema di configurazione persistente.

\* Separazione tra configurazione ordinaria e avanzata.

\* Migrazione delle impostazioni strutturate a dataclass.

\* Configurazione dei codec e dei formati avanzati.

\* Generazione del file delle impostazioni avanzate.

\* Visualizzazione e ripristino delle impostazioni avanzate.

\* Backup e restore dei valori di configurazione.



\## Storage Root



La classe `StorageDirs` è considerata completata.



Sono stati implementati:



\* percorso predefinito;

\* percorso personalizzato salvato nella configurazione;

\* override da riga di comando;

\* priorità `CLI > configurazione > default`;

\* normalizzazione automatica della directory `PBD`;

\* creazione automatica delle directory necessarie;

\* validazione preventiva del percorso;

\* backup della configurazione prima del salvataggio;

\* ripristino della configurazione precedente in caso di errore;

\* mantenimento dello stato runtime precedente quando il salvataggio fallisce;

\* blocco della modifica da menu quando è attivo un override CLI;

\* messaggi UI dedicati ai diversi percorsi operativi e di errore.



Il percorso nominale è stato verificato con successo.



Rimangono da collaudare sistematicamente:



\* utilizzo del percorso predefinito;

\* caricamento del percorso dal file di configurazione;

\* override tramite CLI;

\* persistenza del percorso dopo il riavvio;

\* rami di errore simulati.



\---



\# 1. Completamento del porting degli errori



\## Obiettivo



Completare la migrazione di tutti i moduli alla nuova gerarchia degli errori e alla nuova convenzione di gestione locale.



\## Principio architetturale



Gli errori devono essere gestiti il più vicino possibile al punto in cui vengono generati.



Devono essere propagati soltanto:



\* gli errori non recuperabili localmente;

\* gli errori che richiedono una decisione del livello chiamante;

\* gli errori che impediscono la prosecuzione coerente dell’applicazione.



Gli errori recuperabili non devono risalire inutilmente fino a `main()`.



\## Attività immediate



\* Completare il porting del modulo `animation`.

\* Verificare gli eventuali punti ancora legati alla vecchia gestione degli errori.

\* Eliminare riferimenti obsoleti alle vecchie classi.

\* Controllare la distinzione tra `PBDError.hierarchy()` e `PBDError.cast()`.

\* Uniformare la gestione degli errori prodotti dalle librerie esterne.

\* Verificare la corretta trasformazione delle eccezioni `OSError`.

\* Verificare che i rami recuperabili non terminino l’applicazione.

\* Verificare che gli errori realmente fatali arrivino correttamente al gestore globale.



\---



\# 2. Collaudo della gestione degli errori



\## Obiettivo



Verificare i percorsi non nominali simulando esplicitamente gli errori che difficilmente si presenterebbero durante l’uso ordinario.



\## Casi da simulare



\### Configurazione e Storage Root



\* errore durante la creazione della directory;

\* percorso non valido;

\* directory non accessibile;

\* errore durante `config.backup()`;

\* errore durante `config.save()`;

\* errore durante `config.restore()`;

\* file di configurazione assente;

\* file JSON danneggiato;

\* valore di configurazione del tipo errato;

\* backup assente durante un errore di salvataggio;

\* errore contemporaneo di salvataggio e ripristino.



\### Download



\* fallimento del salvataggio dei metadata;

\* errore durante la creazione della cartella dell’opera;

\* errore durante il submit al pool;

\* errore durante il download di un singolo media;

\* errore durante la cancellazione del checkpoint;

\* interruzione dell’utente con lavori ancora pendenti;

\* rate limit durante il recupero dei metadata;

\* rate limit durante il download dei media.



\### Archivio locale



\* checkpoint illeggibile;

\* metadata danneggiati;

\* directory incompleta;

\* file mancanti;

\* errore durante la scansione ricorsiva;

\* errore durante la ricostruzione dell’indice.



\---



\# 3. Refactoring del flusso UI degli errori



\## Obiettivo



Rendere i messaggi di errore più leggibili e coerenti, evitando righe eccessivamente lunghe e sovraccariche.



\## Convenzione proposta



I messaggi complessi dovranno essere suddivisi su più righe.



La prima riga dovrà indicare:



\* l’operazione fallita;

\* il contesto principale;

\* l’eventuale entità coinvolta.



Le righe successive dovranno essere indentate e mostrare:



\* tipo o descrizione dell’errore;

\* causa riportata dall’eccezione;

\* conseguenze operative;

\* azione automatica intrapresa;

\* eventuale azione richiesta all’utente.



Esempio concettuale:



```text

\[!]: Unable to save the new storage path.

&#x20;    Error: <descrizione dell’errore>

&#x20;    The configuration file may have been damaged.

```



Oppure:



```text

\[!]: Download failed.

&#x20;    Artwork: <ID:123456789> Titolo

&#x20;    Media: image.jpg

&#x20;    Error: <descrizione dell’errore>

&#x20;    The checkpoint has been preserved.

```



\## Attività previste



\* Individuare i messaggi di errore troppo lunghi.

\* Separare messaggio principale e dettagli.

\* Definire un’indentazione uniforme.

\* Uniformare la posizione di ID, titolo, file e percorso.

\* Evitare la ripetizione del tipo di errore quando già incluso da `report()`.

\* Distinguere chiaramente:



&#x20; \* errore;

&#x20; \* avviso;

&#x20; \* informazione;

&#x20; \* azione disponibile;

&#x20; \* operazione completata.

\* Valutare un metodo UI dedicato alla stampa strutturata degli errori.

\* Verificare il comportamento con righe lunghe e terminali stretti.

\* Integrare il nuovo formato con il renderer concorrente.



\---



\# 4. Conversione delle ugoira



\## Obiettivo



Completare il modulo multimediale e integrare la conversione delle ugoira nel workflow ordinario di download.



\## Formati previsti



\* GIF;

\* WebM.



Un eventuale supporto MP4 rimane un’evoluzione futura.



\## Attività immediate



\* Completare `set\_preferred\_media\_formats()`.

\* Completare il porting degli errori nel modulo `animation`.

\* Caricare i metadata specifici delle ugoira.

\* Estrarre i frame dall’archivio ZIP.

\* Associare a ogni frame il relativo delay.

\* Costruire la sequenza di `AnimationFrame`.

\* Implementare la generazione GIF.

\* Implementare la generazione WebM.

\* Utilizzare FFmpeg tramite CLI.

\* Verificare la disponibilità degli encoder richiesti.

\* Gestire i file temporanei.

\* Gestire la pulizia in caso di conversione fallita.

\* Integrare la conversione nel workflow di download.

\* Conservare il checkpoint se una conversione fallisce.

\* Considerare completata l’opera soltanto quando tutte le conversioni richieste sono terminate.

\* Collaudare l’intera pipeline.



\## Flusso previsto



```text

recupero metadata

→ download ZIP ugoira

→ estrazione dei frame

→ costruzione della sequenza temporale

→ conversione GIF

→ conversione WebM

→ verifica dei risultati

→ rimozione del checkpoint

```



\---



\# 5. Revisione completa del login



\## Obiettivo



Rifattorizzare integralmente il sistema di autenticazione, eliminando i residui della vecchia applicazione e isolando meglio le dipendenze esterne.



\## Ambiti del refactoring



\* apertura della sessione;

\* autenticazione OAuth;

\* integrazione con Playwright;

\* integrazione con `my\_gppt`;

\* gestione del redirect;

\* acquisizione del token;

\* rinnovo della sessione;

\* gestione dei timeout;

\* gestione degli errori di rete;

\* gestione degli errori prodotti dal browser;

\* gestione delle credenziali non valide;

\* gestione dell’interruzione da parte dell’utente;

\* separazione tra errori recuperabili e fatali;

\* presentazione dei messaggi UI.



\## Attività previste



\* Analizzare il flusso attuale completo.

\* Eliminare `LoginFailedError` se confermato come residuo obsoleto.

\* Definire le responsabilità di `open\_session()` e `auth()`.

\* Separare autenticazione, sessione e chiamate API.

\* Ridurre l’accoppiamento con `my\_gppt`.

\* Tradurre gli errori esterni nella gerarchia `PBDError`.

\* Definire eventuali retry.

\* Gestire chiaramente i timeout.

\* Migliorare la diagnostica senza esporre informazioni sensibili.

\* Uniformare i messaggi di errore al nuovo flusso UI multilinea.

\* Testare:



&#x20; \* login riuscito;

&#x20; \* credenziali non valide;

&#x20; \* timeout;

&#x20; \* browser non disponibile;

&#x20; \* redirect non ricevuto;

&#x20; \* errore di rete;

&#x20; \* sessione scaduta;

&#x20; \* interruzione manuale.



\---



\# 6. Classe di supporto al debug e ai test



\## Stato



Funzionalità da progettare in futuro. Non deve essere implementata durante il porting corrente.



\## Obiettivo



Disporre di un sistema centralizzato che permetta di attivare selettivamente comportamenti di debug e simulare condizioni difficili da riprodurre manualmente.



\## Possibile struttura



La classe potrà esporre costanti o flag relativi ai diversi sottosistemi, in modo simile all’organizzazione delle classi di errore.



Esempio concettuale:



```python

class Debug:



&#x20;   STORAGE = False

&#x20;   CONFIG = False

&#x20;   LOGIN = False

&#x20;   API = False

&#x20;   DOWNLOAD = False

&#x20;   ANIMATION = False

&#x20;   RENDERER = False

```



Potrà inoltre offrire metodi di test dedicati alla simulazione di comportamenti.



Esempio concettuale:



```python

Debug.raise\_config\_save\_error()

Debug.raise\_config\_restore\_error()

Debug.raise\_download\_error()

Debug.raise\_rate\_limit()

Debug.simulate\_login\_timeout()

```



\## Requisiti da valutare



\* attivazione e disattivazione centralizzata;

\* possibilità di abilitare un solo sottosistema;

\* esclusione automatica dalle build di rilascio, se necessario;

\* assenza di impatto sul percorso nominale;

\* simulazioni deterministiche;

\* simulazioni ripetibili;

\* possibilità di selezionare uno specifico punto di errore;

\* messaggi che rendano evidente quando una simulazione è attiva;

\* impossibilità di attivare accidentalmente il debug in produzione;

\* compatibilità con PyInstaller e con l’eseguibile compilato;

\* eventuale attivazione tramite variabili d’ambiente;

\* eventuale attivazione tramite argomenti CLI riservati allo sviluppo;

\* eventuale integrazione con test automatici.



La responsabilità della classe non dovrà essere quella di gestire gli errori, ma soltanto di produrre condizioni controllate che permettano di verificare i relativi percorsi.



\---



\# 7. Revisione delle librerie esterne



\## Obiettivo



Uniformare e isolare l’integrazione con le dipendenze esterne.



\## Librerie interessate



\* PixivPy3;

\* Playwright;

\* `my\_gppt`;

\* FFmpeg;

\* eventuali componenti di supporto alla console.



\## Attività previste



\* Individuare tutte le chiamate dirette alle librerie.

\* Racchiudere le chiamate esterne nei moduli di adattamento.

\* Evitare che eccezioni esterne si propaghino direttamente.

\* Normalizzare i dati restituiti.

\* Verificare la compatibilità con Python 3.13.

\* Consolidare le versioni delle dipendenze.

\* Rimuovere dipendenze non più utilizzate.

\* Documentare i requisiti dell’ambiente.

\* Verificare il funzionamento nell’eseguibile compilato.



\---



\# 8. Consolidamento del sistema di build



\## Obiettivo



Verificare che la struttura dell’applicazione compilata sia stabile e indipendente dalla directory di lavoro.



\## Stato già raggiunto



\* struttura delle cartelle finali modificata;

\* percorsi statici ricalcolati sulla base della posizione dell’eseguibile;

\* FFmpeg collocato nella directory prevista;

\* separazione tra file distribuiti e file generati dall’utente.



\## Attività rimanenti



\* verificare la presenza di FFmpeg nella build;

\* verificare il rilevamento dell’eseguibile FFmpeg;

\* verificare gli encoder disponibili;

\* verificare la creazione automatica delle cartelle utente;

\* verificare il primo avvio senza configurazione;

\* verificare il funzionamento da collegamento;

\* verificare gli override CLI contenuti nei collegamenti;

\* verificare l’avvio da directory di lavoro differenti;

\* verificare aggiornamenti e reinstallazioni;

\* evitare la sovrascrittura dei file utente.



\---



\# 9. Collaudo generale



\## Workflow da validare



\* avvio iniziale;

\* login;

\* caricamento della configurazione;

\* percorso predefinito;

\* percorso personalizzato;

\* override CLI;

\* download completo;

\* missing;

\* chrono;

\* resume;

\* aggiunta bookmark da CSV;

\* gestione delle opere non trovate;

\* gestione degli URL scartati;

\* interruzione manuale;

\* rate limit;

\* conversione ugoira;

\* configurazione dei formati;

\* impostazioni avanzate;

\* backup e restore;

\* chiusura ordinata dei pool;

\* arresto del renderer.



\## Livelli di collaudo



\### Percorsi nominali



Verificare prima tutti i workflow in condizioni ottimali.



\### Errori recuperabili



Simulare errori che devono permettere la prosecuzione o il retry.



\### Errori non recuperabili



Simulare errori che devono interrompere una singola attività senza compromettere l’intera applicazione.



\### Errori fatali



Verificare che soltanto gli errori realmente incompatibili con la prosecuzione raggiungano il gestore globale.



\### Build compilata



Ripetere i test principali usando l’eseguibile distribuito e non soltanto l’ambiente Python.



\---



\# 10. Consolidamento della UI



\## Attività previste



\* uniformare italiano e inglese;

\* consolidare la semantica dei prefissi;

\* documentare la convenzione:



```text

\[+] avanzamento, disponibilità, stato positivo o azione principale

\[-] assenza, esclusione o risultato negativo non critico

\[i] informazione o istruzione accessoria

\[?] richiesta diretta di input

\[!] avviso, errore, interruzione o anomalia

```



\* uniformare punteggiatura e spaziatura;

\* verificare colori e tag;

\* eliminare messaggi duplicati;

\* controllare la leggibilità su terminali stretti;

\* migliorare il flusso multilinea degli errori;

\* verificare la pulizia delle righe dinamiche;

\* verificare l’interazione tra UI ordinaria e renderer.



\---



\# 11. Documentazione e reportistica



\## Attività previste



\* aggiornare la roadmap;

\* aggiornare il Decision Log;

\* documentare la gestione dei percorsi;

\* documentare la gerarchia degli errori;

\* documentare il workflow delle ugoira;

\* documentare il Thread Pool System;

\* documentare il renderer;

\* documentare il sistema di configurazione;

\* documentare la build;

\* aggiungere commenti orientati alle ragioni delle decisioni;

\* evitare commenti che si limitino a descrivere meccanicamente il codice.



La documentazione e la reportistica possono essere gestite autonomamente dall’assistente dopo il completamento delle modifiche implementative.



\---



\# 12. Sequenza operativa a breve termine



Ordine consigliato delle prossime attività:



1\. completare il porting degli errori nel modulo `animation`;

2\. verificare l’avvio completo dell’applicazione;

3\. completare i test nominali di `StorageDirs`;

4\. simulare i principali errori di configurazione e percorso;

5\. completare la conversione ugoira in GIF;

6\. completare la conversione ugoira in WebM;

7\. integrare la conversione nel downloader;

8\. collaudare download e resume delle ugoira;

9\. completare il porting degli eventuali moduli residui;

10\. eseguire il collaudo generale;

11\. creare il commit;

12\. aggiornare documentazione e reportistica.



\---



\# 13. Attività a medio termine



\* Refactoring completo del login.

\* Refactoring del flusso UI degli errori.

\* Revisione delle librerie esterne.

\* Consolidamento del sistema di build.

\* Revisione dei messaggi dell’applicazione.

\* Verifica di tutte le responsabilità residue nei moduli.

\* Eliminazione del codice deprecato.

\* Aumento della copertura dei test.

\* Creazione di test automatici per i percorsi principali.



\---



\# 14. Evoluzioni future



Attività non prioritarie:



\* classe centralizzata di debug e simulazione;

\* test fault-injection automatizzati;

\* conversione automatica degli ZIP ugoira già presenti nell’archivio;

\* supporto MP4;

\* backup automatico dei file operativi;

\* backup delle liste URL;

\* ripristino automatico dei file operativi;

\* importazione ed esportazione della configurazione;

\* gestione di più profili di configurazione;

\* miglioramenti della UI;

\* ottimizzazioni prestazionali;

\* analisi delle metriche di produttività basate sulle decisioni;

\* raccolta strutturata delle decisioni progettuali;

\* eventuali nuove funzionalità per la gestione dei bookmark.



\---



\# 15. Pubblicazione



Dopo il completamento delle modifiche correnti:



1\. creare un commit completo;

2\. aggiornare documentazione e reportistica;

3\. verificare il repository pubblico;

4\. controllare eventuali download o utilizzi del progetto;

5\. aggiornare la documentazione online;

6\. pubblicare un avviso sullo stato del progetto;

7\. preparare il primo rilascio pubblico stabile.



\---



\# Criterio di completamento della fase corrente



La fase corrente potrà essere considerata conclusa quando:



\* tutti i moduli utilizzeranno la nuova gestione degli errori;

\* `StorageDirs` sarà collaudata nei percorsi nominali e di errore;

\* le ugoira saranno convertite correttamente in GIF e WebM;

\* la conversione sarà integrata nel workflow di download;

\* i checkpoint saranno gestiti correttamente;

\* l’applicazione supererà il collaudo generale;

\* la build compilata funzionerà senza dipendere dalla directory di lavoro;

\* documentazione, roadmap e Decision Log saranno aggiornati.



