# Generuje podstrony tras (SEO) dla krakow-transfers.com w 6 językach.
# Uruchom z katalogu repo: python3 auto-blog/build-routes.py
# Ceny i style bierze z index.html, więc po zmianie cennika wystarczy uruchomić ponownie.
import json, os, re, html, glob, urllib.parse, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import routes_extra as X  # trasy bez cennika (cena na zapytanie)
import route_guides as G  # sekcje poradnikowe pod główne frazy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://krakow-transfers.com"
PHONE = "48728814659"
BRAND = "Kraków Transfers"
ORG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "org.json"), encoding="utf-8"))
LANGS = ["pl", "en", "de", "fr", "it", "es"]
ROUTES = ["kr", "zak", "kz"] + X.NEW_ROUTES
SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", SRC, re.S).group(1)

def prices(head_key):
    i = SRC.find(f'data-i18n="{head_key}"')
    tb = SRC[i:SRC.find("</tbody>", i)]
    vals = [int(x) for x in re.findall(r">(\d+) zł<", tb)]
    return {"d3": vals[0], "n3": vals[1], "d8": vals[2], "n8": vals[3], "d20": vals[4], "n20": vals[5]}

P = {"kr": prices("pricing_city_kr"), "zak": prices("pricing_city_zak"), "kz": prices("pricing_city_kz")}

SLUG = {
    "pl": {"kr": "transfer-pyrzowice-krakow", "zak": "transfer-pyrzowice-zakopane", "kz": "transfer-krakow-zakopane"},
    "en": {"kr": "katowice-airport-to-krakow-transfer", "zak": "katowice-airport-to-zakopane-transfer", "kz": "krakow-to-zakopane-transfer"},
    "de": {"kr": "transfer-flughafen-kattowitz-krakau", "zak": "transfer-flughafen-kattowitz-zakopane", "kz": "transfer-krakau-zakopane"},
    "fr": {"kr": "transfert-aeroport-katowice-cracovie", "zak": "transfert-aeroport-katowice-zakopane", "kz": "transfert-cracovie-zakopane"},
    "it": {"kr": "transfer-aeroporto-katowice-cracovia", "zak": "transfer-aeroporto-katowice-zakopane", "kz": "transfer-cracovia-zakopane"},
    "es": {"kr": "traslado-aeropuerto-katowice-cracovia", "zak": "traslado-aeropuerto-katowice-zakopane", "kz": "traslado-cracovia-zakopane"},
}

for _l in SLUG: SLUG[_l].update(X.SLUG[_l])

def path_of(lang, r):
    return ("" if lang == "pl" else lang + "/") + SLUG[lang][r] + ".html"

def url_of(lang, r):
    return DOMAIN + "/" + path_of(lang, r)

def home_of(lang):
    return DOMAIN + "/" + ("" if lang == "pl" else lang + "/")

