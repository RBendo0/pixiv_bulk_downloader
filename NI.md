# PIXIV BULK DOWNLOADER — STATO DEL PROGETTO
## Riepilogo di passaggio — 24/08/2026

## 1. Stato generale

Nelle ultime sessioni è stato completato e testato il grosso porting architetturale di PBD.

Sono ormai stabilizzati:

- nuovo modello dei metadata artwork/author;
- `illust_detail()` come fonte canonica dell'artwork;
- `PixivMetadata` aggiornato alla nuova struttura;
- esclusione preventiva delle opere cancellate;
- nuovo sistema di storage e bucketing;
- pipeline di scansione dell'archivio;
- modalità All Missing e Resume Pending;
- download concorrente tramite artwork pool e image pool;
- gestione dell'interruzione tramite `InputPending/default_abort`;
- metadata autore reso opzionale durante `retrieve_bookmarks()`;
- pipeline Ugoira/FFmpeg;
- renderer concorrente;
- status slot con tempo trascorso;
- riepilogo statistico finale del download.

I test effettuati hanno dato esito positivo.

È stato inoltre aggiunto `build_and_run.ps1`, che permette di ricostruire l'eseguibile tramite PyInstaller e avviarlo direttamente.

L'ultimo blocco di lavoro è stato committato e inviato su `master`.


## 2. Metadata autore — decisione aggiornata

Il metadata autore rimane supportato, ma la sua acquisizione durante `retrieve_bookmarks()` è ora opzionale.

Motivo:

- circa 49.000 opere vengono recuperate dalla scansione bookmark in blocchi da 30, quindi con circa 1.600 chiamate API;
- gli autori distinti sono circa 10–11.000;
- `user_detail()` richiede una chiamata per autore;
- acquisire sistematicamente i metadata autore aumenta quindi enormemente il numero di chiamate e provoca facilmente rate limit.

Il metadata artwork contiene già l'ID e le informazioni autore necessarie al normale funzionamento di PBD.

L'utente può quindi scegliere durante `retrieve_bookmarks()` se acquisire anche i metadata autore. Normalmente non sono necessari.


## 3. Download e renderer — stato attuale

Il renderer utilizza slot associati ai worker e una riga globale di STATUS.

Lo status viene costruito direttamente da `Renderer` e mostra attualmente:

- tempo trascorso dall'inizio dell'operazione.

Il cronometro:

- parte con l'avvio effettivo del renderer;
- utilizza `time.monotonic()`;
- viene aggiornato ad ogni refresh del renderer;
- viene resettato con `Renderer.stop()`.

La riga STATUS non fa parte degli slot originali: viene aggiunta alla copia locale utilizzata da `_render()`.

La pulizia finale del pannello è stata semplificata mediante una singola sequenza ANSI costruita tramite moltiplicazione di stringhe.

Il comportamento è stato testato anche durante l'interruzione tramite ESC e la cancellazione delle righe è corretta.


## 4. Reportistica finale del download

`PixivBaseDownloader.download()` produce ora un piccolo riepilogo persistente dopo la scomparsa del renderer:

[+]: Artworks detected
[+]: Artworks processed
[+]: Media added
[+]: Media size

Semantica:

- `Artworks detected`: numero totale delle opere ricevute da `download()`;
- `Artworks processed`: numero delle opere effettivamente affidate all'artwork pool;
- `Media added`: differenza nel numero dei file non JSON presenti nell'archivio prima e dopo il download;
- `Media size`: differenza della dimensione complessiva degli stessi file.

Le statistiche sono volutamente informative e non fanno parte dell'infrastruttura critica.

Sono raccolte localmente in un dizionario `stats`.

Sono stati aggiunti due helper statici:

- `_media_stats(save_path)` → restituisce `(numero_file, dimensione_byte)`;
- `_format_size(size)` → converte automaticamente in B/KiB/MiB/GiB.

Test reale con interruzione:

- Artworks detected: 65
- Artworks processed: 21
- Media added: 175
- Media size: 548.14 MiB

Esito positivo.


# 5. PROSSIMA FASE — DIPENDENZE E LOGIN

QUESTO È IL PUNTO DA CUI RIPARTIRE NELLA NUOVA CHAT.

Prima di continuare i test finali/error handling, si vuole affrontare la revisione delle dipendenze strategiche e del login.


## 5.1 Dipendenze strategiche

È già stata presa la decisione architetturale di non affidare la ricostruibilità futura di PBD alla permanenza dei package/repository esterni.

Le due dipendenze strategiche sono:

- `my_gppt`;
- `pixivpy3`.

L'obiettivo è incorporarne nel repository PBD una copia effettivamente utilizzata dall'applicazione.

Nel progetto attuale sono già presenti directory locali dedicate a:

- `src/pixiv_bulk_downloader/my_gppt`
- `src/pixiv_bulk_downloader/my_pixivpy3`

La struttura definitiva e gli import devono però essere verificati.

Obiettivi:

1. identificare esattamente le versioni upstream attualmente utilizzate;
2. verificare le copie locali presenti nel repository;
3. decidere la struttura definitiva;
4. fare in modo che PBD utilizzi realmente le copie incorporate;
5. eliminare, dove opportuno, la dipendenza runtime dai package installati esternamente;
6. conservare per ogni libreria:
   - licenza;
   - versione upstream;
   - provenienza;
   - eventuali modifiche locali;
7. verificare il comportamento con PyInstaller;
8. verificare successivamente la ricostruibilità in ambiente pulito.

Va mantenuta una separazione concettuale netta:

DISPONIBILITÀ DEL CODICE
→ viene risolta conservando localmente le dipendenze.

