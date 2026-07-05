# Registro USESCASE – ERRS

## USESCASE #001 – Errore in fase di inizializzazione

**Contesto**

Recupero di informazioni preliminari (`user_detail`, `total`, ecc.) prima dell'avvio del flusso principale.

**Osservazioni**

- avviene prima del `while`;
- non esiste ancora una pagina corrente;
- oggi termina con messaggio + `return`;
- in futuro potrebbe degradare il servizio (es. proseguire senza `total`).

---

## USESCASE #002 – La stessa classe di errore può richiedere strategie diverse

La classe dell'errore non determina automaticamente la strategia di recovery.

Lo stesso `ApiError` può richiedere:

- terminazione;
- retry;
- prosecuzione;
- semplice propagazione.

La strategia dipende dal caso d'uso.

---

## USESCASE #003 – L'interfaccia di `handle()`

È emersa la necessità che `handle()` possa adattarsi a contesti differenti.

Per il momento la progettazione dell'interfaccia viene rimandata fino al completamento dell'analisi dei casi d'uso.

---

## USESCASE #004 – Il look-ahead produceva uno sfasamento logico

L'utilizzo di `next_json` anticipava la lettura della pagina successiva.

Conseguenze:

- errori riferiti alla pagina N+1 gestiti durante la pagina N;
- necessità di compensazioni (`page_number -= 1`);
- maggiore complessità del flusso.

Decisione:

- eliminazione completa del look-ahead;
- ritorno ad un flusso lineare basato sulla pagina corrente.

---

## USESCASE #005 – Terminazione naturale della modalità `chrono`

La modalità `chrono` termina quando incontra il primo artwork già presente nel database locale.

La terminazione è una normale conclusione della funzione:

```python
return urls
```

---

## USESCASE #006 – Separazione tra classificazione, presentazione e recovery

Nel blocco `except` sono emerse tre responsabilità distinte:

- classificazione dell'errore (`PBDError.from_exception()`);
- presentazione del messaggio contestuale;
- strategia di recupero (`handle()`).

La costruzione dei messaggi rimane responsabilità del caso d'uso, poiché dipende dal contesto operativo (pagina, artwork, file, ecc.).

`PBDError` si occupa della classificazione dell'errore. L'eventuale gestione dell'errore viene demandata al metodo virtuale handle(), la cui implementazione dipende dalla specifica classe di errore e dal caso d'uso.

---

## USESCASE #007 – La gestione degli errori non è sempre necessaria

L'analisi di `add_list_to_bookmarks()` ha evidenziato che non tutti i casi d'uso richiedono una gestione interattiva degli errori.

Se il flusso possiede già un meccanismo naturale di ripresa (ad esempio una lista persistente di URL ancora da elaborare), può essere sufficiente:

- classificare l'errore;
- terminare il processo;
- lasciare invariato lo stato dell'operazione.

Principio:

> ERRS non deve imporre una strategia di recovery. La gestione degli errori deve essere proporzionata al valore che apporta al caso d'uso.