# ---------- teksty wspólne ----------
UI = {
 "pl": dict(dtail=["Płatność u kierowcy.", "Odbiór 24/7.", "Bez przedpłaty."], cur="zł", locale="pl_PL", brand=BRAND,
   home="Strona główna", routes="Trasy", book="Zarezerwuj", cap="Liczba osób", day="Dzień", night="Noc",
   c3="Do 3 osób", c8="Do 8 osób", c20="Do 20 osób", c30="Do 30 i 60 osób", req="na zapytanie",
   dist="Dystans", time="Czas jazdy", from_="Cena od", per="za cały pojazd",
   pnote="Cena za cały pojazd, nie za osobę. Ostateczną cenę potwierdzamy przed przejazdem. Stawka nocna obowiązuje w nocy, a 24–26 grudnia dopłata świąteczna +25%.",
   how="Jak wygląda przejazd", pricet="Cennik", faq="Najczęstsze pytania", other="Inne trasy", read="Przydatne artykuły",
   wa="Zarezerwuj na WhatsApp", wa_note="Odpowiadamy zwykle w ciągu kilku minut", call="lub zadzwoń",
   cta_t="Zarezerwuj transfer", cta_s="Napisz na WhatsApp: data, godzina (lub numer lotu), liczba osób i adres — potwierdzimy cenę i termin.",
   form="Formularz rezerwacji", rights="Wszelkie prawa zastrzeżone.",
   why=[("Stała cena","Cena ustalona przed podróżą — bez taksometru i ukrytych opłat."),("Płatność u kierowcy","Gotówką lub kartą, bez przedpłaty online."),("24/7","Odbieramy o każdej porze dnia i nocy."),("Od drzwi do drzwi","Bez przesiadek i bez czekania na innych pasażerów.")]),
 "en": dict(dtail=["Pay the driver.", "24/7 pick-up.", "No prepayment."], cur="PLN", locale="en_GB", brand=BRAND,
   home="Home", routes="Routes", book="Book", cap="Passengers", day="Day", night="Night",
   c3="Up to 3 people", c8="Up to 8 people", c20="Up to 20 people", c30="Up to 30 and 60 people", req="on request",
   dist="Distance", time="Driving time", from_="Price from", per="per vehicle",
   pnote="Price per vehicle, not per person. We confirm the final price before your trip. Night rate applies at night; 24–26 December +25% holiday surcharge.",
   how="How the transfer works", pricet="Prices", faq="Frequently asked questions", other="Other routes", read="Useful articles",
   wa="Book on WhatsApp", wa_note="We usually reply within minutes", call="or call",
   cta_t="Book your transfer", cta_s="Send us on WhatsApp: date, time (or flight number), number of people and address — we will confirm the price and time.",
   form="Booking form", rights="All rights reserved.",
   why=[("Fixed price","Agreed before the trip — no meter, no hidden fees."),("Pay the driver","Cash or card, no online prepayment."),("24/7","Pick-ups at any time of day or night."),("Door to door","No changes and no waiting for other passengers.")]),
 "de": dict(dtail=["Zahlung beim Fahrer.", "Abholung 24/7.", "Ohne Vorauszahlung."], cur="PLN", locale="de_DE", brand=BRAND,
   home="Startseite", routes="Strecken", book="Buchen", cap="Personen", day="Tag", night="Nacht",
   c3="Bis 3 Personen", c8="Bis 8 Personen", c20="Bis 20 Personen", c30="Bis 30 und 60 Personen", req="auf Anfrage",
   dist="Entfernung", time="Fahrzeit", from_="Preis ab", per="pro Fahrzeug",
   pnote="Preis pro Fahrzeug, nicht pro Person. Den Endpreis bestätigen wir vor der Fahrt. Nachts gilt der Nachttarif; 24.–26. Dezember +25 % Feiertagszuschlag.",
   how="So läuft der Transfer ab", pricet="Preise", faq="Häufige Fragen", other="Weitere Strecken", read="Nützliche Artikel",
   wa="Per WhatsApp buchen", wa_note="Wir antworten meist innerhalb weniger Minuten", call="oder anrufen",
   cta_t="Transfer buchen", cta_s="Schreiben Sie uns per WhatsApp: Datum, Uhrzeit (oder Flugnummer), Personenzahl und Adresse — wir bestätigen Preis und Termin.",
   form="Buchungsformular", rights="Alle Rechte vorbehalten.",
   why=[("Festpreis","Vor der Fahrt vereinbart — kein Taxameter, keine versteckten Kosten."),("Zahlung beim Fahrer","Bar oder mit Karte, keine Online-Vorauszahlung."),("24/7","Abholung zu jeder Tages- und Nachtzeit."),("Von Tür zu Tür","Ohne Umsteigen und ohne Warten auf andere Fahrgäste.")]),
 "fr": dict(dtail=["Paiement au chauffeur.", "Service 24h/24.", "Sans prépaiement."], cur="PLN", locale="fr_FR", brand=BRAND,
   home="Accueil", routes="Trajets", book="Réserver", cap="Passagers", day="Jour", night="Nuit",
   c3="Jusqu'à 3 personnes", c8="Jusqu'à 8 personnes", c20="Jusqu'à 20 personnes", c30="Jusqu'à 30 et 60 personnes", req="sur demande",
   dist="Distance", time="Durée du trajet", from_="Prix à partir de", per="par véhicule",
   pnote="Prix par véhicule, pas par personne. Nous confirmons le prix final avant le trajet. Tarif de nuit la nuit ; du 24 au 26 décembre, supplément fêtes de +25 %.",
   how="Comment se déroule le transfert", pricet="Tarifs", faq="Questions fréquentes", other="Autres trajets", read="Articles utiles",
   wa="Réserver sur WhatsApp", wa_note="Nous répondons généralement en quelques minutes", call="ou appelez",
   cta_t="Réservez votre transfert", cta_s="Écrivez-nous sur WhatsApp : date, heure (ou numéro de vol), nombre de personnes et adresse — nous confirmons le prix et l'horaire.",
   form="Formulaire de réservation", rights="Tous droits réservés.",
   why=[("Prix fixe","Convenu avant le trajet — pas de compteur, pas de frais cachés."),("Paiement au chauffeur","En espèces ou par carte, sans prépaiement en ligne."),("24h/24","Prise en charge à toute heure du jour et de la nuit."),("Porte à porte","Sans changement ni attente d'autres passagers.")]),
 "it": dict(dtail=["Pagamento all'autista.", "Servizio 24/7.", "Nessun anticipo."], cur="PLN", locale="it_IT", brand=BRAND,
   home="Home", routes="Tratte", book="Prenota", cap="Passeggeri", day="Giorno", night="Notte",
   c3="Fino a 3 persone", c8="Fino a 8 persone", c20="Fino a 20 persone", c30="Fino a 30 e 60 persone", req="su richiesta",
   dist="Distanza", time="Tempo di viaggio", from_="Prezzo da", per="per veicolo",
   pnote="Prezzo per veicolo, non a persona. Confermiamo il prezzo finale prima del viaggio. Di notte vale la tariffa notturna; dal 24 al 26 dicembre supplemento festivo +25%.",
   how="Come funziona il transfer", pricet="Prezzi", faq="Domande frequenti", other="Altre tratte", read="Articoli utili",
   wa="Prenota su WhatsApp", wa_note="Di solito rispondiamo in pochi minuti", call="oppure chiama",
   cta_t="Prenota il transfer", cta_s="Scrivici su WhatsApp: data, ora (o numero del volo), numero di persone e indirizzo — confermiamo prezzo e orario.",
   form="Modulo di prenotazione", rights="Tutti i diritti riservati.",
   why=[("Prezzo fisso","Concordato prima del viaggio — niente tassametro né costi nascosti."),("Pagamento all'autista","In contanti o con carta, senza pagamento anticipato online."),("24/7","Prelievo a qualsiasi ora del giorno e della notte."),("Porta a porta","Senza cambi e senza attendere altri passeggeri.")]),
 "es": dict(dtail=["Pago al conductor.", "Servicio 24/7.", "Sin prepago."], cur="PLN", locale="es_ES", brand=BRAND,
   home="Inicio", routes="Rutas", book="Reservar", cap="Pasajeros", day="Día", night="Noche",
   c3="Hasta 3 personas", c8="Hasta 8 personas", c20="Hasta 20 personas", c30="Hasta 30 y 60 personas", req="bajo consulta",
   dist="Distancia", time="Tiempo de viaje", from_="Precio desde", per="por vehículo",
   pnote="Precio por vehículo, no por persona. Confirmamos el precio final antes del viaje. De noche se aplica la tarifa nocturna; del 24 al 26 de diciembre, recargo festivo del +25 %.",
   how="Cómo funciona el traslado", pricet="Precios", faq="Preguntas frecuentes", other="Otras rutas", read="Artículos útiles",
   wa="Reservar por WhatsApp", wa_note="Normalmente respondemos en pocos minutos", call="o llame al",
   cta_t="Reserve su traslado", cta_s="Escríbanos por WhatsApp: fecha, hora (o número de vuelo), número de personas y dirección — confirmaremos el precio y la hora.",
   form="Formulario de reserva", rights="Todos los derechos reservados.",
   why=[("Precio fijo","Acordado antes del viaje — sin taxímetro ni costes ocultos."),("Pago al conductor","En efectivo o con tarjeta, sin prepago online."),("24/7","Recogida a cualquier hora del día o de la noche."),("Puerta a puerta","Sin transbordos ni esperas por otros pasajeros.")]),
}

