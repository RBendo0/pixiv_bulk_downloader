# ROADMAP

## Stato attuale

L’architettura principale è sostanzialmente completata.
È stata completata l’integrazione della conversione delle ugoira (GIF, WebM e MP4) direttamente nel workflow di download, mantenendo invariata l’architettura concorrente.

La fase corrente riguarda il consolidamento della gestione degli errori e il completamento del refactoring dell’infrastruttura.

## Breve termine

* Completare il porting degli errori nei moduli residui.
* Rifattorizzare la gerarchia degli errori, introducendo una `Hierarchy` specializzata per dominio.
* Collaudare `StorageDirs`: default, configurazione, CLI e rami di errore simulati.
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
* Valutare ulteriori miglioramenti UI e prestazionali.

## Pubblicazione

* Verificare il repository pubblico.
* Aggiornare la documentazione online.
* Pubblicare un avviso sullo stato del progetto.
* Preparare il primo rilascio stabile.