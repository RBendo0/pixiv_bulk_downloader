ROADMAP IMMEDIATA

1. Conversione automatica delle Ugoira
-------------------------------------
Obiettivo:
- Implementare gli encoder per convertire automaticamente gli archivi ZIP delle ugoira nelle animazioni finali.

Decisioni:
- La conversione sarà parte integrante del flusso di download.
- L'utente finale non dovrà gestire manualmente gli archivi ZIP.


2. Rifattorizzazione gestione errori (Config / StorageDirs)
-----------------------------------------------------------
Obiettivo:
- Portare Config e StorageDirs alla nuova architettura PBDError.

Decisioni:
- Eliminare la gestione eterogenea delle eccezioni.
- Utilizzare sistematicamente:
    PBDError.hierarchy(...)
    report()
- Uniformare il comportamento al resto dell'applicazione.


3. Porting di Bookmarks al nuovo sistema di report
--------------------------------------------------
Obiettivo:
- Sostituire i vecchi messaggi di errore con report().

Decisioni:
- Anche gli errori non bloccanti devono essere mostrati in console.
- Ogni catch che prosegue l'esecuzione dovrà comunque produrre un report uniforme.
- Dove necessario utilizzare:
    e = PBDError.hierarchy(e)
prima della stampa.


4. Generalizzazione della scansione dell'archivio
-------------------------------------------------
Obiettivo:
- Sostituire rebuild_index() con un'infrastruttura generale di scansione.

Decisioni architetturali:
- Il nuovo scan_archive() attraversa TUTTO l'archivio senza applicare filtri.
- Per ogni cartella individua:
    • fetch (se presente)
    • metadata (se presente)
- Invoca una funzione callback passando:
    worker(fetch_file | None, metadata_file | None)
- scan_archive() conosce soltanto la struttura dell'archivio.
- La callback decide:
    • quali opere ignorare;
    • quale file caricare;
    • quali dati estrarre;
    • come costruire il risultato.
- rebuild_index(), retrieve_bookmarks() e futuri utilizzi diventeranno semplici callback specializzate.