# ---------- teksty tras ----------
# a/b = skąd/dokąd, km, t = czas, title/desc/h1/sub/intro, steps (4), faq (lista par)
def R(lang, r):
    if r in X.NEW_ROUTES: return X.route(lang, r)
    p = P[r]; c = UI[lang]["cur"]
    d3, n3, d8, d20 = p["d3"], p["n3"], p["d8"], p["d20"]
    airport = r != "kz"
    data = {
    "pl": {
     "kr": dict(a="Lotnisko Katowice-Pyrzowice", b="Kraków", km="110 km", t="ok. 1,5 godz.",
        title=f"Transfer Pyrzowice – Kraków od {d3} zł" + " | " + BRAND,
        h1="Transfer z lotniska Pyrzowice do Krakowa",
        sub=f"Prywatny przejazd z lotniska Katowice-Pyrzowice pod wskazany adres w Krakowie — hotel, mieszkanie, biuro. Stała cena od {d3} zł za auto, kierowca czeka w hali przylotów."),
     "zak": dict(a="Lotnisko Katowice-Pyrzowice", b="Zakopane", km="ok. 200 km", t="ponad 3 godz.",
        title=f"Transfer Pyrzowice – Zakopane od {d3} zł" + " | " + BRAND,
        h1="Transfer z lotniska Pyrzowice do Zakopanego",
        sub=f"Bezpośredni przejazd z lotniska Katowice-Pyrzowice prosto pod Twój pensjonat lub hotel w Zakopanem i okolicy. Bez przesiadki w Krakowie, stała cena od {d3} zł za auto."),
     "kz": dict(a="Kraków", b="Zakopane", km="ok. 100 km", t="zwykle ok. 2 godz.",
        title=f"Transfer Kraków – Zakopane od {d3} zł" + " | " + BRAND,
        h1="Prywatny transfer Kraków – Zakopane",
        sub=f"Przejazd od drzwi do drzwi między Krakowem a Zakopanem — z hotelu w Krakowie pod pensjonat w Tatrach lub z powrotem. Stała cena od {d3} zł za auto."),
    },
    "en": {
     "kr": dict(a="Katowice Airport (Pyrzowice)", b="Kraków", km="110 km", t="approx. 1.5 hr",
        title="Katowice Airport Transfer to Kraków" + " | " + BRAND,
        h1="Katowice Airport transfer to Kraków",
        sub=f"Door-to-door ride from Katowice-Pyrzowice Airport (KTW) to your hotel, apartment or office in Kraków. Fixed price from {d3} {c} per vehicle — your driver meets you in the arrivals hall."),
     "zak": dict(a="Katowice Airport (Pyrzowice)", b="Zakopane", km="approx. 200 km", t="3+ hours",
        title="Katowice Airport to Zakopane Transfer" + " | " + BRAND,
        h1="Private transfer from Katowice Airport to Zakopane",
        sub=f"Direct ride from Katowice-Pyrzowice Airport (KTW) to your guesthouse or hotel in Zakopane and the Tatra area. No change in Kraków, fixed price from {d3} {c} per vehicle."),
     "kz": dict(a="Kraków", b="Zakopane", km="approx. 100 km", t="usually about 2 hr",
        title="Kraków to Zakopane Private Transfer" + " | " + BRAND,
        h1="Private transfer Kraków – Zakopane",
        sub=f"Door-to-door ride between Kraków and Zakopane — from your Kraków hotel to your accommodation in the Tatras, or back. Fixed price from {d3} {c} per vehicle."),
    },
    "de": {
     "kr": dict(a="Flughafen Kattowitz (Pyrzowice)", b="Krakau", km="110 km", t="ca. 1,5 Std.",
        title="Transfer Flughafen Kattowitz – Krakau" + " | " + BRAND,
        h1="Privater Transfer vom Flughafen Kattowitz nach Krakau",
        sub=f"Fahrt von Tür zu Tür vom Flughafen Katowice-Pyrzowice (KTW) zu Ihrem Hotel, Ihrer Wohnung oder Ihrem Büro in Krakau. Festpreis ab {d3} {c} pro Fahrzeug — der Fahrer erwartet Sie in der Ankunftshalle."),
     "zak": dict(a="Flughafen Kattowitz (Pyrzowice)", b="Zakopane", km="ca. 200 km", t="über 3 Std.",
        title="Transfer Flughafen Kattowitz – Zakopane" + " | " + BRAND,
        h1="Privater Transfer vom Flughafen Kattowitz nach Zakopane",
        sub=f"Direkte Fahrt vom Flughafen Katowice-Pyrzowice (KTW) zu Ihrer Pension oder Ihrem Hotel in Zakopane und der Tatra-Region. Ohne Umsteigen in Krakau, Festpreis ab {d3} {c} pro Fahrzeug."),
     "kz": dict(a="Krakau", b="Zakopane", km="ca. 100 km", t="meist ca. 2 Std.",
        title="Privater Transfer Krakau – Zakopane" + " | " + BRAND,
        h1="Privater Transfer Krakau – Zakopane",
        sub=f"Fahrt von Tür zu Tür zwischen Krakau und Zakopane — vom Hotel in Krakau zu Ihrer Unterkunft in der Tatra oder zurück. Festpreis ab {d3} {c} pro Fahrzeug."),
    },
    "fr": {
     "kr": dict(a="Aéroport de Katowice (Pyrzowice)", b="Cracovie", km="110 km", t="env. 1 h 30",
        title="Transfert aéroport Katowice – Cracovie" + " | " + BRAND,
        h1="Transfert privé de l'aéroport de Katowice à Cracovie",
        sub=f"Trajet porte à porte de l'aéroport de Katowice-Pyrzowice (KTW) jusqu'à votre hôtel, appartement ou bureau à Cracovie. Prix fixe à partir de {d3} {c} par véhicule — le chauffeur vous attend dans le hall des arrivées."),
     "zak": dict(a="Aéroport de Katowice (Pyrzowice)", b="Zakopane", km="env. 200 km", t="plus de 3 h",
        title="Transfert aéroport Katowice – Zakopane" + " | " + BRAND,
        h1="Transfert privé de l'aéroport de Katowice à Zakopane",
        sub=f"Trajet direct de l'aéroport de Katowice-Pyrzowice (KTW) jusqu'à votre pension ou hôtel à Zakopane et dans les Tatras. Sans changement à Cracovie, prix fixe à partir de {d3} {c} par véhicule."),
     "kz": dict(a="Cracovie", b="Zakopane", km="env. 100 km", t="généralement env. 2 h",
        title="Transfert privé Cracovie – Zakopane" + " | " + BRAND,
        h1="Transfert privé Cracovie – Zakopane",
        sub=f"Trajet porte à porte entre Cracovie et Zakopane — de votre hôtel à Cracovie jusqu'à votre hébergement dans les Tatras, ou retour. Prix fixe à partir de {d3} {c} par véhicule."),
    },
    "it": {
     "kr": dict(a="Aeroporto di Katowice (Pyrzowice)", b="Cracovia", km="110 km", t="circa 1 h 30",
        title="Transfer aeroporto Katowice – Cracovia" + " | " + BRAND,
        h1="Transfer privato dall'aeroporto di Katowice a Cracovia",
        sub=f"Viaggio porta a porta dall'aeroporto di Katowice-Pyrzowice (KTW) al tuo hotel, appartamento o ufficio a Cracovia. Prezzo fisso da {d3} {c} per veicolo — l'autista ti aspetta nella sala arrivi."),
     "zak": dict(a="Aeroporto di Katowice (Pyrzowice)", b="Zakopane", km="circa 200 km", t="oltre 3 ore",
        title="Transfer aeroporto Katowice – Zakopane" + " | " + BRAND,
        h1="Transfer privato dall'aeroporto di Katowice a Zakopane",
        sub=f"Viaggio diretto dall'aeroporto di Katowice-Pyrzowice (KTW) alla tua pensione o al tuo hotel a Zakopane e nei Tatra. Senza cambi a Cracovia, prezzo fisso da {d3} {c} per veicolo."),
     "kz": dict(a="Cracovia", b="Zakopane", km="circa 100 km", t="di solito circa 2 ore",
        title="Transfer privato Cracovia – Zakopane" + " | " + BRAND,
        h1="Transfer privato Cracovia – Zakopane",
        sub=f"Viaggio porta a porta tra Cracovia e Zakopane — dal tuo hotel a Cracovia all'alloggio nei Tatra, o ritorno. Prezzo fisso da {d3} {c} per veicolo."),
    },
    "es": {
     "kr": dict(a="Aeropuerto de Katowice (Pyrzowice)", b="Cracovia", km="110 km", t="aprox. 1 h 30",
        title="Traslado aeropuerto Katowice – Cracovia" + " | " + BRAND,
        h1="Traslado privado del aeropuerto de Katowice a Cracovia",
        sub=f"Trayecto puerta a puerta desde el aeropuerto de Katowice-Pyrzowice (KTW) hasta su hotel, apartamento u oficina en Cracovia. Precio fijo desde {d3} {c} por vehículo — el conductor le espera en la sala de llegadas."),
     "zak": dict(a="Aeropuerto de Katowice (Pyrzowice)", b="Zakopane", km="aprox. 200 km", t="más de 3 h",
        title="Traslado aeropuerto Katowice – Zakopane" + " | " + BRAND,
        h1="Traslado privado del aeropuerto de Katowice a Zakopane",
        sub=f"Trayecto directo desde el aeropuerto de Katowice-Pyrzowice (KTW) hasta su pensión u hotel en Zakopane y los Tatras. Sin transbordo en Cracovia, precio fijo desde {d3} {c} por vehículo."),
     "kz": dict(a="Cracovia", b="Zakopane", km="aprox. 100 km", t="normalmente unas 2 h",
        title="Traslado privado Cracovia – Zakopane" + " | " + BRAND,
        h1="Traslado privado Cracovia – Zakopane",
        sub=f"Trayecto puerta a puerta entre Cracovia y Zakopane — desde su hotel en Cracovia hasta su alojamiento en los Tatras, o de vuelta. Precio fijo desde {d3} {c} por vehículo."),
    }}[lang][r]
    a, b, km, t = data["a"], data["b"], data["km"], data["t"]
    if lang == "pl":
        steps = ([("Rezerwujesz","Na WhatsApp lub w formularzu podajesz datę, numer lotu, liczbę osób i adres docelowy."),
                  ("Śledzimy lot","Monitorujemy przylot — przy opóźnieniu kierowca po prostu czeka."),
                  ("Odbiór z tabliczką","Kierowca czeka w hali przylotów z tabliczką z Twoim nazwiskiem i pomaga z bagażem."),
                  ("Prosto pod adres",f"Jedziesz bez przesiadek prosto pod drzwi — {b}, {km}, {t}.")] if airport else
                 [("Rezerwujesz","Na WhatsApp lub w formularzu podajesz datę, godzinę, liczbę osób i oba adresy."),
                  ("Odbiór spod drzwi","Kierowca przyjeżdża pod hotel lub mieszkanie o umówionej godzinie i pomaga z bagażem."),
                  ("Przerwa po drodze","Na życzenie krótki postój po drodze — wystarczy powiedzieć kierowcy."),
                  ("Prosto pod adres",f"Wysiadasz pod samym pensjonatem — {km}, {t}.")])
        faq = [(f"Ile kosztuje transfer {a} – {b}?", f"Od {d3} zł w dzień ({n3} zł w nocy) za auto do 3 osób, {d8} zł za pojazd do 8 osób i {d20} zł do 20 osób. Cena jest za cały pojazd, nie za osobę, i nie zmienia się w trakcie jazdy."),
               ("Ile trwa przejazd?", f"Trasa ma {km}, przejazd trwa {t}. Czas zależy od ruchu — w weekendy i w sezonie na drodze do Zakopanego bywa dłużej." if r != "kr" else f"Trasa ma {km} i prowadzi autostradą — przejazd trwa {t}, zależnie od ruchu w Krakowie."),
               (("Co jeśli mój lot się opóźni?", "Śledzimy Twój lot i dopasowujemy godzinę odbioru do faktycznego przylotu — za opóźnienie samolotu nie dopłacasz.") if airport else
                ("Czy możecie odebrać mnie z Zakopanego i zawieźć na lotnisko?", "Tak — jeździmy w obie strony, także z Zakopanego lub Krakowa na lotnisko Katowice-Pyrzowice. Wybierz trasę lotniskową w formularzu albo napisz na WhatsApp.")),
               ("Jak się płaci?", "Gotówką lub kartą bezpośrednio u kierowcy. Nie pobieramy przedpłaty online."),
               ("Jak zarezerwować?", "Najszybciej przez WhatsApp albo przez formularz na stronie głównej. Rezerwacje na mniej niż 24 godziny przed przejazdem przyjmujemy tylko przez WhatsApp.")]
    elif lang == "en":
        steps = ([("You book","On WhatsApp or via the form: date, flight number, number of people and destination address."),
                  ("We track your flight","We monitor your arrival — if the flight is late, the driver simply waits."),
                  ("Meet & greet","Your driver waits in the arrivals hall with a name sign and helps with your luggage."),
                  ("Straight to your door",f"No changes, straight to your door — {b}, {km}, {t}.")] if airport else
                 [("You book","On WhatsApp or via the form: date, time, number of people and both addresses."),
                  ("Door pick-up","The driver arrives at your hotel or apartment at the agreed time and helps with luggage."),
                  ("Stop on the way","A short stop on the way on request — just tell the driver."),
                  ("Straight to your door",f"You get out right at your accommodation — {km}, {t}.")])
        faq = [(f"How much is a transfer from {a} to {b}?", f"From {d3} {c} by day ({n3} {c} at night) for a car for up to 3 people, {d8} {c} for up to 8 people and {d20} {c} for up to 20. The price is per vehicle, not per person, and does not change during the ride."),
               ("How long does the ride take?", f"The route is {km} and takes {t}. Traffic matters — at weekends and in high season the road to Zakopane can be slower." if r != "kr" else f"The route is {km}, mostly motorway, and takes {t} depending on Kraków traffic."),
               (("What if my flight is delayed?", "We track your flight and adjust the pick-up to the actual landing time — you pay nothing extra for a delay.") if airport else
                ("Can you take me from Zakopane to the airport?", "Yes — we drive both ways, including from Zakopane or Kraków to Katowice-Pyrzowice Airport. Choose the airport route in the form or message us on WhatsApp.")),
               ("How do I pay?", "Cash or card directly to the driver. No online prepayment."),
               ("How do I book?", "Fastest on WhatsApp, or use the form on the home page. Bookings less than 24 hours before the ride are accepted on WhatsApp only.")]
    elif lang == "de":
        steps = ([("Sie buchen","Per WhatsApp oder Formular: Datum, Flugnummer, Personenzahl und Zieladresse."),
                  ("Wir verfolgen Ihren Flug","Wir beobachten Ihre Ankunft — bei Verspätung wartet der Fahrer einfach."),
                  ("Abholung mit Namensschild","Der Fahrer erwartet Sie in der Ankunftshalle mit Namensschild und hilft beim Gepäck."),
                  ("Direkt vor die Tür",f"Ohne Umsteigen direkt vor die Tür — {b}, {km}, {t}.")] if airport else
                 [("Sie buchen","Per WhatsApp oder Formular: Datum, Uhrzeit, Personenzahl und beide Adressen."),
                  ("Abholung an der Tür","Der Fahrer kommt zur vereinbarten Zeit zu Ihrem Hotel oder Ihrer Wohnung und hilft beim Gepäck."),
                  ("Pause unterwegs","Auf Wunsch ein kurzer Halt unterwegs — sagen Sie es einfach dem Fahrer."),
                  ("Direkt vor die Tür",f"Sie steigen direkt an Ihrer Unterkunft aus — {km}, {t}.")])
        faq = [(f"Was kostet ein Transfer {a} – {b}?", f"Ab {d3} {c} am Tag ({n3} {c} nachts) für ein Auto bis 3 Personen, {d8} {c} bis 8 Personen und {d20} {c} bis 20 Personen. Der Preis gilt pro Fahrzeug, nicht pro Person, und ändert sich während der Fahrt nicht."),
               ("Wie lange dauert die Fahrt?", f"Die Strecke ist {km} lang und dauert {t}. An Wochenenden und in der Saison kann es auf dem Weg nach Zakopane länger dauern." if r != "kr" else f"Die Strecke ist {km} lang, überwiegend Autobahn, und dauert {t}, je nach Verkehr in Krakau."),
               (("Was passiert, wenn mein Flug Verspätung hat?", "Wir verfolgen Ihren Flug und passen die Abholung an die tatsächliche Landung an — für Verspätungen zahlen Sie nichts extra.") if airport else
                ("Fahren Sie auch von Zakopane zum Flughafen?", "Ja — wir fahren in beide Richtungen, auch von Zakopane oder Krakau zum Flughafen Katowice-Pyrzowice. Wählen Sie die Flughafenstrecke im Formular oder schreiben Sie uns per WhatsApp.")),
               ("Wie bezahle ich?", "Bar oder mit Karte direkt beim Fahrer. Keine Online-Vorauszahlung."),
               ("Wie buche ich?", "Am schnellsten per WhatsApp oder über das Formular auf der Startseite. Buchungen weniger als 24 Stunden vor der Fahrt nur per WhatsApp.")]
    elif lang == "fr":
        steps = ([("Vous réservez","Sur WhatsApp ou via le formulaire : date, numéro de vol, nombre de personnes et adresse."),
                  ("Nous suivons votre vol","Nous surveillons votre arrivée — en cas de retard, le chauffeur attend."),
                  ("Accueil avec pancarte","Le chauffeur vous attend dans le hall des arrivées avec une pancarte à votre nom et vous aide avec les bagages."),
                  ("Jusqu'à votre porte",f"Sans changement, jusqu'à votre porte — {b}, {km}, {t}.")] if airport else
                 [("Vous réservez","Sur WhatsApp ou via le formulaire : date, heure, nombre de personnes et les deux adresses."),
                  ("Prise en charge à la porte","Le chauffeur arrive à votre hôtel ou appartement à l'heure convenue et vous aide avec les bagages."),
                  ("Pause en route","Un court arrêt en route sur demande — il suffit de le dire au chauffeur."),
                  ("Jusqu'à votre porte",f"Vous descendez devant votre hébergement — {km}, {t}.")])
        faq = [(f"Combien coûte un transfert {a} – {b} ?", f"À partir de {d3} {c} le jour ({n3} {c} la nuit) pour une voiture jusqu'à 3 personnes, {d8} {c} jusqu'à 8 personnes et {d20} {c} jusqu'à 20 personnes. Le prix est par véhicule, pas par personne, et ne change pas pendant le trajet."),
               ("Combien de temps dure le trajet ?", f"Le trajet fait {km} et dure {t}. Le week-end et en haute saison, la route de Zakopane peut être plus lente." if r != "kr" else f"Le trajet fait {km}, surtout par l'autoroute, et dure {t} selon la circulation à Cracovie."),
               (("Et si mon vol est en retard ?", "Nous suivons votre vol et adaptons la prise en charge à l'heure réelle d'atterrissage — aucun supplément pour un retard.") if airport else
                ("Pouvez-vous me conduire de Zakopane à l'aéroport ?", "Oui — nous roulons dans les deux sens, y compris de Zakopane ou Cracovie vers l'aéroport de Katowice-Pyrzowice. Choisissez le trajet aéroport dans le formulaire ou écrivez-nous sur WhatsApp.")),
               ("Comment payer ?", "En espèces ou par carte, directement au chauffeur. Pas de prépaiement en ligne."),
               ("Comment réserver ?", "Le plus rapide : WhatsApp, ou le formulaire de la page d'accueil. Les réservations à moins de 24 heures du trajet se font uniquement sur WhatsApp.")]
    elif lang == "it":
        steps = ([("Prenoti","Su WhatsApp o tramite il modulo: data, numero del volo, numero di persone e indirizzo."),
                  ("Seguiamo il tuo volo","Monitoriamo l'arrivo — se il volo è in ritardo, l'autista aspetta."),
                  ("Accoglienza con cartello","L'autista ti aspetta nella sala arrivi con un cartello con il tuo nome e ti aiuta con i bagagli."),
                  ("Fino alla porta",f"Senza cambi, fino alla tua porta — {b}, {km}, {t}.")] if airport else
                 [("Prenoti","Su WhatsApp o tramite il modulo: data, ora, numero di persone ed entrambi gli indirizzi."),
                  ("Prelievo alla porta","L'autista arriva al tuo hotel o appartamento all'ora concordata e ti aiuta con i bagagli."),
                  ("Sosta lungo la strada","Una breve sosta lungo il percorso su richiesta — basta dirlo all'autista."),
                  ("Fino alla porta",f"Scendi davanti al tuo alloggio — {km}, {t}.")])
        faq = [(f"Quanto costa un transfer {a} – {b}?", f"Da {d3} {c} di giorno ({n3} {c} di notte) per un'auto fino a 3 persone, {d8} {c} fino a 8 persone e {d20} {c} fino a 20. Il prezzo è per veicolo, non a persona, e non cambia durante il viaggio."),
               ("Quanto dura il viaggio?", f"Il percorso è di {km} e dura {t}. Nei fine settimana e in alta stagione la strada per Zakopane può essere più lenta." if r != "kr" else f"Il percorso è di {km}, soprattutto in autostrada, e dura {t} a seconda del traffico a Cracovia."),
               (("E se il mio volo è in ritardo?", "Seguiamo il tuo volo e adattiamo il prelievo all'orario reale di atterraggio — nessun costo extra per il ritardo.") if airport else
                ("Potete portarmi da Zakopane all'aeroporto?", "Sì — viaggiamo in entrambe le direzioni, anche da Zakopane o Cracovia all'aeroporto di Katowice-Pyrzowice. Scegli la tratta aeroporto nel modulo o scrivici su WhatsApp.")),
               ("Come si paga?", "In contanti o con carta direttamente all'autista. Nessun pagamento anticipato online."),
               ("Come prenoto?", "Il modo più veloce è WhatsApp, oppure il modulo nella home page. Le prenotazioni a meno di 24 ore dal viaggio si accettano solo su WhatsApp.")]
    else:
        steps = ([("Usted reserva","Por WhatsApp o en el formulario: fecha, número de vuelo, número de personas y dirección."),
                  ("Seguimos su vuelo","Controlamos su llegada — si el vuelo se retrasa, el conductor simplemente espera."),
                  ("Recogida con cartel","El conductor le espera en la sala de llegadas con un cartel con su nombre y le ayuda con el equipaje."),
                  ("Hasta su puerta",f"Sin transbordos, hasta su puerta — {b}, {km}, {t}.")] if airport else
                 [("Usted reserva","Por WhatsApp o en el formulario: fecha, hora, número de personas y ambas direcciones."),
                  ("Recogida en la puerta","El conductor llega a su hotel o apartamento a la hora acordada y le ayuda con el equipaje."),
                  ("Parada en el camino","Una breve parada en el camino si lo desea — solo dígaselo al conductor."),
                  ("Hasta su puerta",f"Baja justo en su alojamiento — {km}, {t}.")])
        faq = [(f"¿Cuánto cuesta un traslado {a} – {b}?", f"Desde {d3} {c} de día ({n3} {c} de noche) por un coche para hasta 3 personas, {d8} {c} hasta 8 personas y {d20} {c} hasta 20. El precio es por vehículo, no por persona, y no cambia durante el trayecto."),
               ("¿Cuánto dura el trayecto?", f"La ruta tiene {km} y dura {t}. Los fines de semana y en temporada alta la carretera a Zakopane puede ser más lenta." if r != "kr" else f"La ruta tiene {km}, casi todo autopista, y dura {t} según el tráfico en Cracovia."),
               (("¿Y si mi vuelo se retrasa?", "Seguimos su vuelo y ajustamos la recogida a la hora real de aterrizaje — no paga nada extra por el retraso.") if airport else
                ("¿Pueden llevarme de Zakopane al aeropuerto?", "Sí — viajamos en ambos sentidos, también desde Zakopane o Cracovia al aeropuerto de Katowice-Pyrzowice. Elija la ruta al aeropuerto en el formulario o escríbanos por WhatsApp.")),
               ("¿Cómo se paga?", "En efectivo o con tarjeta directamente al conductor. Sin prepago online."),
               ("¿Cómo reservo?", "Lo más rápido es WhatsApp, o el formulario de la página de inicio. Las reservas con menos de 24 horas de antelación solo por WhatsApp.")]
    data["steps"], data["faq"] = steps, faq
    data["desc"] = DESC[(lang, r)].format(d3=d3) if (lang, r) in DESC else fit_desc(data["sub"], UI[lang]["dtail"])
    return data

