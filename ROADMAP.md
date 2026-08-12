# ROADMAP — Pixiv Bulk Downloader

## Stato attuale

### Completato

- [x] Integrazione encoder FFmpeg streaming per Ugoira.
- [x] Lifecycle Encoder definito come `start()` → `add()` → `stop()`.
- [x] Gestione e propagazione degli errori Ugoira integrata nella gerarchia `PBDError`.
- [x] Distinzione tra errori fatali dell'animazione ed errori limitati al singolo formato.
- [x] Recovery dell'Encoder tramite `stop(ignore_errors=True)`.
- [x] Gestione ZIP Ugoira tramite context manager e validazione preventiva dei frame.
- [x] Integrazione degli errori concorrenti con renderer e storico console.
- [x] Gestione rate limit durante il download con countdown, attesa e retry automatico.
- [x] Nuova struttura di archiviazione con bucketing di primo livello per autore.
- [x] Introduzione del metadata autore separato dal metadata dell'opera.
- [x] Introduzione di `illust_detail()` come sorgente del metadata completo dell'opera.
- [x] Conservazione dell'envelope `illust` nel metadata artwork.
- [x] Aggiornamento dell'interfaccia `PixivMetadata` alla nuova struttura.
- [x] Eliminazione della gestione delle opere cancellate tramite `author_id == 0`.
- [x] Eliminazione del bucketing di secondo livello e della cartella autore `0`.

---

## 1. Verifica immediata — nuovo sistema metadata/storage

- [ ] Eseguire test integrato del nuovo flusso `retrieve_bookmarks()`.
- [ ] Verificare chiamata `illust_detail()` per ogni opera.
- [ ] Verificare esclusione delle opere cancellate tramite `artwork_data.has_error`.
- [ ] Verificare che per le opere cancellate non venga effettuata la chiamata `user_detail()`.
- [ ] Verificare salvataggio del metadata artwork con struttura `metadata -> illust`.
- [ ] Verificare salvataggio del metadata autore.
- [ ] Verificare corretto funzionamento di `artw_id`, `artw_title`, `artw_type`, `artw_get_links`, `author_id` e `author_name`.
- [ ] Verificare struttura finale:
  - bucket di primo livello;
  - cartella autore;
  - cartella opera.
- [ ] Verificare che non venga più generata alcuna cartella autore `0`.
- [ ] Verificare assenza di regressioni nel download effettivo delle opere.
- [ ] Verificare checkpoint e ripresa del download con la nuova struttura.

---

## 2. Renderer — slot di stato e temporizzatore

- [ ] Aggiungere al renderer una riga permanente sotto gli slot dei worker.
- [ ] Definire uno slot di stato globale indipendente dagli slot dei thread.
- [ ] Visualizzare nello slot di stato il tempo trascorso dall'inizio dell'operazione.
- [ ] Definire il formato del temporizzatore.
- [ ] Valutare quali ulteriori informazioni globali mostrare nello slot di stato.
- [ ] Mantenere separati:
  - slot worker = stato delle singole operazioni concorrenti;
  - slot di stato = informazioni globali dell'esecuzione.

---

## 3. Test end-to-end Ugoira

- [ ] Eseguire test completo del normale flusso Ugoira.
- [ ] Verificare generazione GIF.
- [ ] Verificare generazione WEBM.
- [ ] Verificare generazione MP4.
- [ ] Verificare aggiornamento progressivo del renderer.
- [ ] Verificare messaggi finali `GIF completed`, `WEBM completed`, `MP4 completed`.
- [ ] Verificare assenza di regressioni nel download delle opere non-Ugoira.
- [ ] Verificare rimozione del checkpoint in caso di successo completo.

---

## 4. Debug rapido / fault injection

Realizzare un sistema semplice e temporaneo che permetta di provocare artificialmente gli errori nei punti significativi della pipeline, senza dover riprodurre manualmente ogni condizione reale.

Obiettivo: poter attraversare rapidamente tutti i failure path e verificare error handling, UI, checkpoint e recovery.

### Ugoira / Encoder

- [ ] Simulare struttura `frames` non valida.
- [ ] Simulare frame dichiarato nei metadata ma assente nello ZIP.
- [ ] Simulare ZIP mancante, non valido o corrotto.
- [ ] Simulare errore durante `archive.read()`.
- [ ] Simulare errore di avvio FFmpeg.
- [ ] Simulare errore durante `Encoder.add()`.
- [ ] Simulare FFmpeg con return code diverso da zero.
- [ ] Verificare `stop(ignore_errors=True)` durante il recovery.
- [ ] Verificare che l'errore primario non venga sostituito da eventuali errori di terminazione.
- [ ] Verificare `FORMAT discarded` per errore limitato al singolo formato.
- [ ] Verificare `Animation building failed` per errore fatale.

### Pipeline generale

