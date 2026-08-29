# PBD — Spunti per il prossimo refactoring dell'Encoder

## Contesto

Il lavoro sul Debug / Simulation ha portato all'introduzione di `DebuggedFFmpegProcess`, nato per permettere l'esecuzione del flusso reale di `Encoder` senza avviare realmente FFmpeg.

Il risultato ha avuto un effetto architetturale più ampio: la gestione concreta del processo FFmpeg è stata separata dalla logica dell'Encoder.

Oggi `Encoder` non gestisce più direttamente:

- `subprocess.Popen`
- `stdin`
- `stdin.closed`
- `poll()`
- `kill()`
- `wait()` come primitiva di processo
- apertura / chiusura / cancellazione del log FFmpeg

L'interazione col backend avviene invece tramite una piccola interfaccia specializzata:

```text
write(data)
close_input()
abort()
wait() -> FFmpegResult
```

`FFmpegResult` contiene:

```python
@dataclass(frozen=True)
class FFmpegResult:
    code: int
    log_file: Path
```

`code` è il dato primario che determina l'esito dell'esecuzione; `log_file` è sempre valorizzato con il percorso completo assegnato al log, ma la sua rilevanza dipende dal valore di `code`.

---

## Perché il refactoring ha migliorato l'architettura

La Simulation richiedeva di poter eseguire davvero la logica di `Encoder` senza dipendere dall'esecuzione reale di FFmpeg.

Questa necessità ha reso evidente che `Encoder` conosceva troppi dettagli implementativi del backend. L'introduzione del wrapper ha quindi aumentato separazione e incapsulamento.

Il punto importante è che il beneficio non è limitato al debug: il nuovo confine resta utile anche in assenza della Simulation.

In particolare, oggi il componente che esegue FFmpeg è molto più isolato e potenzialmente sostituibile.

Questo è simile alla pressione architetturale esercitata dalla TDD: voler testare o simulare un componente isolatamente costringe a rendere esplicite le sue dipendenze e a ridurre l'accoppiamento con i dettagli esterni.

---

## Cosa rimane ancora legato a FFmpeg dentro `Encoder`

### 1. Costruzione della command line FFmpeg

È il legame principale rimasto.

`Encoder` conosce ancora direttamente opzioni e sintassi specifiche di FFmpeg, tra cui:

```text
-filter_complex
-vf
-c:v
-crf
-pix_fmt
-movflags
image2pipe
pipe:0
```

Anche `_output_arguments()` traduce direttamente le intenzioni di encoding nella sintassi FFmpeg.

Questo significa che `Encoder` è ormai separato dall'esecuzione concreta del processo, ma non ancora dal linguaggio del backend.

Il confine residuo può essere espresso così:

```text
intenzione di encoding
        ↓
traduzione in argomenti FFmpeg
```

### 2. Eseguibile FFmpeg nel costruttore

`Encoder` riceve ancora esplicitamente:

```python
ffmpeg: Path
```

lo conserva in:

```python
self._ffmpeg
```

ed è `Encoder` stesso a inserirlo come primo elemento del comando.

Quindi la classe sa ancora che il backend concreto è un eseguibile FFmpeg.

### 3. Errore nominalmente specifico di FFmpeg

`Encoder.stop()` interpreta il risultato e, in caso di errore, genera ancora:

```python
FFmpegExecutionError
```

con un messaggio del tipo:

```text
FFmpeg exited with code ...
```

Questo legame è molto meno invasivo rispetto alla precedente gestione di `Popen`, ma rimane comunque una conoscenza esplicita del backend.

---

## Parti dell'Encoder già sostanzialmente indipendenti da FFmpeg

Le seguenti responsabilità appartengono al dominio dell'encoding e non dipendono direttamente da FFmpeg:

- validazione dei delay dei frame;
- calcolo del tick temporale comune;
- conteggio e avanzamento dei frame;
- gestione di overflow e underflow dello stream;
- protocollo `start() / add() / stop()`;
- decisione se l'encoding è riuscito sulla base del risultato restituito dal backend.

Questa è la parte che rende plausibile una futura sostituzione del backend senza riscrivere l'intero flusso.

---

## Possibile direzione del prossimo refactoring

Non implementare preventivamente un'astrazione universale.

Il prossimo refactoring dovrebbe partire da casi d'uso reali, come già fatto con `DebuggedFFmpegProcess`.

Se in futuro si rendesse necessario supportare un backend differente da FFmpeg, il punto naturale da estrarre sarebbe probabilmente la traduzione:

```text
MediaFormat + codec + output + timing
            ↓
istruzioni specifiche del backend
```

A quel punto si potrebbe valutare una separazione tra:

```text
Encoder
    ↓
backend di encoding
    ↓
FFmpeg / eventuale sostituto
```

ma solo quando esiste un'esigenza concreta che permetta di progettare l'interfaccia sulla base dell'uso reale.

---

## Principio architetturale da conservare

Il risultato ottenuto con il wrapper FFmpeg suggerisce una regola utile per i prossimi refactoring di PBD:

> Quando una modalità di debug, simulazione o test richiede di sostituire una risorsa esterna senza alterare la logica del chiamante, quella difficoltà può indicare che manca un confine architetturale tra responsabilità differenti.

L'obiettivo non è aggiungere astrazioni per principio, ma fare in modo che ogni componente conosca il minimo necessario delle proprie dipendenze.

Nel caso di FFmpeg, il refactoring ha già separato il **come eseguire il backend**. Il prossimo eventuale passo riguarderebbe il **come parlare al backend**.
