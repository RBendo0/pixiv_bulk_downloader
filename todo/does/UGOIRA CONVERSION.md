## Conversione ugoira — decisioni progettuali

### Modulo dedicato

La gestione della conversione sarà raccolta in un nuovo modulo, indicativamente:

```text
ugoira.py
```

Il modulo conterrà:

* le routine che interpretano i metadata Pixiv;
* la routine che legge le immagini dallo ZIP;
* la costruzione della struttura dati normalizzata;
* il convertitore GIF;
* il convertitore WebM.

`download_media()` manterrà invece il coordinamento generale:

* download dello ZIP;
* invocazione delle conversioni;
* aggiornamento di contatori e interfaccia;
* gestione dell’esito e degli errori.

---

### Struttura dati dei frame

I metadata Pixiv forniscono una sequenza ordinata composta da:

```python
{
    "file": "000000.jpg",
    "delay": 70,
}
```

Il modulo ugoira userà questi dati per leggere dallo ZIP la relativa immagine e costruire una struttura normalizzata:

```python
frames = [
    (image, delay),
    ...
]
```

dove:

* `image` è un’immagine Pillow caricata in memoria;
* `delay` è la durata del frame espressa in millisecondi.

Le immagini saranno lette direttamente dallo ZIP tramite `zipfile` e `BytesIO`, senza estrazione permanente su disco.

---

### Conversione GIF

La GIF sarà generata direttamente con Pillow.

Il convertitore riceverà la sequenza normalizzata dei frame e userà i singoli delay forniti da Pixiv, preservando quindi la temporizzazione originale dell’ugoira.

Il file GIF sarà salvato direttamente nel percorso definitivo indicato dal chiamante.

---

### Conversione WebM

La WebM sarà generata tramite una build Windows statica e completa di FFmpeg, distribuita insieme all’applicazione.

Indicativamente:

```text
tools/
    ffmpeg.exe
```

FFmpeg sarà invocato tramite `subprocess`.

La conversione userà una sequenza a durata variabile, senza trasformare i delay in un FPS medio, così da preservare fedelmente la temporizzazione di ogni frame.

FFmpeg scriverà direttamente il file `.webm` nel percorso definitivo.

Il modulo dovrà:

1. preparare gli input temporanei necessari a FFmpeg;
2. costruire il comando;
3. avviare `ffmpeg.exe`;
4. verificare il codice di uscita;
5. eliminare i file temporanei;
6. lasciare il WebM nella cartella dell’opera.

---

### Codec WebM

Il codec non sarà fissato direttamente nel convertitore.

In `const.py` sarà definito il codec predefinito, inizialmente:

```python
DEFAULT_WEBM_CODEC = "vp9"
```

La configurazione utente conterrà il codec attualmente selezionato:

```text
webm_codec = vp9
```

Nel menu di configurazione sarà aggiunta una voce che permetterà di sostituire il codec corrente.

I codec inizialmente previsti sono:

```text
VP8
VP9
AV1
```

La configurazione conserverà il nome logico del codec, mentre il codice lo tradurrà nell’encoder FFmpeg corrispondente:

```python
WEBM_ENCODERS = {
    "vp8": "libvpx",
    "vp9": "libvpx-vp9",
    "av1": "libaom-av1",
}
```

Il codec predefinito sarà VP9, scelto come compromesso tra qualità, dimensione, velocità di codifica e compatibilità.
