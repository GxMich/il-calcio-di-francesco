# Il Calcio di Francesco

Il primo sito di Francesco: risultati della Serie A, le ultime 100 partite, la classifica e le esultanze più famose dei calciatori.

**Guardalo qui:** https://gxmich.github.io/il-calcio-di-francesco/

Sull'iPhone: aprilo con Safari, tocca il pulsante Condividi e poi «Aggiungi alla schermata Home». Comparirà come un'app.

## Come funziona

- `aggiorna_sito.py` scarica i risultati dall'API gratuita [TheSportsDB](https://www.thesportsdb.com), calcola la classifica, scarica stemmi e foto e costruisce `index.html`.
- `modello.html` è la grafica della pagina: colori, testi, sezioni.
- `img/` contiene stemmi e foto dei calciatori (da Wikimedia Commons, con licenza libera: l'autore è scritto sotto ogni foto).
- `cache/` conserva i dati già scaricati, così non si riscaricano ogni volta.

## Aggiornamento

Ogni lunedì mattina GitHub aggiorna da solo i risultati (file `.github/workflows/aggiorna.yml`).
Per aggiornare subito: scheda **Actions** → **Aggiorna i risultati** → **Run workflow**.

Oppure dal computer:

```
pip install pillow
python aggiorna_sito.py
```
