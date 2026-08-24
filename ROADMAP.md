# ROADMAP — Pixiv Bulk Downloader

## Stato attuale

### Completato

- [x] Porting del nuovo modello metadata/storage.
- [x] Pipeline di scansione archivio e modalità All Missing / Resume Pending.
- [x] Download concorrente tramite artwork pool e image pool.
- [x] Pipeline Ugoira con encoder FFmpeg streaming.
- [x] Renderer concorrente con slot worker e status globale.
- [x] Gestione rate limit e interruzione controllata.
- [x] Reportistica finale del download.
- [x] Revisione del login/autenticazione Pixiv.
- [x] Revisione delle dipendenze Python.
- [x] Eliminazione delle dipendenze locali legacy `my_gppt` / `my_pixivpy3`.
- [x] Migrazione e verifica su Python 3.14.
- [x] Aggiornamento e pulizia del `pyproject.toml`.
- [x] Verifica build PyInstaller.
- [x] Snapshot locale delle dipendenze in `third_party`.

---

## 1. Normalizzazione del flusso UI degli errori

Il renderer e il modello generale di gestione degli errori sono già definiti.

L'intervento riguarda esclusivamente la normalizzazione della presentazione degli errori, passando dalle attuali stampe monoriga alle notifiche multiriga persistenti tramite `PBDError.notify()`.

- [ ] Individuare le stampe degli errori ancora gestite in forma monoriga.
- [ ] Convertirle all'utilizzo di `PBDError.notify()`.
- [ ] Uniformare la presentazione degli errori come notifiche multiriga persistenti.
- [ ] Verificare il comportamento delle notifiche durante l'esecuzione concorrente e con renderer attivo.

### Rate limit consecutivi

Esiste un problema noto nella presentazione di rate limit consecutivi: un precedente messaggio di rate limit può rimanere associato alla riga operativa e interferire con quelli successivi, falsando la formattazione.

- [ ] Riesaminare la presentazione del rate limit nel nuovo flusso basato su `notify()`.
- [ ] Eliminare l'accumulo dei messaggi di rate limit sulla riga operativa.
- [ ] Verificare sequenze di rate limit ripetuti/consecutivi.
- [ ] Verificare che le notifiche successive non provochino disallineamenti o alterazioni del renderer.

---

## 2. Debug rapido / fault injection

Realizzare un sistema semplice che permetta di provocare artificialmente gli errori nei punti significativi della pipeline, senza dover riprodurre manualmente ogni condizione reale.

Obiettivo: attraversare rapidamente i failure path e verificare error handling, UI, checkpoint e recovery.

La struttura definitiva del sistema di fault injection non è ancora stata decisa.

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
- [ ] Verificare errore limitato al singolo formato.
- [ ] Verificare errore fatale dell'animazione.

### Pipeline generale

- [ ] Estendere il fault injection ai principali punti critici di PBD.
- [ ] Simulare errori filesystem.
- [ ] Simulare errori API.
- [ ] Simulare rate limit dove necessario.
- [ ] Simulare errori durante download e salvataggio.
- [ ] Verificare comportamento dei checkpoint nei diversi failure path.
- [ ] Verificare recovery dopo interruzioni ed errori.
- [ ] Verificare comportamento Fatal / Retry / Continue / Rate Limit.

---

## 3. Revisione dell'error handling durante i test

La revisione dell'error handling verrà effettuata durante il fault injection e i test finali, intervenendo sui problemi effettivamente riscontrati.

- [ ] Verificare la gerarchia `PBDError`.
- [ ] Riesaminare i vecchi `PBDError.cast()`.
- [ ] Migrare dove opportuno da `cast()` a `hierarchy()`.
- [ ] Verificare che ogni livello intercetti soltanto gli errori di propria competenza.
- [ ] Eliminare eventuali traduzioni o intercettazioni duplicate.
- [ ] Verificare gli errori filesystem.
- [ ] Verificare gli errori API.
- [ ] Verificare gli errori del download.
- [ ] Verificare gli errori della pipeline Ugoira/Encoder.
- [ ] Verificare checkpoint e recovery nei failure path.
- [ ] Riesaminare dove necessario le strategie:
  - Fatal;
  - Retry;
  - Continue;
  - Rate Limit.
- [ ] Verificare conservazione/eliminazione dei log FFmpeg nei diversi esiti.

---

## 4. Test finali complessivi

- [ ] Eseguire il flusso completo di PBD dopo il consolidamento dell'error handling.
- [ ] Verificare assenza di regressioni nella scansione dell'archivio.
- [ ] Verificare All Missing e Resume Pending.
- [ ] Verificare download concorrente.
- [ ] Verificare opere normali e Ugoira.
- [ ] Verificare interruzione controllata.
- [ ] Verificare checkpoint e ripresa.
- [ ] Verificare renderer e reportistica finale.
- [ ] Verificare comportamento dopo errori recuperabili e non recuperabili.

---

## 5. Distribuzione

- [ ] Definire la strategia complessiva di distribuzione di PBD:
  - sorgente Python;
  - eseguibile PyInstaller;
  - eventuale package installabile;
  - eventuale pubblicazione PyPI.
- [ ] Definire il ruolo dell'eseguibile PyInstaller.
- [ ] Riesaminare la distribuzione di FFmpeg.
- [ ] Distinguere chiaramente ciò che viene incorporato nell'eseguibile da ciò che deve essere distribuito separatamente.
- [ ] Verificare l'esecuzione dell'EXE in ambiente pulito.
- [ ] Verificare PATH e risoluzione degli strumenti esterni senza dipendere dall'ambiente di sviluppo.
- [ ] Verificare la ricostruibilità utilizzando lo snapshot `third_party`.
- [ ] Verificare la riproducibilità della build in ambiente pulito.
- [ ] Valutare eventuale preparazione alla distribuzione pubblica/PyPI.

---

## Ordine di lavoro previsto

1. Normalizzazione del flusso UI degli errori tramite `PBDError.notify()`.
2. Correzione della presentazione dei rate limit consecutivi.
3. Sistema di debug rapido / fault injection.
4. Test dei failure path e revisione dell'error handling.
5. Test finali complessivi.
6. Strategia di distribuzione.
7. Test finale di build e riproducibilità in ambiente pulito.
8. Eventuale preparazione alla distribuzione pubblica/PyPI.