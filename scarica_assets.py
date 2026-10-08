#!/usr/bin/env python3
"""
Scarica in locale foto e font del sito "12 assi" dentro la cartella assets/.

Uso:   python3 scarica_assets.py
Poi:   apri index.html (doppio click). Funziona anche offline.

Solo libreria standard, nessun pip install. Puoi rilanciarlo: salta i file già scaricati.
"""
import json, re, sys, time, shutil, unicodedata, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / "assets" / "photos"
FONTS = ROOT / "assets" / "fonts"
UA = "12assi-offline/1.0 (uso personale; script di download)"
FONT_URL = "https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap"

NAMES = [
 "Karl Liebknecht",
 "Rosa Luxemburg",
 "Salvador Allende",
 "Gustavo Petro",
 "Bernie Sanders",
 "Alexandria Ocasio-Cortez",
 "Jeremy Corbyn",
 "Olof Palme",
 "Enrico Berlinguer",
 "Lula da Silva",
 "Thomas Sankara",
 "Nelson Mandela",
 "Martin Luther King",
 "Mahatma Gandhi",
 "Jacinda Ardern",
 "Barack Obama",
 "Franklin D. Roosevelt",
 "Abraham Lincoln",
 "Thomas Jefferson",
 "Giuseppe Mazzini",
 "Giuseppe Garibaldi",
 "Camillo Cavour",
 "Alcide De Gasperi",
 "Mario Draghi",
 "Angela Merkel",
 "Emmanuel Macron",
 "Charles de Gaulle",
 "Winston Churchill",
 "Ronald Reagan",
 "Margaret Thatcher",
 "Silvio Berlusconi",
 "Giorgia Meloni",
 "Donald Trump",
 "Javier Milei",
 "Narendra Modi",
 "Lee Kuan Yew",
 "Vladimir Putin",
 "Xi Jinping",
 "Hugo Chávez",
 "Che Guevara",
 "Fidel Castro",
 "Lenin",
 "Robespierre",
 "Napoleone",
 "Giulio Cesare",
 "Benito Mussolini",
 "Augusto Pinochet",
 "Elly Schlein",
 "Giuseppe Conte",
 "Matteo Salvini",
 "Matteo Renzi",
 "Antonio Tajani",
 "Romano Prodi",
 "Nichi Vendola",
 "Sergio Mattarella",
 "Jean-Luc Mélenchon",
 "Marine Le Pen",
 "Keir Starmer",
 "Olaf Scholz",
 "Pedro Sánchez",
 "Viktor Orbán",
 "Volodymyr Zelensky",
 "Claudia Sheinbaum",
 "Gabriel Boric",
 "Joe Biden",
 "Kamala Harris",
 "Sandro Pertini",
 "Giacomo Matteotti",
 "Palmiro Togliatti",
 "Aldo Moro",
 "Carlo Calenda",
 "Nicola Fratoianni",
 "Roberto Vannacci",
 "Angelo Bonelli",
 "Riccardo Magi",
 "Emma Bonino",
 "Marco Cappato",
 "Enrico Letta",
 "Massimo D'Alema",
 "Pier Luigi Bersani",
 "Paolo Gentiloni",
 "Stefano Bonaccini",
 "Giuseppe Sala",
 "Maurizio Landini",
 "Beppe Grillo",
 "Luigi Di Maio",
 "Pier Ferdinando Casini",
 "Guido Crosetto",
 "Carlo Nordio",
 "Giancarlo Giorgetti",
 "Roberto Calderoli",
 "Luca Zaia",
 "Massimiliano Fedriga",
 "Francesco Lollobrigida",
 "Ignazio La Russa",
 "Daniela Santanchè",
 "Maurizio Lupi",
 "Giovanni Donzelli",
 "Alessandro Di Battista",
 "Michele Emiliano",
 "Vincenzo De Luca",
 "Matteo Piantedosi",
 "Tommaso Foti",
 "Recep Tayyip Erdoğan",
 "Benjamin Netanyahu",
 "Rishi Sunak",
 "Justin Trudeau",
 "Anthony Albanese",
 "Nayib Bukele",
 "Cyril Ramaphosa",
 "Bettino Craxi",
 "Giulio Andreotti",
 "Enrico Mattei",
 "Giovanni Giolitti",
 "Luigi Sturzo",
 "John F. Kennedy",
 "Mao Zedong",
 "Tito",
 "Mario Monti",
 "Giulio Tremonti",
 "Gianfranco Fini",
 "Antonio Di Pietro",
 "Laura Boldrini",
 "Chiara Appendino",
 "Paola Taverna",
 "Gianni Cuperlo",
 "Andrea Orlando",
 "Dario Franceschini",
 "Francesco Boccia",
 "Peppe Provenzano",
 "Silvia Salis",
 "Roberto Gualtieri",
 "Matteo Lepore",
 "Massimo Cacciari",
 "Giorgio Agamben",
 "Ursula von der Leyen",
 "Friedrich Merz",
 "Mark Rutte",
 "Geert Wilders",
 "Nigel Farage",
 "Santiago Abascal",
 "Alice Weidel",
 "Jair Bolsonaro",
 "Evo Morales",
 "Nicolás Maduro",
 "Yoon Suk Yeol",
 "Aung San Suu Kyi",
 "Imran Khan",
 "Mohammed bin Salman",
 "Ali Khamenei",
 "Kim Jong-un",
 "Elon Musk",
 "Pedro Castillo",
 "Andrés Manuel López Obrador",
 "Zohran Mamdani",
 "Judith Butler",
 "Jürgen Habermas",
 "Michael Sandel",
 "Byung-Chul Han",
 "Thomas Piketty",
 "Yanis Varoufakis",
 "Shinzo Abe",
 "Alexander Hamilton",
 "George Washington",
 "Simón Bolívar",
 "Adolf Hitler",
 "Josef Stalin",
 "Francisco Franco",
 "António Salazar",
 "Juan Perón",
 "Evita Perón",
 "Jawaharlal Nehru",
 "Mustafa Kemal Atatürk",
 "Michail Gorbaciov",
 "Willy Brandt",
 "Konrad Adenauer",
 "Julius Nyerere",
 "Patrice Lumumba",
 "Kwame Nkrumah",
 "Lev Trockij",
 "Eduard Bernstein",
 "Piero Gobetti",
 "Carlo Rosselli",
 "Altiero Spinelli",
 "Benedetto Croce",
 "Giovanni Gentile",
 "Norberto Bobbio",
 "Umberto Eco",
 "Emma Goldman",
 "Pëtr Kropotkin",
 "Pierre-Joseph Proudhon",
 "Socrate",
 "Sant'Agostino",
 "Tommaso d'Aquino",
 "Baruch Spinoza",
 "David Hume",
 "G.W.F. Hegel",
 "Arthur Schopenhauer",
 "Søren Kierkegaard",
 "Alexis de Tocqueville",
 "Max Weber",
 "Carl Schmitt",
 "Isaiah Berlin",
 "Karl Popper",
 "Walter Benjamin",
 "Herbert Marcuse",
 "Robert Nozick",
 "Platone",
 "Aristotele",
 "Epicuro",
 "Marco Aurelio",
 "Confucio",
 "Machiavelli",
 "Thomas Hobbes",
 "John Locke",
 "Montesquieu",
 "Jean-Jacques Rousseau",
 "Voltaire",
 "Immanuel Kant",
 "Adam Smith",
 "Edmund Burke",
 "John Stuart Mill",
 "Henry David Thoreau",
 "Karl Marx",
 "Michail Bakunin",
 "Friedrich Nietzsche",
 "Antonio Gramsci",
 "Hannah Arendt",
 "Albert Camus",
 "Simone de Beauvoir",
 "John M. Keynes",
 "Friedrich Hayek",
 "Murray Rothbard",
 "Ayn Rand",
 "John Rawls",
 "Michel Foucault",
 "Roger Scruton",
 "Noam Chomsky",
 "Peter Singer",
 "Slavoj Žižek",
 "Papa Francesco"
]
PRESET = {
 "Barack Obama": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Barack_Obama.jpg/600px-Barack_Obama.jpg",
 "Donald Trump": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/600px-Donald_Trump_official_portrait.jpg",
 "Angela Merkel": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Angela_Merkel_2019.jpg/600px-Angela_Merkel_2019.jpg",
 "Emmanuel Macron": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Emmanuel_Macron_2022.jpg/600px-Emmanuel_Macron_2022.jpg",
 "Giorgia Meloni": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Giorgia_Meloni_2023.jpg/600px-Giorgia_Meloni_2023.jpg",
 "Matteo Salvini": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Matteo_Salvini_2019.jpg/600px-Matteo_Salvini_2019.jpg",
 "Elly Schlein": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Elly_Schlein_2022.jpg/600px-Elly_Schlein_2022.jpg",
 "Marine Le Pen": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Marine_Le_Pen_2022.jpg/600px-Marine_Le_Pen_2022.jpg",
 "Javier Milei": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Javier_Milei_2023.jpg/600px-Javier_Milei_2023.jpg",
 "Vladimir Putin": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Vladimir_Putin_2024.jpg/600px-Vladimir_Putin_2024.jpg",
 "Xi Jinping": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Xi_Jinping_2019.jpg/600px-Xi_Jinping_2019.jpg",
 "Mahatma Gandhi": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mahatma-Gandhi%2C_studio%2C_1931.jpg/600px-Mahatma-Gandhi%2C_studio%2C_1931.jpg",
 "Karl Marx": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Karl_Marx_001.jpg/600px-Karl_Marx_001.jpg",
 "Friedrich Nietzsche": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Nietzsche1882.jpg/600px-Nietzsche1882.jpg",
 "Socrate": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Socrates_Louvre.jpg/600px-Socrates_Louvre.jpg",
 "Aristotele": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Aristotle_Altemps_Inv8575.jpg/600px-Aristotle_Altemps_Inv8575.jpg",
 "Karl Popper": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Karl_Popper.jpg/600px-Karl_Popper.jpg",
 "John Locke": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/John_Locke_by_Herman_Verelst.png/600px-John_Locke_by_Herman_Verelst.png",
 "Thomas Hobbes": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Thomas_Hobbes_%28portrait%29.jpg/600px-Thomas_Hobbes_%28portrait%29.jpg",
 "Nicola Fratoianni": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Nicola_Fratoianni_2018.jpg/600px-Nicola_Fratoianni_2018.jpg",
 "Giuseppe Conte": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Giuseppe_Conte_2019.jpg/600px-Giuseppe_Conte_2019.jpg",
 "Marco Cappato": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Marco_Cappato_2019.jpg/600px-Marco_Cappato_2019.jpg",
 "Papa Francesco": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Pope_Francis_2021.jpg/600px-Pope_Francis_2021.jpg",
 "Nelson Mandela": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Nelson_Mandela_1994.jpg/600px-Nelson_Mandela_1994.jpg",
 "Mao Zedong": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Mao_Zedong_in_1940s.jpg/600px-Mao_Zedong_in_1940s.jpg",
 "Adolf Hitler": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Hitler_portrait_crop.jpg/600px-Hitler_portrait_crop.jpg",
 "Josef Stalin": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Joseph_Stalin_1945.jpg/600px-Joseph_Stalin_1945.jpg",
 "Winston Churchill": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Winston_Churchill_1944.jpg/600px-Winston_Churchill_1944.jpg",
 "Charles de Gaulle": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Charles_de_Gaulle_1961.jpg/600px-Charles_de_Gaulle_1961.jpg",
 "Margaret Thatcher": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Margaret_Thatcher_1986.jpg/600px-Margaret_Thatcher_1986.jpg",
 "Ronald Reagan": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Ronald_Reagan_1985.jpg/600px-Ronald_Reagan_1985.jpg"
}


