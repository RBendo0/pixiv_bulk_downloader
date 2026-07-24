# ROADMAP

## Stato attuale

L’architettura principale è sostanzialmente completata.
Sono operativi il sistema concorrente, il renderer, i principali workflow di download, la configurazione persistente e la gestione della Storage Root.

La fase corrente riguarda il completamento del porting alla nuova gestione degli errori e l’integrazione della conversione delle ugoira.

## Breve termine

* Completare il porting degli errori nei moduli residui, a partire da `animation`.
* Collaudare `StorageDirs`: default, configurazione, CLI e rami di errore simulati.
* Completare `MultiMediaManager`.
* Implementare conversione ugoira in GIF e WebM.
* Integrare la conversione nel workflow di download.
* Eseguire il collaudo generale dei workflow principali.
* Commit completo e aggiornamento di roadmap, Decision Log e documentazione.

## Medio termine

* Rifattorizzare completamente il login e la gestione della sessione.
* Rifattorizzare il flusso UI degli errori con messaggi multilinea e dettagli indentati.
* Uniformare la gestione delle eccezioni prodotte dalle librerie esterne.
* Consolidare build, dipendenze e struttura dell’eseguibile.
* Rimuovere codice obsoleto e completare i test automatici.

## Lungo termine

* Introdurre una classe centralizzata di debug e test.
* Esporre flag per sottosistema e metodi per simulare errori o comportamenti specifici.
* Automatizzare i test dei percorsi di errore.
* Convertire gli ZIP ugoira già presenti nell’archivio.
* Aggiungere backup automatici dei file operativi.
* Valutare supporto MP4 e ulteriori miglioramenti UI e prestazionali.

## Pubblicazione

* Verificare il repository pubblico.
* Aggiornare la documentazione online.
* Pubblicare un avviso sullo stato del progetto.
* Preparare il primo rilascio stabile.
