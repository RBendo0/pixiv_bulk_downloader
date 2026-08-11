## TODO ATTUALE — Ugoira / Error handling

### Completato

- [x] Integrazione encoder FFmpeg streaming nella pipeline Ugoira.
- [x] Protocollo Encoder definito come `start()` → `add()` → `stop()`.
- [x] `Encoder.start()`, `add()` e `stop()` normalizzano le eccezioni tramite la gerarchia `PBDError`.
- [x] Rimossa da `start()` e `add()` la responsabilità di terminare autonomamente le risorse in caso di errore.
- [x] `stop()` centralizzato come routine di terminazione dell'Encoder.
- [x] Aggiunto `stop(ignore_errors=True)` per i percorsi di recovery con errore già attivo.
- [x] Separato il reset dello stato interno dalla terminazione delle risorse tramite `_reset()`.
- [x] Validazione preventiva della struttura dei frame.
- [x] Verifica preventiva della corrispondenza tra metadata dei frame e contenuto dello ZIP Ugoira.
- [x] Apertura dello ZIP una sola volta per l'intera `build_animation()`.
- [x] Gestione automatica del lifecycle dello ZIP tramite context manager.
- [x] Introdotta `AnimationError` come dominio comune degli errori di animazione e superclasse di `EncoderError`.
- [x] Distinti gli errori fatali dell'intera animazione dagli errori del singolo formato.
- [x] Gestione locale degli errori del singolo formato in `build_animation()`:
  - notifica nello storico;
  - stato `discarded` nel renderer;
  - prosecuzione con i formati successivi.
- [x] Propagazione degli errori fatali dell'animazione verso `_download_media()`.
- [x] Gestione dedicata di `AnimationError` in `_download_media()`.
- [x] Separata la presentazione degli errori:
  - renderer = stato operativo sintetico;
  - storico console = contesto e report diagnostico.
- [x] Integrato `PBDError.notify()` nel flusso concorrente con sospensione sicura del renderer.
- [x] Sostituito in `_download_media()` il vecchio `PBDError.cast()` con `PBDError.hierarchy()`.
- [x] Conservazione del checkpoint collegata al fallimento della conversione tramite `return False`.

### Rate limit download — test reale superato

- [x] Intercettazione del rate limit durante il download di un media.
- [x] Visualizzazione del countdown nel renderer.
- [x] Attesa di 60 secondi.
- [x] Nessun blocco degli altri worker/thread pool.
- [x] Retry automatico del media interessato.
- [x] Download del media completato dopo il retry.
- [x] Opera completata correttamente.
- [x] File metadata presente.
- [x] Checkpoint rimosso dopo il completamento.

### Verifica immediata

- [ ] Eseguire test end-to-end del normale flusso Ugoira.
- [ ] Verificare generazione GIF.
- [ ] Verificare generazione WEBM.
- [ ] Verificare generazione MP4.
- [ ] Verificare aggiornamento progressivo del renderer.
- [ ] Verificare messaggi finali `GIF completed`, `WEBM completed`, `MP4 completed`.
- [ ] Verificare assenza di regressioni nel download delle opere non-Ugoira.
- [ ] Verificare rimozione del checkpoint in caso di successo completo.

### Test dedicati error handling Ugoira

Da progettare come test riproducibili tramite fault injection.

- [ ] Simulare struttura `frames` non valida.
- [ ] Simulare frame dichiarato nei metadata ma assente nello ZIP.
- [ ] Simulare ZIP mancante, non valido o corrotto.
- [ ] Simulare errore durante `archive.read()`.
- [ ] Simulare errore di avvio FFmpeg.
- [ ] Simulare errore durante `Encoder.add()`.
- [ ] Simulare FFmpeg con return code diverso da zero.
- [ ] Verificare `stop(ignore_errors=True)` durante il recovery.
- [ ] Verificare che l'errore primario non venga sostituito da eventuali errori di terminazione.
- [ ] Verificare notifica nello storico con ID opera e report specifico.
- [ ] Verificare `FORMAT discarded` per errore limitato al singolo formato.
- [ ] Verificare `Animation building failed` per errore fatale dell'intera animazione.
- [ ] Verificare conservazione del checkpoint nei failure path previsti.
- [ ] Verificare conservazione/eliminazione dei log FFmpeg nei diversi esiti.

### Prossima fase — revisione generale error handling

- [ ] Audit completo dei vecchi `PBDError.cast()`.
- [ ] Migrare dove opportuno da `cast()` a `hierarchy()`.
- [ ] Riesaminare il flusso UI degli errori alla luce di `PBDError.notify()`.
- [ ] Separare sistematicamente:
  - renderer = stato sintetico;
  - storico = diagnosi persistente.
- [ ] Audit error handling di `base.py`.
- [ ] Audit error handling di `retrieve_bookmarks()`.
- [ ] Audit error handling di `download()`.
- [ ] Mappatura errori filesystem.
- [ ] Mappatura errori API.
- [ ] Verifica delle strategie Fatal / Retry / Continue / Rate Limit.