# meta description (150-160 znaków) dla każdej trasy i języka
DESC={
('pl','kr'):"Prywatny transfer z lotniska Katowice-Pyrzowice pod adres w Krakowie. Stała cena od {d3} zł za auto, kierowca z tabliczką w hali przylotów, płatność u kierowcy.",
('pl','zak'):"Bezpośredni transfer z lotniska Katowice-Pyrzowice do Zakopanego, bez przesiadki w Krakowie. Stała cena od {d3} zł za auto, odbiór 24/7, płatność u kierowcy.",
('pl','kz'):"Prywatny przejazd Kraków – Zakopane od drzwi do drzwi, z hotelu pod pensjonat w Tatrach lub z powrotem. Stała cena od {d3} zł za auto, płatność u kierowcy.",
('en','kr'):"Private transfer from Katowice Airport (KTW) to any address in Kraków. Fixed price from {d3} PLN per vehicle, meet & greet in arrivals, pay the driver.",
('en','zak'):"Direct private transfer from Katowice Airport (KTW) to Zakopane, no change in Kraków. Fixed price from {d3} PLN per vehicle, 24/7 pick-up, pay the driver.",
('en','kz'):"Door-to-door private transfer between Kraków and Zakopane, from your Kraków hotel to your Tatra accommodation or back. Fixed price from {d3} PLN per vehicle.",
('de','kr'):"Privater Transfer vom Flughafen Kattowitz (KTW) zu jeder Adresse in Krakau. Festpreis ab {d3} PLN pro Fahrzeug, Abholung mit Namensschild, Zahlung beim Fahrer.",
('de','zak'):"Direkter Privattransfer vom Flughafen Kattowitz (KTW) nach Zakopane, ohne Umsteigen in Krakau. Festpreis ab {d3} PLN pro Fahrzeug, Abholung rund um die Uhr.",
('de','kz'):"Privater Transfer von Tür zu Tür zwischen Krakau und Zakopane – vom Hotel zu Ihrer Unterkunft in der Tatra oder zurück. Festpreis ab {d3} PLN pro Fahrzeug.",
('fr','kr'):"Transfert privé de l'aéroport de Katowice (KTW) à votre adresse à Cracovie. Prix fixe dès {d3} PLN par véhicule, accueil avec pancarte, paiement au chauffeur.",
('fr','zak'):"Transfert privé direct de l'aéroport de Katowice (KTW) à Zakopane, sans changement à Cracovie. Prix fixe dès {d3} PLN par véhicule, prise en charge 24h/24.",
('fr','kz'):"Transfert privé porte à porte entre Cracovie et Zakopane, de votre hôtel à votre hébergement dans les Tatras ou retour. Prix fixe dès {d3} PLN par véhicule.",
('it','kr'):"Transfer privato dall'aeroporto di Katowice (KTW) al tuo indirizzo a Cracovia. Prezzo fisso da {d3} PLN per veicolo, autista con cartello, pagamento a bordo.",
('it','zak'):"Transfer privato diretto dall'aeroporto di Katowice (KTW) a Zakopane, senza cambi a Cracovia. Prezzo fisso da {d3} PLN per veicolo, servizio 24 ore su 24.",
('it','kz'):"Transfer privato porta a porta tra Cracovia e Zakopane, dal tuo hotel all'alloggio nei Tatra o ritorno. Prezzo fisso da {d3} PLN per veicolo, pagamento a bordo.",
('es','kr'):"Traslado privado del aeropuerto de Katowice (KTW) a su dirección en Cracovia. Precio fijo desde {d3} PLN por vehículo, recogida con cartel, pago al conductor.",
('es','zak'):"Traslado privado directo del aeropuerto de Katowice (KTW) a Zakopane, sin transbordo en Cracovia. Precio fijo desde {d3} PLN por vehículo, servicio 24 horas.",
('es','kz'):"Traslado privado puerta a puerta entre Cracovia y Zakopane, de su hotel a su alojamiento en los Tatras o de vuelta. Precio fijo desde {d3} PLN por vehículo.",
}