- [ ] Estendere il sistema di fault injection ai principali punti critici di PBD.
- [ ] Simulare errori filesystem.
- [ ] Simulare errori API.
- [ ] Simulare rate limit dove necessario.
- [ ] Simulare errori durante download e salvataggio.
- [ ] Verificare comportamento dei checkpoint per ogni failure path.
- [ ] Verificare comportamento Fatal / Retry / Continue / Rate Limit.

---

## 5. Refactoring generale error handling

- [ ] Audit completo della gerarchia `PBDError`.
- [ ] Audit completo dei vecchi `PBDError.cast()`.
- [ ] Migrare dove opportuno da `cast()` a `hierarchy()`.
- [ ] Verificare che ogni livello intercetti soltanto gli errori di propria competenza.
- [ ] Evitare traduzioni o intercettazioni duplicate dello stesso errore.
- [ ] Audit error handling di `base.py`.
- [ ] Audit error handling di `retrieve_bookmarks()`.
- [ ] Audit error handling di `download()`.
- [ ] Audit error handling della pipeline Ugoira/Encoder.
- [ ] Mappatura degli errori filesystem.
- [ ] Mappatura degli errori API.
- [ ] Riesaminare sistematicamente le strategie:
  - Fatal;
  - Retry;
  - Continue;
  - Rate Limit.
- [ ] Verificare conservazione/rimozione dei checkpoint nei diversi failure path.
- [ ] Verificare conservazione/eliminazione dei log FFmpeg nei diversi esiti.

---

## 6. Refactoring flusso UI degli errori

- [ ] Riesaminare globalmente la presentazione degli errori.
- [ ] Consolidare l'utilizzo di `PBDError.notify()`.
- [ ] Definire chiaramente la responsabilità dei due canali:
  - renderer = stato operativo sintetico;
  - storico console = contesto e diagnosi persistente.
- [ ] Eliminare messaggi duplicati tra renderer e storico.
- [ ] Uniformare formulazione, livello di dettaglio e colori dei messaggi.
- [ ] Verificare comportamento della UI durante errori provenienti dai worker concorrenti.
- [ ] Verificare sospensione e ripristino sicuro del renderer durante le notifiche.
- [ ] Integrare il nuovo slot di stato globale con il modello UI definitivo.

---

## 7. Refactoring login e autenticazione Pixiv

- [ ] Riesaminare l'intero flusso di autenticazione.
- [ ] Separare chiaramente:
  - acquisizione delle credenziali/token;
  - autenticazione;
  - persistenza;
  - refresh;
  - gestione degli errori.
- [ ] Riesaminare responsabilità e dipendenze tra login, configurazione e `PixivCallAPI`.
- [ ] Verificare gestione del refresh token.
- [ ] Verificare comportamento con credenziali/token mancanti, scaduti o non validi.
- [ ] Eliminare eventuale logica legacy o ridondante.
- [ ] Valutare la struttura definitiva del login prima di procedere all'implementazione.

---

## 8. Dipendenze e packaging

- [ ] Audit delle dipendenze Python effettivamente utilizzate.
- [ ] Eliminare dipendenze non più necessarie.
- [ ] Verificare distinzione tra dipendenze runtime e dipendenze di sviluppo.
- [ ] Riesaminare gestione delle dipendenze esterne, in particolare FFmpeg.
- [ ] Verificare struttura delle dipendenze in vista della distribuzione.
- [ ] Riesaminare configurazione PyInstaller.
- [ ] Verificare esecuzione dell'EXE in ambiente pulito.
- [ ] Verificare PATH e risoluzione degli strumenti esterni senza dipendere dall'ambiente di sviluppo.

---

## 9. Distribuzione e conservazione delle dipendenze

- [ ] Definire la strategia di distribuzione di PBD:
  - sorgente Python;
  - eseguibile PyInstaller;
  - eventuale pacchetto installabile.
- [ ] Stabilire quali dipendenze mantenere esterne durante lo sviluppo.
- [ ] Valutare il vendoring o l'archiviazione locale delle dipendenze critiche, in particolare:
  - `my_gppt`;
  - `pixivpy3`.
- [ ] Distinguere tra:
  - dipendenze runtime dell'ambiente di sviluppo;
  - dipendenze incorporate nell'eseguibile;
  - snapshot di conservazione a lungo termine.
- [ ] Definire una strategia per poter ricostruire una release anche in futuro, indipendentemente dalla disponibilità dei repository originali.
- [ ] Valutare il salvataggio delle versioni esatte delle dipendenze usate per ogni release.
- [ ] Verificare quali componenti esterne non sono realmente inglobate nell'eseguibile e richiedono distribuzione separata.

---

## Ordine di lavoro previsto

1. Test integrato del nuovo sistema metadata/storage.
2. Slot di stato e temporizzatore del renderer.
3. Test end-to-end Ugoira.
4. Sistema di debug rapido / fault injection.
5. Refactoring generale dell'error handling.
6. Refactoring del flusso UI degli errori.
7. Refactoring login/autenticazione.
8. Audit dipendenze e packaging.