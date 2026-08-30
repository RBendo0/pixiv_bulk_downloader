# Debug Trace Binding

## 1. Due identificatori distinti

Il sistema usa due concetti:

**Debug ID**
- progressivo;
- identifica la **singola occorrenza** registrata da Debug;
- viene generato al momento della registrazione;
- deve seguire l'eccezione durante il suo percorso.

**Debug Section ID**
- identifica invece il **punto del programma** nel quale l'evento è stato generato;
- più Debug ID possono quindi riferirsi alla stessa Section ID.

Esempio:

```text
Debug ID 0000017 → Section 4
Debug ID 0000021 → Section 4
Debug ID 0000038 → Section 4
```

Il primo identifica *l'evento*, il secondo *il punto d'origine*.

## 2. L'associazione appartiene a Debug

Debug può associare dinamicamente il proprio ID a qualunque istanza di `Exception`, comprese eccezioni standard come `OSError`.

Concettualmente:

```python
error = OSError("Injected error")

debug.register(
    error,
    section_id=4,
    ...
)

raise error
```

Internamente Debug potrà fare qualcosa equivalente a:

```python
error._debug_id = 17
```

ma questo è deliberatamente un **dettaglio privato di Debug**.

Né `errors.py`, né `notify()`, né il resto di PBD devono conoscere il nome dell'attributo o il modo in cui viene memorizzato.

## 3. `register()` crea il binding

L'operazione concettuale è:

```python
debug.register(error, ...)
```

e ha la responsabilità di:

```text
genera Debug ID
        ↓
registra le informazioni Debug
        ↓
associa Debug ID all'istanza Exception
```

Il record contiene almeno le informazioni necessarie a ricostruire qualcosa del tipo:

```text
Debug ID 0000017: Raised APIError in section number: 4
```

Non abbiamo ancora fissato la struttura interna del record, né è necessario farlo ora.

## 4. Il contesto non viene standardizzato

Decisione importante già presa: **non esiste un contesto universale del Fault Injection**.

Il contesto dipende dal punto d'iniezione e può essere, per esempio:

```text
PixivMetadata
cartella/path
chiamata FFmpeg
operazione API
download
...
```

Debug deve quindi poter registrare l'informazione pertinente localmente senza imporre un oggetto-context comune.

## 5. Il binding segue l'eccezione

Questo è il cuore del meccanismo.

`PBDError.hierarchy()` oggi, quando riceve già una `PBDError`, restituisce la stessa istanza: in quel caso il binding sopravvive automaticamente.

Quando invece traduce un'eccezione:

```text
OSError
    ↓
FileOperationError
```

viene creata una nuova istanza e quindi il binding deve essere trasferito.

Lo stesso problema riguarda `cast()`, che crea sempre una nuova `PBDError`.

Per nascondere completamente il meccanismo introduciamo concettualmente:

```python
debug.inherit(new_error, old_error)
```

`inherit()` significa esclusivamente:

> La nuova eccezione deriva dalla precedente: conserva la sua eventuale associazione Debug.

Come lo faccia rimane affare di `debug.py`.

## 6. `errors.py` conosce Debug, non il suo internals

Questa distinzione è fondamentale.

Un `hierarchy()` può fare:

```python
new_error = FileOperationError(str(error))
debug.inherit(new_error, error)
return new_error
```

ma **non**:

```python
new_error._debug_id = error._debug_id
```

Quindi `errors.py` conosce l'interfaccia di Debug, ma non conosce il Debug Trace Binding.

Quando Debug è disattivato, `inherit()` può essere semplicemente un no-op. Di conseguenza tutta la gestione degli attributi clandestini scompare dal comportamento effettivo del programma.

Anche gli `hierarchy()` specializzati che producono nuove istanze dovranno rispettare lo stesso principio; nel file attuale accade, per esempio, in `ConfigError`, `MediaToolExecutableError` ed `EncoderStreamError`.

## 7. `notify()` è il punto di osservazione finale

`notify()` ha una proprietà molto utile per il Fault Injection: quando viene eseguito sappiamo che l'eccezione è effettivamente arrivata al sistema ordinario di gestione/notifica.

Oggi stampa la normale riga:

```text
[!]: <message>
```

e, opzionalmente, il report.

Con Debug attivo specializzerà leggermente il comportamento:

```python
if debug.enabled():
    debug_info = debug.error_info(self)
    ui.line(
        f"[#]: {debug_info}",
        ...
    )
```

seguito dal comportamento normale di `notify()`.

## 8. `error_info()` è l'unica interrogazione necessaria a `notify()`

La sua interfaccia concettuale è:

```python
debug.error_info(error) -> str
```

e Debug si occupa internamente di:

```text
Exception
    ↓
Debug ID associato
    ↓
record Debug
    ↓
messaggio
```

Risultato normale:

```text
Debug ID 0000017: Raised APIError in section number: 4
```

`notify()` non deve sapere come sia stato trovato l'ID.

## 9. Nessuna inferenza tramite truthiness

Decisione esplicita: **non useremo il valore restituito da `error_info()` per dedurre se Debug sia attivo o se la riga debba essere mostrata.**

Quindi niente:

```python
debug_info = debug.error_info(self)

if debug_info:
    ...
```

Lo stato viene interrogato direttamente:

```python
if debug.enabled():
    debug_info = debug.error_info(self)
    ...
```

Questo evita di attribuire implicitamente alla stringa vuota il significato «Debug non attivo».

## 10. Debug attivo ma binding assente è informazione diagnostica

Proprio per la decisione precedente, se `notify()` viene raggiunto con Debug attivo ma l'eccezione non possiede un Debug ID valido, la riga Debug **non deve necessariamente sparire**.

`error_info()` potrà restituire esplicitamente qualcosa come:

```text
Debug ID: not associated
```

oppure:

```text
Debug ID: invalid ID
```

La formulazione esatta resta da decidere.

Questo è utile perché una mancata associazione può rivelare un buco nella nostra stessa strumentazione.

## 11. Marcatore UI Debug

Confermato:

```text
[#]:
```

Il `#` richiama identificazione/numerazione e ha l'aspetto di un messaggio di sistema senza confondersi con il normale errore `[!]`.

La resa sarà quindi indicativamente:

```text
[#]: Debug ID 0000017: Raised APIError in section number: 4
[!]: Failed to retrieve bookmarks
```

Il colore Debug dedicato rimane da scegliere.

## 12. Fault Injection e normali errori possono usare lo stesso meccanismo

Infine, il Debug Trace Binding **non è limitato agli errori creati artificialmente**.

Nel Fault Injection:

```text
Debug crea errore
→ registra Debug ID
→ binding
→ raise
```

In un punto in cui il normale codice genera già l'errore:

```text
codice determina l'errore
→ Debug, se attivo, lo registra
→ binding
→ normale raise
```

Da quel momento il percorso è identico:

```text
                 Debug Trace Binding
                         │
Exception ───────────────┘
    ↓
hierarchy / cast
    ↓
debug.inherit()
    ↓
PBDError
    ↓
notify()
    ↓
debug.error_info()
    ↓
[#]: Debug ID ... Section ...
[!]: normale notifica PBD
```

**Debug Trace Binding** identifica precisamente questa parte dell'infrastruttura, lasciando `Fault Injection` come concetto superiore: il Fault Injection *usa* il Debug Trace Binding, ma non coincide con esso.
