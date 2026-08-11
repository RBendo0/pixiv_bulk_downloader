# Pixiv Bulk Downloader — Prossime fasi di sviluppo

## 1. Verifica della nuova pipeline Ugoira

### Test del flusso nominale

- [ ] Eseguire un test end-to-end della pipeline Ugoira.
- [ ] Verificare il download corretto dello ZIP.
- [ ] Verificare la generazione GIF.
- [ ] Verificare la generazione WEBM.
- [ ] Verificare la generazione MP4.
- [ ] Verificare l'aggiornamento progressivo del renderer.
- [ ] Verificare i messaggi finali:
  - `GIF completed`
  - `WEBM completed`
  - `MP4 completed`
- [ ] Verificare che non vengano prodotte notifiche di errore inattese.
- [ ] Verificare la corretta rimozione del checkpoint al completamento dell'opera.
- [ ] Verificare l'assenza di regressioni nel download delle opere non-Ugoira.

### Caso emerso durante il test

Durante il test del flusso normale è stato effettivamente incontrato un **rate limit durante il download di un'immagine**.

Questo caso dovrà essere analizzato anche nell'ambito della revisione generale dell'error handling:

- [ ] Verificare come viene classificato attualmente il rate limit.
- [ ] Verificare il percorso attraverso `PBDError.hierarchy()`.
- [ ] Verificare la gestione del retry.
- [ ] Verificare il comportamento del renderer durante il rate limit.
- [ ] Verificare cosa viene scritto nello storico della console.
- [ ] Verificare la gestione del checkpoint.
- [ ] Stabilire se l'attuale comportamento deve essere mantenuto o uniformato al nuovo modello di gestione degli errori.

---

## 2. Test dedicati dell'error handling Ugoira

Il normale test end-to-end verifica principalmente il percorso nominale.

I failure path della nuova pipeline dovranno invece essere provocati artificialmente tramite test dedicati e riproducibili.

### Validazione dei dati

- [ ] Simulare una struttura `frames` non valida.
- [ ] Simulare un frame privo del campo richiesto.
- [ ] Simulare un frame dichiarato nei metadata ma assente nello ZIP.
- [ ] Verificare la generazione e propagazione di `AnimationError`.

### Archivio ZIP

- [ ] Simulare ZIP inesistente.
- [ ] Simulare ZIP non valido.
- [ ] Simulare ZIP corrotto.
- [ ] Simulare errore durante `archive.read()`.
- [ ] Verificare sempre il corretto rilascio dell'archivio.

### Encoder / FFmpeg

- [ ] Simulare errore durante `Encoder.start()`.
- [ ] Simulare errore durante `Encoder.add()`.
- [ ] Simulare FFmpeg terminato con return code diverso da zero.
- [ ] Verificare `Encoder.stop(ignore_errors=True)` durante il recovery.
- [ ] Verificare che eventuali errori durante la terminazione non sostituiscano l'errore primario.

### UI e recovery

- [ ] Verificare la notifica nello storico con ID dell'opera e report specifico.
- [ ] Verificare `FORMAT discarded` per un errore limitato al singolo formato.
- [ ] Verificare la prosecuzione con gli altri formati dopo il fallimento di un formato.
- [ ] Verificare `Animation building failed` per un errore che compromette l'intera animazione.
- [ ] Verificare la conservazione del checkpoint nei failure path previsti.
- [ ] Verificare conservazione/eliminazione dei log FFmpeg nei diversi esiti.

---

## 3. Revisione generale dell'error handling

La gestione degli errori è evoluta significativamente con l'introduzione di:

- `PBDError.hierarchy()`;
- `PBDError.notify()`;
- storico persistente della console;
- sospensione sicura del renderer;
- nuove classi specializzate come `AnimationError`;
- distinzione tra errore diagnostico e stato mostrato dal renderer.

Occorre quindi effettuare un porting sistematico del vecchio codice verso il nuovo modello.

### Audit della gerarchia

