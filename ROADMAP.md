# ROADMAP

## Stato del progetto

L'architettura principale è completata.
La fase corrente è dedicata al completamento del supporto alle ugoira e al consolidamento finale dell'applicazione.

## Milestone completate

- Architettura applicativa
- Thread Pool System
- Renderer concorrente
- Workflow di download
- Sistema di configurazione persistente
- Gestione della storage root
- Collaudo del sistema di configurazione

---

# 1. Conversione ugoira (fase corrente)

Completare la conversione delle ugoira in GIF e WebM e integrarla nel workflow di download.

Attività:
- conversione GIF;
- conversione WebM;
- configurazione codec;
- integrazione nel downloader;
- collaudo.

---

# 2. Consolidamento delle dipendenze

Ridurre l'accoppiamento con le librerie esterne e consolidare i confini dell'architettura.

---

# 3. Revisione del login

Rifinire il workflow di autenticazione, la gestione della sessione e la presentazione dei messaggi.

---

# 4. Revisione delle librerie esterne

Uniformare l'integrazione con PixivPy3, Playwright, my_gppt e FFmpeg.

---

# 5. Collaudo generale

Validare tutti i workflow applicativi e il pacchetto distribuito.

---

# 6. Documentazione

Aggiornare DecisionLog, documentazione tecnica e reportistica.

---

# 7. Pubblicazione

Verificare il repository, aggiornare la documentazione pubblica e preparare il rilascio.

---

# 8. Evoluzioni future

Miglioramenti non prioritari: UI, prestazioni, backup automatici, nuove funzionalità.