def fit_desc(text, tails):
    # meta description 150-160 znaków: dokleja krótkie zdania z listy, a za długi tekst tnie na słowie
    out = text
    for t in tails:
        if len(out) >= 150: break
        if len(out) + 1 + len(t) <= 160: out = out + " " + t
    if len(out) > 160:
        out = out[:157].rsplit(" ", 1)[0].rstrip(",—–:; ") + "…"
    return out

import route_topics as RT  # dopasowanie artykułów do tras po temacie (wspólne z link-routes.py)

def articles(lang, r, n=6):
    """Najlepiej pasujące artykuły w tym języku (temat oceniany na wersji PL), max n."""
    d = "blog" if lang == "pl" else f"blog/{lang}"
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, d, "*.html"))):
        rel = os.path.relpath(f, ROOT)
        s = RT.post_scores(rel)
        if s[r] <= 0 or r not in RT.routes_for(rel): continue
        t = re.search(r"<title>(.*?)</title>", open(f, encoding="utf-8").read(), re.S)
        if t: out.append((-s[r], DOMAIN + "/" + rel, html.unescape(t.group(1)).split(" | ")[0]))
    out.sort()
    return [(u, t) for _, u, t in out[:n]]

WA_SVG = re.search(r'(<svg viewBox="0 0 24 24" fill="#08331b">.*?</svg>)', SRC, re.S).group(1)