- [ ] Cercare tutti gli utilizzi residui di `PBDError.cast()`.
- [ ] Valutare singolarmente la sostituzione con `PBDError.hierarchy()`.
- [ ] Controllare la classificazione delle eccezioni Python native.
- [ ] Controllare le classi specializzate già presenti.
- [ ] Verificare che gli errori non vengano inutilmente riconfezionati perdendo informazioni.
- [ ] Verificare i confini tra errori appartenenti a domini differenti.

### Revisione del flusso UI

Adottare progressivamente la convenzione:

**Renderer**
- stato operativo sintetico;
- informazioni immediatamente utili durante l'esecuzione.

**Storico console**
- descrizione dell'operazione fallita;
- identificazione dell'opera;
- report dell'errore;
- informazioni sul recovery;
- informazioni sul checkpoint;
- eventuali dettagli diagnostici.

- [ ] Audit di `base.py`.
- [ ] Audit di `download()`.
- [ ] Audit di `retrieve_bookmarks()`.
- [ ] Audit del rebuild/resume dei checkpoint.
- [ ] Audit degli errori filesystem.
- [ ] Audit degli errori API.
- [ ] Revisione specifica della gestione del rate limit.

### Strategie di gestione

Per ogni categoria di errore verificare esplicitamente la strategia prevista:

- Fatal
- Retry
- Continue
- Rate Limit
- Preserve checkpoint
- Discard singolo risultato

L'errore deve essere gestito nel livello in cui esiste abbastanza contesto per prendere una decisione corretta.

---

## 4. Normalizzazione del login

Il sistema di login deve essere riordinato e reso coerente con la struttura generale dell'applicazione.

### Profilo Chrome

Attualmente il profilo Chrome persistente utilizzato per il login è conservato nella home dell'utente.

Obiettivo:

- [ ] Spostare il profilo Chrome sotto la **root di default di PBD**.
- [ ] Definire una directory dedicata al browser/profile.
- [ ] Eliminare la dipendenza dal percorso attuale nella home.
- [ ] Centralizzare la determinazione del percorso.
- [ ] Verificare la creazione automatica della directory quando necessaria.
- [ ] Verificare il comportamento con installazione nuova.
- [ ] Verificare il comportamento con profilo già esistente.
- [ ] Valutare l'eventuale migrazione automatica o manuale del vecchio profilo.

Obiettivo architetturale:

> Riunire sotto la root di default dell'applicazione tutti i dati e le risorse persistenti appartenenti direttamente a PBD.

### Riordino del login

- [ ] Riesaminare l'intero flusso di autenticazione.
- [ ] Separare chiaramente login, browser automation e configurazione.
- [ ] Eliminare eventuali dipendenze non più necessarie.
- [ ] Verificare la gestione degli errori di autenticazione secondo il nuovo modello.
- [ ] Verificare il lifecycle del browser.
- [ ] Verificare la persistenza della sessione.

---

## 5. Riordino delle dipendenze

Il riordino era stato previsto insieme alla normalizzazione del login.

- [ ] Riesaminare le dipendenze Python attuali.
- [ ] Identificare quelle specifiche del login/browser automation.
- [ ] Identificare dipendenze obsolete o non più utilizzate.
- [ ] Controllare gli import.
- [ ] Verificare le dipendenze runtime rispetto a quelle esclusivamente di sviluppo.
- [ ] Verificare le dipendenze necessarie alla distribuzione PyInstaller.
- [ ] Mantenere separate le responsabilità dei diversi sottosistemi.

---

## 6. Riscansione completa dell'archivio

È prevista una nuova scansione completa delle opere già archiviate.

La scansione dovrà raccogliere informazioni aggiuntive rispetto a quella attuale.

### Author ID

- [ ] Rilevare l'ID Pixiv dell'autore di ogni opera.
- [ ] Associare stabilmente `artwork ID` e `author ID`.
- [ ] Verificare quali metadata già disponibili permettono di recuperarlo.
- [ ] Evitare richieste API aggiuntive quando l'informazione è già disponibile localmente.
- [ ] Definire il comportamento per opere con metadata incompleti.

La nuova scansione servirà come base per la riorganizzazione dell'archivio.

---

## 7. Nuova organizzazione delle opere per autore

