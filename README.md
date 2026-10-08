# 12 assi — Test politico

Test politico a 12 assi: 36 affermazioni, ideologia, politici, filosofi e Paesi più vicini a te.
Sito statico (un solo `index.html`), pubblicato con GitHub Pages.

## Come funziona la pubblicazione

A ogni push su `main`, GitHub Actions esegue `scarica_assets.py` (scarica foto e font in `assets/`)
e pubblica il sito. Non serve committare le foto.

## Provarlo in locale

```bash
python3 scarica_assets.py   # scarica foto e font in assets/
# poi apri index.html
```

## Crediti

Le foto provengono da Wikimedia Commons e sono soggette alle rispettive licenze.
I profili di personalità e Paesi sono stime orientative a scopo di gioco.
