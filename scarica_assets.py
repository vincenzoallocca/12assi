#!/usr/bin/env python3
"""
Scarica in locale foto e font del sito "12 assi" dentro la cartella assets/.

Uso:   python3 scarica_assets.py
    python3 scarica_assets.py --optimize-only
    python3 scarica_assets.py --repair-portraits-only
Poi:   apri index.html (doppio click). Funziona anche offline.

Il download usa la libreria standard; l'ottimizzazione WebP usa Pillow se disponibile.
Gli originali restano come fallback. Puoi rilanciarlo: salta i file già scaricati.
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

PHOTO_FIXES = {
 "Antonio Gramsci": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Gramsci.png",
 "Alexander Hamilton": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/05/Alexander_Hamilton_portrait_by_John_Trumbull_1806.jpg/960px-Alexander_Hamilton_portrait_by_John_Trumbull_1806.jpg",
 "Aung San Suu Kyi": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Aung_San_Suu_Kyi_par_Claude_Truong-Ngoc_octobre_2013.jpg/960px-Aung_San_Suu_Kyi_par_Claude_Truong-Ngoc_octobre_2013.jpg",
 "Baruch Spinoza": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/53/Baruch_Spinoza_portrait_HAB_original.jpg/960px-Baruch_Spinoza_portrait_HAB_original.jpg",
 "Carlo Rosselli": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Carlo_Rosselli_3.jpg",
 "Dario Franceschini": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2f/Dario_Franceschini_Official_%28cropped%29.jpg/960px-Dario_Franceschini_Official_%28cropped%29.jpg",
 "Franklin D. Roosevelt": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/42/FDR_1944_Color_Portrait.jpg/960px-FDR_1944_Color_Portrait.jpg",
 "Geert Wilders": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b7/Geert_Wilders%2C_painted_portrait_%2833694410786%29.jpg/960px-Geert_Wilders%2C_painted_portrait_%2833694410786%29.jpg",
 "George Washington": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Gilbert_Stuart_-_George_Washington_%28Lansdowne_Portrait%29_-_Google_Art_Project.jpg/960px-Gilbert_Stuart_-_George_Washington_%28Lansdowne_Portrait%29_-_Google_Art_Project.jpg",
 "Giacomo Matteotti": "https://upload.wikimedia.org/wikipedia/commons/4/4a/Giacomo_Matteotti_2_%28cropped%29.jpg",
 "Giulio Cesare": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/62/Retrato_de_Julio_C%C3%A9sar_%2826724093101%29_%28cropped%29.jpg/960px-Retrato_de_Julio_C%C3%A9sar_%2826724093101%29_%28cropped%29.jpg",
 "Giuseppe Garibaldi": "https://upload.wikimedia.org/wikipedia/commons/b/b7/Giuseppe_Garibaldi_portrait.jpg",
 "Hugo Chávez": "https://upload.wikimedia.org/wikipedia/commons/5/59/Hugo_Chavez_Portrait_%28cropped%29.jpg",
 "Immanuel Kant": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a2/Immanuel_Kant_portrait_c1790.jpg/960px-Immanuel_Kant_portrait_c1790.jpg",
 "Isaiah Berlin": "https://upload.wikimedia.org/wikipedia/commons/a/a8/IsaiahBerlin1983.jpg",
 "Jürgen Habermas": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/75/JuergenHabermas_crop1.jpg/960px-JuergenHabermas_crop1.jpg",
 "Laura Boldrini": "https://upload.wikimedia.org/wikipedia/commons/6/69/Laura_Boldrini_2016.jpg",
 "Lev Trockij": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cf/Leon_Trotsky_1918_%283x4_rotated_cropped_b%29.jpg/960px-Leon_Trotsky_1918_%283x4_rotated_cropped_b%29.jpg",
 "Montesquieu": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Charles_Montesquieu.jpg",
 "Patrice Lumumba": "https://upload.wikimedia.org/wikipedia/commons/d/d5/Patrice_Lumumba_official_portrait.jpg",
 "Piero Gobetti": "https://upload.wikimedia.org/wikipedia/commons/5/56/Piero_gobetti.JPG",
 "Salvador Allende": "https://upload.wikimedia.org/wikipedia/commons/0/0d/Salvador_Allende_Gossens-.jpg",
 "Sant'Agostino": "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ea/Saint_Augustine_by_Philippe_de_Champaigne.jpg/960px-Saint_Augustine_by_Philippe_de_Champaigne.jpg",
 "Thomas Jefferson": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/07/Official_Presidential_portrait_of_Thomas_Jefferson_%28by_Rembrandt_Peale%2C_1800%29.jpg/960px-Official_Presidential_portrait_of_Thomas_Jefferson_%28by_Rembrandt_Peale%2C_1800%29.jpg",
 "Tommaso d'Aquino": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0a/St-thomas-aquinasFXD.jpg/960px-St-thomas-aquinasFXD.jpg",
 "Walter Benjamin": "https://upload.wikimedia.org/wikipedia/commons/c/cc/Walter_Benjamin_vers_1928.jpg",
 "Nelson Mandela": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/02/Nelson_Mandela_1994.jpg/330px-Nelson_Mandela_1994.jpg",
 "Mahatma Gandhi": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7a/Mahatma-Gandhi%2C_studio%2C_1931.jpg/330px-Mahatma-Gandhi%2C_studio%2C_1931.jpg",
 "Barack Obama": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8d/President_Barack_Obama.jpg/330px-President_Barack_Obama.jpg",
 "Angela Merkel": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0f/Angela_Merkel_2019_cropped.jpg/330px-Angela_Merkel_2019_cropped.jpg",
 "Emmanuel Macron": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3c/Emmanuel_Macron_2025_%28cropped%29.jpg/330px-Emmanuel_Macron_2025_%28cropped%29.jpg",
 "Charles de Gaulle": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9d/De_Gaulle-OWI_%28cropped%29_%28c%29%282%29.jpg/330px-De_Gaulle-OWI_%28cropped%29_%28c%29%282%29.jpg",
 "Winston Churchill": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/02/Sir_Winston_Churchill_-_19086236948_%28restored%29.jpg/330px-Sir_Winston_Churchill_-_19086236948_%28restored%29.jpg",
 "Ronald Reagan": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/16/Official_Portrait_of_President_Reagan_1981.jpg/330px-Official_Portrait_of_President_Reagan_1981.jpg",
 "Margaret Thatcher": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/3d/Margaret_Thatcher_stock_portrait_%28cropped%29.jpg/330px-Margaret_Thatcher_stock_portrait_%28cropped%29.jpg",
 "Giorgia Meloni": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/96/Giorgia_Meloni_Official_2024_%28cropped%29.jpg/330px-Giorgia_Meloni_Official_2024_%28cropped%29.jpg",
 "Donald Trump": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/16/Official_Presidential_Portrait_of_President_Donald_J._Trump_%282025%29.jpg/330px-Official_Presidential_Portrait_of_President_Donald_J._Trump_%282025%29.jpg",
 "Javier Milei": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/76/Javier_Milei_in_pull-aside_meeting_at_the_United_Nations_Headquarters_%283x4_cropped%29.jpg/330px-Javier_Milei_in_pull-aside_meeting_at_the_United_Nations_Headquarters_%283x4_cropped%29.jpg",
 "Vladimir Putin": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/86/Vladimir_Putin_%282026_02_23%29.jpg/330px-Vladimir_Putin_%282026_02_23%29.jpg",
 "Xi Jinping": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dc/Prime_Minister_Keir_Starmer_visits_China_%2855066713683%29_%28cropped%2Bangle%29.jpg/330px-Prime_Minister_Keir_Starmer_visits_China_%2855066713683%29_%28cropped%2Bangle%29.jpg",
 "Napoleone": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/50/Jacques-Louis_David_-_The_Emperor_Napoleon_in_His_Study_at_the_Tuileries_-_Google_Art_Project.jpg/330px-Jacques-Louis_David_-_The_Emperor_Napoleon_in_His_Study_at_the_Tuileries_-_Google_Art_Project.jpg",
 "Elly Schlein": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2a/Elly_Schlein_in_2023_%28cropped%29.jpg/330px-Elly_Schlein_in_2023_%28cropped%29.jpg",
 "Giuseppe Conte": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/01/Giuseppe_Conte_Official.jpg/330px-Giuseppe_Conte_Official.jpg",
 "Matteo Salvini": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/04/Matteo_Salvini_2025_%28cropped%29.jpg/330px-Matteo_Salvini_2025_%28cropped%29.jpg",
 "Marine Le Pen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f0/Marine_Le_Pen_2025_%283x4_cropped%29.jpg/330px-Marine_Le_Pen_2025_%283x4_cropped%29.jpg",
 "Olaf Scholz": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/27/Olaf_Scholz_September_2024.jpg/330px-Olaf_Scholz_September_2024.jpg",
 "Palmiro Togliatti": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/34/Palmiro-Togliatti-00504708.jpg/330px-Palmiro-Togliatti-00504708.jpg",
 "Nicola Fratoianni": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/67/Nicola_Fratoianni_Quirinale_2022_%28cropped%29.jpg/330px-Nicola_Fratoianni_Quirinale_2022_%28cropped%29.jpg",
 "Marco Cappato": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/77/Marco_Cappato%2C_10.22_%28cropped%29.jpg/330px-Marco_Cappato%2C_10.22_%28cropped%29.jpg",
 "Stefano Bonaccini": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/31/1719930276898_20240702_BONACCINI_Stefano_IT_003.jpg/330px-1719930276898_20240702_BONACCINI_Stefano_IT_003.jpg",
 "Massimiliano Fedriga": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a1/Massimiliano_Fedriga_in_2024.jpg/330px-Massimiliano_Fedriga_in_2024.jpg",
 "Giovanni Giolitti": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/07/Portrait_of_Giovanni_Giolitti%2C_1920.jpg/330px-Portrait_of_Giovanni_Giolitti%2C_1920.jpg",
 "Mao Zedong": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5e/Mao_Zedong_1950_Portrait_%283x4_cropped%29%282%29.jpg/330px-Mao_Zedong_1950_Portrait_%283x4_cropped%29%282%29.jpg",
 "Paola Taverna": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f4/Ms._Paola_Taverna%2C_OSCE_PA_Autumn_Meeting%2C_Marrakech%2C_5_Oct._2019.jpg/330px-Ms._Paola_Taverna%2C_OSCE_PA_Autumn_Meeting%2C_Marrakech%2C_5_Oct._2019.jpg",
 "Giorgio Agamben": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/da/Agamben.png/330px-Agamben.png",
 "Judith Butler": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bf/JudithButler2013.jpg/330px-JudithButler2013.jpg",
 "Adolf Hitler": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0c/Hitler_portrait_crop_%28cropped%29%282%29.jpg/330px-Hitler_portrait_crop_%28cropped%29%282%29.jpg",
 "Josef Stalin": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/08/StalinCropped1943.jpg/330px-StalinCropped1943.jpg",
 "Konrad Adenauer": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/86/Bundesarchiv_B_145_Bild-F078072-0004%2C_Konrad_Adenauer.jpg/330px-Bundesarchiv_B_145_Bild-F078072-0004%2C_Konrad_Adenauer.jpg",
 "Benedetto Croce": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4c/Benedetto_Croce_01.jpg/330px-Benedetto_Croce_01.jpg",
 "Socrate": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Socrates_Louvre.jpg/330px-Socrates_Louvre.jpg",
 "David Hume": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/03/David_Hume_Ramsay.jpg/330px-David_Hume_Ramsay.jpg",
 "Karl Popper": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/43/Karl_Popper.jpg/330px-Karl_Popper.jpg",
 "Robert Nozick": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cb/Robert_Nozick_1977_Libertarian_Review_cover_%284x5_cropped%29.jpg/330px-Robert_Nozick_1977_Libertarian_Review_cover_%284x5_cropped%29.jpg",
 "Platone": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/21/Plato_Silanion_Musei_Capitolini_MC1377.png/330px-Plato_Silanion_Musei_Capitolini_MC1377.png",
 "Aristotele": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ae/Aristotle_Altemps_Inv8575.jpg/330px-Aristotle_Altemps_Inv8575.jpg",
 "Epicuro": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/88/Epikouros_BM_1843.jpg/330px-Epikouros_BM_1843.jpg",
 "Thomas Hobbes": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/09/Thomas_Hobbes_by_John_Michael_Wright_%28colour%29_%283x4_cropped%29.jpg/330px-Thomas_Hobbes_by_John_Michael_Wright_%28colour%29_%283x4_cropped%29.jpg",
 "John Locke": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/db/Godfrey_Kneller_-_Portrait_of_John_Locke_%28Hermitage%29.jpg/330px-Godfrey_Kneller_-_Portrait_of_John_Locke_%28Hermitage%29.jpg",
 "Adam Smith": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/43/Adam_Smith_The_Muir_portrait.jpg/330px-Adam_Smith_The_Muir_portrait.jpg",
 "Karl Marx": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b3/Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored.png/330px-Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored.png",
 "Michail Bakunin": "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e8/Mikhail_Bakunin_Nader_%283x4_cropped%29.jpg/330px-Mikhail_Bakunin_Nader_%283x4_cropped%29.jpg",
 "Friedrich Nietzsche": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1b/Nietzsche187a.jpg/330px-Nietzsche187a.jpg",
 "Albert Camus": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/08/Albert_Camus%2C_gagnant_de_prix_Nobel%2C_portrait_en_buste%2C_pos%C3%A9_au_bureau%2C_faisant_face_%C3%A0_gauche%2C_cigarette_de_tabagisme.jpg/330px-Albert_Camus%2C_gagnant_de_prix_Nobel%2C_portrait_en_buste%2C_pos%C3%A9_au_bureau%2C_faisant_face_%C3%A0_gauche%2C_cigarette_de_tabagisme.jpg",
 "Papa Francesco": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8b/Pope_Francis_Korea_Haemi_Castle_19_%284x5_cropped%29.jpg/330px-Pope_Francis_Korea_Haemi_Castle_19_%284x5_cropped%29.jpg"
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
    if name in PHOTO_FIXES:
        return PHOTO_FIXES[name]
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
    files = sorted(PHOTOS.glob(s + ".*"), key=lambda f: f.suffix.lower() == ".webp")
    for f in files:
        if f.stat().st_size > 0:
            return f
    return None


def optimize_photo_mapping(mapping):
    try:
        from PIL import Image
    except ImportError:
        print("WebP non generato: Pillow non disponibile; restano gli originali.")
        return {}
    optimized = {}
    for name, rel in mapping.items():
        source = ROOT / rel
        if source.suffix.lower() == ".webp" or not source.is_file():
            continue
        target = source.with_suffix(".webp")
        try:
            if not target.is_file():
                with Image.open(source) as image:
                    image.thumbnail((600, 600), Image.Resampling.LANCZOS)
                    mode = "RGBA" if "A" in image.getbands() else "RGB"
                    image.convert(mode).save(target, "WEBP", quality=84, method=6)
            optimized[name] = "assets/photos/" + target.name
        except Exception as error:
            print(f"WebP non generato per {name}: {error}")
    return optimized


def fixed_photo_path(name):
    url = PHOTO_FIXES[name]
    return PHOTOS / (slug(name) + "_portrait" + ext_for(url, ""))


def download_fixed_photos(mapping):
    for name, url in PHOTO_FIXES.items():
        target = fixed_photo_path(name)
        try:
            if not target.is_file() or target.stat().st_size == 0:
                data, ctype = http_get(url)
                if not ctype.startswith("image/"):
                    raise RuntimeError("risposta non valida")
                target.write_bytes(data)
            mapping[name] = "assets/photos/" + target.name
            print(f"{name}: ritratto aggiornato")
        except Exception as error:
            print(f"{name}: sostituzione non disponibile ({error})")
    return mapping


def write_photo_manifest(mapping, optimized):
    js = "// Generato da scarica_assets.py\n"
    js += "window.LOCAL_PHOTOS = " + json.dumps(mapping, ensure_ascii=False, indent=1) + ";\n"
    js += "window.LOCAL_PHOTOS_WEBP = " + json.dumps(optimized, ensure_ascii=False, indent=1) + ";\n"
    (ROOT / "assets" / "photos.js").write_text(js, encoding="utf-8")


def download_photos():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    mapping, failed = {}, []
    for i, name in enumerate(NAMES, 1):
        s = slug(name)
        f = fixed_photo_path(name) if name in PHOTO_FIXES else existing(s)
        if not f or not f.is_file() or f.stat().st_size == 0:
            try:
                url = resolve_url(name)
                if not url:
                    raise RuntimeError("nessuna foto trovata")
                data, ctype = http_get(url)
                if not ctype.startswith("image/"):
                    raise RuntimeError("risposta non valida")
                basename = s + "_portrait" if name in PHOTO_FIXES else s
                f = PHOTOS / (basename + ext_for(url, ctype))
                f.write_bytes(data)
                time.sleep(0.25)  # gentilezza verso Wikimedia
            except Exception as e:
                failed.append((name, str(e)))
                print(f"[{i}/{len(NAMES)}] {name}: ERRORE ({e})")
                continue
        mapping[name] = "assets/photos/" + f.name
        print(f"[{i}/{len(NAMES)}] {name}: ok")
    optimized = optimize_photo_mapping(mapping)
    write_photo_manifest(mapping, optimized)
    # versione base64 (serve per esportare il PNG anche aprendo index.html con doppio click)
    import base64, mimetypes
    b64 = {}
    for n, rel in mapping.items():
        fp = ROOT / rel
        mt = mimetypes.guess_type(fp.name)[0] or "image/jpeg"
        b64[n] = "data:" + mt + ";base64," + base64.b64encode(fp.read_bytes()).decode()
    (ROOT / "assets" / "photos64.js").write_text("window.LOCAL_PHOTOS64 = " + json.dumps(b64, ensure_ascii=False) + ";\n", encoding="utf-8")
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
    if "--repair-portraits-only" in sys.argv:
        photos_js = (ROOT / "assets" / "photos.js").read_text(encoding="utf-8")
        match = re.search(r"window\.LOCAL_PHOTOS\s*=\s*(\{.*?\});", photos_js, re.S)
        if not match:
            raise RuntimeError("Manifest delle foto locale non valido.")
        mapping = download_fixed_photos(json.loads(match.group(1)))
        optimized = optimize_photo_mapping(mapping)
        write_photo_manifest(mapping, optimized)
        print(f"Ritratti corretti: {len(PHOTO_FIXES)}")
        return
    if "--optimize-only" in sys.argv:
        photos_js = (ROOT / "assets" / "photos.js").read_text(encoding="utf-8")
        match = re.search(r"window\.LOCAL_PHOTOS\s*=\s*(\{.*?\});", photos_js, re.S)
        if not match:
            raise RuntimeError("Manifest delle foto locale non valido.")
        mapping = json.loads(match.group(1))
        optimized = optimize_photo_mapping(mapping)
        write_photo_manifest(mapping, optimized)
        print(f"WebP ottimizzate: {len(optimized)}/{len(mapping)}")
        return
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