Obiettivo: passare da una catalogazione basata essenzialmente sull'opera a una struttura che tenga conto anche dell'autore.

Schema concettuale:

`Autore → Opera → Media`

Da definire:

- [ ] struttura definitiva dei percorsi;
- [ ] identificazione dell'autore nel nome/percorso;
- [ ] gestione di nomi autore non validi come directory;
- [ ] gestione del cambio di nome dell'autore;
- [ ] ruolo dell'`author ID` come identificatore stabile;
- [ ] compatibilità con metadata e checkpoint;
- [ ] compatibilità con opere già archiviate.

### Test preliminare

- [ ] Eseguire nuovamente il test di catalogazione/raggruppamento usando gli `author ID` raccolti.
- [ ] Verificare la distribuzione delle opere per autore.
- [ ] Studiare i casi limite prima di modificare definitivamente il layout dell'archivio.

---

## 8. Migrazione dell'archivio esistente

Una volta stabilita la nuova struttura:

- [ ] riscansionare l'archivio esistente;
- [ ] determinare la destinazione di ogni opera;
- [ ] verificare duplicati e collisioni;
- [ ] verificare metadata;
- [ ] verificare checkpoint;
- [ ] verificare pending jobs;
- [ ] verificare rebuild/resume;
- [ ] progettare la migrazione senza perdita di dati;
- [ ] prevedere prima una modalità di simulazione/dry-run.

La migrazione dovrà essere affrontata soltanto dopo aver stabilizzato il modello dei percorsi.

---

## 9. Revisione checkpoint e rebuild

La nuova struttura dell'archivio può avere conseguenze sui meccanismi che fanno riferimento ai percorsi delle opere.

- [ ] Verificare `_download_artwork()`.
- [ ] Verificare `_download_media()`.
- [ ] Verificare creazione e rimozione checkpoint.
- [ ] Verificare rebuild dei pending job.
- [ ] Verificare resume.
- [ ] Verificare eventuali percorsi serializzati.
- [ ] Evitare che il cambio di struttura renda inutilizzabili checkpoint esistenti.

---

## 10. Distribuzione del progetto

Fase successiva, non prioritaria rispetto ai refactoring strutturali.

- [ ] Rivalutare la pubblicazione su PyPI.
- [ ] Verificare struttura del package.
- [ ] Verificare dipendenze runtime.
- [ ] Verificare distribuzione tramite PyInstaller.
- [ ] Definire cosa appartiene all'installazione e cosa alla root dati di PBD.
- [ ] Verificare gestione degli strumenti esterni, in particolare FFmpeg.

---

# Ordine di lavoro proposto

1. **Completare il test nominale Ugoira attualmente in corso.**
2. **Analizzare il rate limit realmente emerso durante il test.**
3. **Progettare ed eseguire i test di errore della pipeline Ugoira.**
4. **Revisione generale error handling / `PBDError.hierarchy()` / `notify()` / UI.**
5. **Normalizzazione login e spostamento del profilo Chrome nella root di default.**
6. **Riordino delle dipendenze.**
7. **Riscansione completa dell'archivio con acquisizione degli author ID.**
8. **Test della nuova catalogazione per autore.**
9. **Definizione definitiva della nuova struttura dei percorsi.**
10. **Migrazione dell'archivio esistente.**
11. **Verifica e adeguamento di checkpoint/rebuild/resume.**
12. **Successive attività di packaging e distribuzione.**

---

# Principio architetturale trasversale

Durante tutte le fasi:

> Evitare di risolvere un problema introducendo responsabilità improprie in componenti che appartengono ad altri domini.

In particolare:

- individuare il livello che possiede il contesto necessario per prendere una decisione;
- distinguere propagazione, gestione e notifica dell'errore;
- mantenere localizzato il lifecycle delle risorse;
- evitare duplicazioni della gestione degli errori;
- mantenere separate responsabilità di dominio, UI, filesystem e processi esterni;
- preferire modifiche piccole e verificabili;
- non trasformare automaticamente una proposta architetturale in implementazione senza averne prima valutato le conseguenze.