def http_get(url, ua=UA, retries=4):
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and k < retries - 1:
                time.sleep(2 * (k + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if k < retries - 1:
                time.sleep(1.5 * (k + 1))
                continue
            raise


def strip_accents(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("ß", "ss")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", strip_accents(name).lower()).strip("_")


def candidates(name):
    raw = name.strip()
    out = []
    def add(v):
        if v and len(v) > 1 and v not in out:
            out.append(v)
    add(raw); add(strip_accents(raw)); add(re.sub(r"[.,'\"]", "", raw))
    t = strip_accents(raw).split()
    if len(t) > 1:
        add(t[0] + " " + t[-1]); add(t[-1]); add(t[0])
    return out


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data, _ = http_get(url)
    return json.loads(data)


def resolve_url(name):
    """URL dell'immagine: prima quelle fisse, poi ricerca su Wikimedia Commons."""
    if name in PRESET:
        return PRESET[name]
    for cand in candidates(name):
        try:
            d = api({"action": "query", "format": "json", "generator": "search",
                     "gsrsearch": cand, "gsrnamespace": 6, "gsrlimit": 5,
                     "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 600})
        except Exception:
            continue
        pages = (d.get("query") or {}).get("pages") or {}
        c = strip_accents(cand).lower()
        for pg in pages.values():
            title = strip_accents(pg.get("title", "")).lower()
            if not re.search(r"\.(jpe?g|png|webp)$", title):
                continue
            if c in title or title.replace("file:", "") in c:
                info = (pg.get("imageinfo") or [{}])[0]
                u = info.get("thumburl") or info.get("url")
                if u:
                    return u
        time.sleep(0.2)
    return None


def ext_for(url, ctype):
    m = re.search(r"\.(jpe?g|png|webp|gif)(?:$|\?)", url, re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    if "png" in ctype: return ".png"
    if "webp" in ctype: return ".webp"
    return ".jpg"


def existing(s):
    for f in PHOTOS.glob(s + ".*"):
        if f.stat().st_size > 0:
            return f
    return None


def download_photos():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    mapping, failed = {}, []
    for i, name in enumerate(NAMES, 1):
        s = slug(name)
        f = existing(s)
        if not f:
            try:
                url = resolve_url(name)
                if not url:
                    raise RuntimeError("nessuna foto trovata")
                data, ctype = http_get(url)
                if not ctype.startswith("image/"):
                    raise RuntimeError("risposta non valida")
                f = PHOTOS / (s + ext_for(url, ctype))
                f.write_bytes(data)
                time.sleep(0.25)  # gentilezza verso Wikimedia
            except Exception as e:
                failed.append((name, str(e)))
                print(f"[{i}/{len(NAMES)}] {name}: ERRORE ({e})")
                continue
        mapping[name] = "assets/photos/" + f.name
        print(f"[{i}/{len(NAMES)}] {name}: ok")
    js = "// Generato da scarica_assets.py\nwindow.LOCAL_PHOTOS = " + json.dumps(mapping, ensure_ascii=False, indent=1) + ";\n"
    (ROOT / "assets" / "photos.js").write_text(js, encoding="utf-8")
    return mapping, failed


def download_font():
    FONTS.mkdir(parents=True, exist_ok=True)
    try:
        # User-Agent da browser moderno, così Google serve i woff2
        chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        css = http_get(FONT_URL, ua=chrome)[0].decode("utf-8")
        for k, u in enumerate(dict.fromkeys(re.findall(r"url\((https:[^)]+)\)", css))):
            fname = f"outfit_{k}.woff2"
            (FONTS / fname).write_bytes(http_get(u, ua=chrome)[0])
            css = css.replace(u, fname)
        (FONTS / "fonts.css").write_text(css, encoding="utf-8")
        # font ora locale: tolgo il collegamento a Google dall'HTML
        idx = ROOT / "index.html"
        html = idx.read_text(encoding="utf-8")
        html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', "", html)
        idx.write_text(html, encoding="utf-8")
        print("Font Outfit: ok")
        return True
    except Exception as e:
        print(f"Font: ERRORE ({e}) - userò il font di sistema")
        return False


def main():
    print("== Foto ==")
    mapping, failed = download_photos()
    print("\n== Font ==")
    download_font()
    print(f"\nFatto: {len(mapping)}/{len(NAMES)} foto in assets/photos/")
    if failed:
        print("Non scaricate (rilancia lo script per riprovare; nel sito resteranno le iniziali):")
        for n, e in failed:
            print(" -", n, "->", e)
    print("Apri index.html per usare il sito.")


if __name__ == "__main__":
    main()