EXTRA_CSS = """
  .rt-hero h1{font-size:clamp(34px,5vw,56px)}
  .rt-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:6px}
  .rt-fact{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:14px 16px}
  .rt-fact .k{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mist)}
  .rt-fact .v{font-size:20px;font-weight:600;color:#fff;margin-top:4px}
  .rt-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}
  .rt-faq details{background:#fff;border-radius:12px;padding:16px 18px;margin-bottom:10px;border:1px solid rgba(0,0,0,.06)}
  .rt-faq summary{cursor:pointer;font-weight:600}
  .rt-faq p{margin:10px 0 0;line-height:1.6}
  .rt-links{display:flex;flex-wrap:wrap;gap:10px}
  .rt-links a{display:inline-block;padding:10px 14px;border-radius:999px;background:#fff;border:1px solid rgba(0,0,0,.1);color:inherit;text-decoration:none;font-weight:500}
  .rt-note{font-size:14px;opacity:.8;margin-top:12px}
  .rt-about{max-width:820px}.rt-about h3{margin:22px 0 8px}.rt-about p{margin:0;line-height:1.7}
  .rt-quote{max-width:760px;line-height:1.7;margin:0 0 18px}
  .rt-formlink{font-weight:600;color:inherit;margin-left:14px}
  .crumbs{font-size:13px;color:var(--mist);margin-bottom:14px}.crumbs a{color:inherit}
  @media (max-width:820px){.rt-facts{grid-template-columns:1fr}.rt-steps{grid-template-columns:1fr 1fr}}
  @media (max-width:520px){.rt-steps{grid-template-columns:1fr}}
"""

