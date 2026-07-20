# ROADMAP

## Stato del progetto

L'architettura principale è sostanzialmente completata.

La fase corrente è dedicata al completamento del supporto alle ugoira e al consolidamento dell'intero workflow di download.

## Milestone completate

* Architettura applicativa
* Thread Pool System (TPS)
* Renderer concorrente
* Workflow di download multi-thread
* Gestione unificata degli errori
* Sistema di configurazione persistente
* Gestione della Storage Root
* Refactoring della configurazione multimediale
* Migrazione delle impostazioni a dataclass
* Configurazione dei codec avanzati
* Collaudo del nuovo sistema di configurazione

---

# 1. Conversione ugoira (fase corrente)

Completare il modulo `MultiMediaManager` e integrarlo nel downloader.

Attività immediate:

* completamento di `set_preferred_media_formats()`;
* caricamento delle immagini dell'ugoira;
* costruzione della sequenza di `AnimationFrame`;
* generazione GIF;
* generazione WebM;
* integrazione della conversione nel workflow di download;
* collaudo completo della pipeline.

---

# 2. Consolidamento architetturale

Completare il disaccoppiamento dai componenti esterni e rifinire i punti di integrazione.

---

# 3. Revisione del login

Consolidare autenticazione, gestione della sessione e presentazione degli errori.

---

# 4. Revisione delle librerie esterne

Uniformare l'integrazione con PixivPy3, Playwright, my_gppt e FFmpeg.

---

# 5. Collaudo generale

Validare tutti i workflow dell'applicazione:

* download;
* resume;
* missing;
* chrono;
* add bookmarks;
* conversione ugoira;
* configurazione.

---

# 6. Documentazione

Aggiornare Decision Log, roadmap e documentazione tecnica.

---

# 7. Pubblicazione

* verifica del repository pubblico;
* aggiornamento della documentazione online;
* preparazione del primo rilascio pubblico.

---

# 8. Evoluzioni future

Attività non prioritarie:

* conversione automatica degli archivi ZIP delle ugoira;
* backup automatico dei file operativi;
* miglioramenti della UI;
* ottimizzazioni prestazionali;
* funzionalità aggiuntive.
