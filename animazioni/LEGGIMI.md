# Animazioni delle esultanze

I file originali dei 14 video della sezione «Esultanze famose», creati con [HyperFrames](https://hyperframes.heygen.com) (animazioni HTML trasformate in video).

- `index.html` contiene il calciatore cartone, lo stadio e le 14 mosse. La mossa da disegnare si sceglie con la variabile `mossa`.
- `esultanze.json` è l'elenco delle 14 mosse da trasformare in video.

## Rifare i video

Servono Node.js e FFmpeg. Da questa cartella:

```
npx hyperframes render --batch esultanze.json --quality looks --output "renders/{name}.mp4"
```

Poi i video vanno rimpiccioliti a 720×720 e copiati nella cartella `../video/`, ognuno con la sua immagine di copertina (`.jpg`).