def esc(s): return html.escape(s, quote=True)

def page(lang, r):
    u, d = UI[lang], R(lang, r)
    priced = r in P
    p = P.get(r); c = u["cur"]; x = X.UI[lang]
    wa = "https://wa.me/" + PHONE + "?text=" + urllib.parse.quote(f"{d['h1']} — ")
    home = home_of(lang)
    rel_home = "index.html" if lang == "pl" else "./"
    alts = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{url_of(l, r)}">' for l in LANGS) + f'\n<link rel="alternate" hreflang="x-default" href="{url_of("pl", r)}">'
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faq"]]}
    svc_ld = {"@context": "https://schema.org", "@type": "TaxiService", "@id": url_of(lang, r) + "#service", "name": d["h1"], "url": url_of(lang, r),
              "serviceType": "Private transfer", "description": d["desc"], "inLanguage": lang,
              "provider": {"@id": ORG["@id"]},
              "areaServed": [{"@type": "Place", "name": d["a"]}, {"@type": "Place", "name": d["b"]}] if not priced else [{"@type": "Place", "name": d["a"]}, {"@type": "City", "name": d["b"]}]}
    if priced:
        svc_ld["offers"] = {"@type": "Offer", "price": str(p["d3"]), "priceCurrency": "PLN", "url": url_of(lang, r),
                            "description": u["c3"] + ", " + u["day"].lower() + " — " + u["per"]}
    bc_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": u["home"], "item": home},
              {"@type": "ListItem", "position": 2, "name": d["h1"], "item": url_of(lang, r)}]}
    rows = "" if not priced else "".join(f'<tr><td class="veh">{u[k]}</td><td class="price mono">{p["d"+n]} {c}</td><td class="price mono">{p["n"+n]} {c}</td></tr>' for k, n in [("c3", "3"), ("c8", "8"), ("c20", "20")])
    if priced: rows += f'<tr><td class="veh">{u["c30"]}</td><td class="price mono" colspan="2" style="text-align:left;">{u["req"]}</td></tr>'
    steps = "".join(f'<div class="why-item"><div class="num mono">0{i+1}</div><h3>{esc(t)}</h3><p>{esc(x.replace("..", "."))}</p></div>' for i, (t, x) in enumerate(d["steps"]))
    why = "".join(f'<div class="why-item"><div class="num mono">0{i+1}</div><h3>{esc(t)}</h3><p>{esc(x)}</p></div>' for i, (t, x) in enumerate(u["why"]))
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in d["faq"])
    others = "".join(f'<a href="{url_of(lang, o)}">{esc(R(lang, o)["h1"])}</a>' for o in ROUTES if o != r)
    arts = articles(lang, r)
    arts_html = (f'<h3 style="margin:28px 0 12px">{u["read"]}</h3><div class="rt-links">' + "".join(f'<a href="{a}">{esc(t)}</a>' for a, t in arts) + "</div>") if arts else ""
    if priced:
        facts = [(u["dist"], d["km"], ""), (u["time"], d["t"], ""), (u["from_"], f"{p['d3']} {c}", u["per"])]
    else:
        facts = [(k, v, "") for k, v in [(u["dist"], d["km"]), (u["time"], d["t"]), (x["pick"], "24/7"), (x["pay"], x["pay_v"])] if v][:2]
        facts.append((u["from_"].split(" ")[0] if lang != "pl" else "Cena", x["onreq"], x["onreq_k"]))
    facts_html = "".join(f'<div class="rt-fact"><div class="k">{esc(k)}</div><div class="v mono">{esc(v)}</div>' + (f'<div class="k" style="margin-top:4px">{esc(s2)}</div>' if s2 else "") + '</div>' for k, v, s2 in facts)
    about_html = ""
    if d.get("about"):
        about_html = (f'<section id="about"><div class="wrap"><div class="section-head"><h2>{esc(x["about"])}</h2></div><div class="rt-about">'
                      + "".join(f'<h3>{esc(h)}</h3><p>{esc(t)}</p>' for h, t in d["about"]) + '</div></div></section>')
    g = G.GUIDES.get((lang, r))
    if g:
        about_html += (f'<section id="guide"><div class="wrap"><div class="section-head"><h2>{esc(g[0])}</h2></div><div class="rt-about">'
                       + "".join(f'<h3>{esc(h)}</h3><p>{esc(t)}</p>' for h, t in g[1]) + '</div></div></section>')
    if priced:
        price_html = f"""<div class="section-head"><h2>{u['pricet']}: {esc(d['a'])} ↔ {esc(d['b'])}</h2></div>
    <div class="price-table-wrap"><table class="price-table">
      <thead><tr><th>{u['cap']}</th><th>{u['day']}</th><th>{u['night']}</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
    <p class="rt-note">{u['pnote']}</p>"""
    else:
        price_html = f"""<div class="section-head"><h2>{esc(x['quote_t'])}</h2></div>
    <p class="rt-quote">{esc(x['quote_s'])}</p>
    <div class="cta-row"><a href="{wa}" class="btn-wa" target="_blank" rel="noopener">{WA_SVG}<span>{u['wa']}</span></a> <a href="{rel_home}#book" class="rt-formlink">{u['form']} →</a></div>"""
    langs_html = " · ".join(f'<a href="{url_of(l, r)}"{" aria-current=\"page\"" if l == lang else ""}>{l.upper()}</a>' for l in LANGS)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(d['title'])}</title>