COMPATIBILITÀ FUTURA CON PIXIV
→ è un problema diverso e verrà affrontato soltanto se API/autenticazione/protocollo cambieranno.


## 5.2 Login / autenticazione

Il login deve essere analizzato insieme alle dipendenze perché coinvolge direttamente `my_gppt` e PixivPy3.

Da riesaminare:

- acquisizione delle credenziali/token;
- autenticazione;
- persistenza;
- refresh;
- gestione degli errori;
- responsabilità tra login, configurazione e `PixivCallAPI`;
- dipendenza effettiva da `my_gppt`;
- eventuali modifiche locali effettuate in passato a `my_gppt`.

Era stata avanzata l'ipotesi di:

1. recuperare/confrontare la versione originale upstream di `my_gppt`;
2. identificare esattamente le modifiche locali;
3. verificare se PBD può essere adattato all'interfaccia originale;
4. evitare modifiche locali alla libreria se non realmente necessarie.

NON assumere però che questa sia già la decisione definitiva: prima va analizzato il codice attuale.


# 6. LAVORI SUCCESSIVI — TEST FINALI ED ERRORI

Dopo dipendenze/login rimane una fase complessiva di test e consolidamento.


## 6.1 Fault injection / debug rapido

Va progettato un sistema semplice per provocare artificialmente errori nei diversi punti della pipeline.

Lo scopo è evitare di dover riprodurre manualmente condizioni rare.

Possibili failure point:

- frames non validi;
- frame mancante nello ZIP;
- ZIP mancante/corrotto;
- `archive.read()` fallita;
- avvio FFmpeg fallito;
- `Encoder.add()` fallita;
- FFmpeg con return code != 0;
- filesystem;
- API;
- rate limit;
- download;
- salvataggio;
- checkpoint;
- recovery.

È stata ipotizzata una modalità/sessione di debug controllata da un modulo dedicato e da flag/costanti per abilitare singole fault injection.

La struttura definitiva NON è ancora stata decisa.


## 6.2 Error handling

La revisione degli errori verrà affrontata insieme ai test finali/fault injection.

Da verificare:

- gerarchia `PBDError`;
- vecchi `PBDError.cast()`;
- utilizzo di `PBDError.hierarchy()`;
- responsabilità dei vari livelli;
- traduzioni/intercettazioni duplicate;
- filesystem;
- API;
- download;
- Ugoira/Encoder;
- checkpoint;
- strategie Fatal / Retry / Continue / Rate Limit.


## 6.3 Flusso UI degli errori

Il principio stabilito è:

renderer
= stato operativo sintetico e temporaneo

console/history
= diagnosi persistente

Il refactoring previsto è relativamente circoscritto: portare la messaggistica degli errori verso `PBDError.notify()`/notifiche persistenti, evitando di cercare di mantenere necessariamente l'errore sulla stessa riga del renderer.

Durante i test con forte rate limiting è emerso un caso significativo:

- al primo rate limit il messaggio veniva aggiunto correttamente alla riga dell'opera;
- se, terminati i primi 60 secondi, scattava immediatamente un secondo rate limit, la riga originale dell'opera non era più disponibile e il messaggio finiva disallineato/a capo.

Questo rafforza l'idea che gli errori persistenti vadano stampati su righe proprie invece di essere legati rigidamente alla riga operativa del renderer.


# 7. Distribuzione — fase successiva

Dopo dipendenze, login e test finali rimarrà da definire la strategia complessiva di distribuzione.

Da discutere:

- sorgente Python;
- EXE standalone;
- eventuale package installabile;
- eventuale pubblicazione PyPI;
- FFmpeg;
- riproducibilità delle build;
- dipendenze runtime/development;
- test in ambiente pulito;
- packaging/PyInstaller.

PyInstaller incorpora già le dipendenze utilizzate al momento della build, ma questo NON risolve da solo il problema della conservazione a lungo termine del sorgente delle dipendenze strategiche.


# 8. Ordine di lavoro aggiornato

Ordine attuale:

1. Revisione dipendenze strategiche `my_gppt` / `pixivpy3`.
2. Analisi e refactoring login/autenticazione.
3. Verifica dell'utilizzo effettivo delle copie locali delle dipendenze.
4. Fault injection / modalità debug.
5. Test finali complessivi.
6. Refactoring generale error handling durante i test.
7. Porting del flusso UI degli errori verso notifiche persistenti.
8. Audit finale checkpoint/recovery/rate limit.
9. Strategia di distribuzione.
10. Test di build/riproducibilità in ambiente pulito.
11. Eventuale preparazione alla distribuzione pubblica/PyPI.


# 9. Metodo di collaborazione

Il lavoro viene svolto in maniera incrementale.

Principi essenziali:

- prima analizzare il codice realmente esistente;
- distinguere sempre analisi, proposta, decisione e implementazione;
- non trasformare automaticamente una proposta in una decisione architetturale;
- una modifica concettuale per volta;
- evitare sovra-ingegnerizzazione;
- preferire soluzioni locali e semplici quando il problema è locale e semplice;
- individuare esplicitamente responsabilità e punto di intervento prima di modificare il codice;
- l'agente può essere proattivo nell'individuare problemi e alternative, ma le decisioni architetturali vanno condivise;
- quando il problema non è ancora maturo, ragionare insieme prima di produrre codice;
- durante l'implementazione guidare con modifiche piccole e verificabili;
- dopo ogni blocco significativo effettuare un test prima di procedere.

Il prossimo lavoro deve quindi iniziare ESAMINANDO lo stato attuale di `my_gppt`, `my_pixivpy3`, login/configurazione e `PixivCallAPI`, senza modificare immediatamente il codice.