<meta name="description" content="{esc(d['desc'])}">
<link rel="canonical" href="{url_of(lang, r)}">
{alts}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{u['brand']}">
<meta property="og:title" content="{esc(d['title'])}">
<meta property="og:description" content="{esc(d['desc'])}">
<meta property="og:url" content="{url_of(lang, r)}">
<meta property="og:image" content="{DOMAIN}/images/vito.jpg">
<meta property="og:locale" content="{u['locale']}">
<script type="application/ld+json">{json.dumps(ORG, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(svc_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA_CSS}</style>
</head>
<body>
<header>
  <div class="nav">
    <a class="logo" href="{rel_home}" style="text-decoration:none">KATOWICE PYRZOWICE<span>AIRPORT TRANSFERS</span></a>
    <nav class="nav-links">
      <a href="{rel_home}">{u['home']}</a>
      <a href="{rel_home}#routes">{u['routes']}</a>
      <a href="{wa}" class="nav-cta" target="_blank" rel="noopener">{u['book']}</a>
    </nav>
  </div>
</header>

<section class="hero rt-hero" id="home">
  <div class="wrap hero-grid">
    <div>
      <p class="crumbs"><a href="{rel_home}">{u['home']}</a> / {esc(d['b'])}</p>
      <h1>{esc(d['h1'])}</h1>
      <p class="sub">{esc(d['sub'])}</p>
      <div class="cta-row">
        <a href="{wa}" class="btn-wa" target="_blank" rel="noopener">{WA_SVG}<span>{u['wa']}</span></a>
        <span class="hero-note">{u['wa_note']}</span>
      </div>
    </div>
    <div class="rt-facts">{facts_html}</div>
  </div>
</section>

{about_html}

<section id="how">
  <div class="wrap">
    <div class="section-head"><h2>{u['how']}</h2></div>
    <div class="why-grid rt-steps">{steps}</div>
  </div>
</section>

<section id="routes" style="background:var(--fog);">
  <div class="wrap">
    {price_html}
  </div>
</section>

<section id="why">
  <div class="wrap"><div class="why-grid">{why}</div></div>
</section>

<section id="faq" style="background:var(--fog);">
  <div class="wrap rt-faq">
    <div class="section-head"><h2>{u['faq']}</h2></div>
    {faq}
    <h3 style="margin:28px 0 12px">{u['other']}</h3>
    <div class="rt-links">{others}<a href="{rel_home}#book">{u['form']}</a></div>
    {arts_html}
  </div>
</section>

<section id="contact" style="background:var(--fog); padding-bottom:70px;">
  <div class="contact">
    <h2>{u['cta_t']}</h2>
    <p>{u['cta_s']}</p>
    <a href="{wa}" class="btn-wa" target="_blank" rel="noopener">{WA_SVG}<span>{u['wa']}</span></a>
    <div class="phone-line">{u['call']}: <span>+48 728 814 659</span></div>
  </div>
</section>

<footer>
  <div class="wrap footer-row">
    <div>Wojciech Rzepka — Xtrip · {u['rights']} © 2026</div>
    <div>{langs_html} · <a href="{DOMAIN}/blog.html">Blog</a> · <a href="https://vibekrakow.pl/">Day trips from Kraków – Vibe Krakow</a></div>
  </div>
</footer>
</body>
</html>
"""

# ---------- linki do nowych tras na stronach głównych (między znacznikami, idempotentnie) ----------
HOME_LINKS = {
 "pl": ("Więcej tras", ["Lotnisko Balice → centrum Krakowa", "Lotnisko Balice → Zakopane", "Kraków → Auschwitz-Birkenau", "Kraków → Kopalnia Soli Wieliczka", "Kraków / Pyrzowice → Energylandia"]),
 "en": ("More routes", ["Kraków Airport → city centre", "Kraków Airport → Zakopane", "Kraków → Auschwitz-Birkenau", "Kraków → Wieliczka Salt Mine", "Kraków / Katowice Airport → Energylandia"]),
 "de": ("Weitere Strecken", ["Flughafen Krakau → Stadtzentrum", "Flughafen Krakau → Zakopane", "Krakau → Auschwitz-Birkenau", "Krakau → Salzbergwerk Wieliczka", "Krakau / Flughafen Kattowitz → Energylandia"]),
 "fr": ("Autres trajets", ["Aéroport de Cracovie → centre-ville", "Aéroport de Cracovie → Zakopane", "Cracovie → Auschwitz-Birkenau", "Cracovie → mine de sel de Wieliczka", "Cracovie / aéroport de Katowice → Energylandia"]),
 "it": ("Altre tratte", ["Aeroporto di Cracovia → centro", "Aeroporto di Cracovia → Zakopane", "Cracovia → Auschwitz-Birkenau", "Cracovia → miniera di sale di Wieliczka", "Cracovia / aeroporto di Katowice → Energylandia"]),
 "es": ("Más rutas", ["Aeropuerto de Cracovia → centro", "Aeropuerto de Cracovia → Zakopane", "Cracovia → Auschwitz-Birkenau", "Cracovia → mina de sal de Wieliczka", "Cracovia / aeropuerto de Katowice → Energylandia"]),
}
HOME_OTHER = {"uk": "Інші маршрути", "mt": "Aktar rotot", "ar": "مسارات أخرى"}  # te strony linkują do wersji EN

def update_homepages():
    S, E = "<!-- routes-more:start -->", "<!-- routes-more:end -->"
    for hl in LANGS + list(HOME_OTHER):
        fp = os.path.join(ROOT, "index.html" if hl == "pl" else f"{hl}/index.html")
        if not os.path.exists(fp): continue
        tl = hl if hl in HOME_LINKS else "en"
        head = HOME_LINKS[tl][0] if hl in HOME_LINKS else HOME_OTHER[hl] + " (EN)"
        extra = "" if hl in HOME_LINKS else ' hreflang="en"'
        links = "".join(f'<a href="{url_of(tl, r)}"{extra} style="display:inline-block;padding:9px 14px;border-radius:999px;background:#fff;border:1px solid rgba(0,0,0,.1);color:inherit;text-decoration:none;font-weight:500;font-size:14px;">{esc(t)}</a>'
                        for r, t in zip(X.NEW_ROUTES, HOME_LINKS[tl][1]))
        block = f'{S}\n    <h3 class="price-city-head">{esc(head)}</h3>\n    <div class="routes-more" style="display:flex;flex-wrap:wrap;gap:10px;margin:0 0 28px;">{links}</div>\n    {E}'
        h = open(fp, encoding="utf-8").read()
        if S in h:
            h = re.sub(re.escape(S) + r".*?" + re.escape(E), lambda m: block, h, flags=re.S)
        else:
            i = h.index('<div class="route-other">')
            h = h[:i] + block + "\n\n    " + h[i:]
        open(fp, "w", encoding="utf-8").write(h)

if __name__ == "__main__":
    update_homepages()
    n = 0
    for lang in LANGS:
        for r in ROUTES:
            fp = os.path.join(ROOT, path_of(lang, r))
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, "w", encoding="utf-8").write(page(lang, r)); n += 1
    print(f"Podstrony tras: {n}")
