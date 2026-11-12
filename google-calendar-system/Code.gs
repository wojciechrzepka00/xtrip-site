/**
 * KATOWICE PYRZOWICE AIRPORT TRANSFERS — system rezerwacji
 * -----------------------------------------------------------
 * Ten plik wklejasz do Google Apps Script (script.google.com).
 * Działa na TWOIM koncie Google — to ono jest "loginem" do systemu.
 *
 * Co robi:
 * 1) doPost(e)  — odbiera zgłoszenie z formularza na stronie, tworzy
 *                 wydarzenie w Twoim Kalendarzu Google, WYSYŁA DO CIEBIE
 *                 (OWNER_EMAIL) powiadomienie o nowej rezerwacji z pełnymi
 *                 danymi klienta, i — jeśli klient podał e-mail — wysyła
 *                 też jemu potwierdzenie ze wszystkimi szczegółami.
 * 2) doGet(e)   — wyświetla panel (Index.html) z listą najbliższych
 *                 rezerwacji i przyciskiem "Kopiuj dane dla kierowcy".
 * 3) Jeśli klient poda numer lotu I skonfigurujesz AVIATIONSTACK_API_KEY
 *    (patrz niżej) — system sam sprawdzi skąd leci ten samolot i doda
 *    tę informację zarówno do Twojego powiadomienia, jak i do maila
 *    z potwierdzeniem dla klienta.
 *
 * KONFIGURACJA (zrób raz):
 * 1. Wejdź na script.google.com -> Nowy projekt.
 * 2. Wklej ten kod jako Code.gs, a zawartość Index.html jako osobny
 *    plik HTML o nazwie "Index".
 * 3. Kliknij Wdróż -> Nowe wdrożenie -> Aplikacja internetowa.
 *    - "Wykonaj jako": Ja (Twoje konto)
 *    - "Kto ma dostęp": Tylko ja  <-- to jest Twoje "logowanie"
 * 4. Skopiuj adres URL wdrożenia — to jest link do Twojego panelu
 *    rezerwacji. Otwórz go zalogowany na swoje konto Google.
 * 5. Dla formularza na stronie: potrzebny będzie oddzielny URL
 *    z dostępem "Każdy" (żeby klienci mogli wysyłać zgłoszenia) —
 *    zrób DRUGIE wdrożenie tego samego kodu z dostępem "Każdy",
 *    i ten adres wklej do zmiennej BOOKING_ENDPOINT w index.html strony.
 *
 * UWAGA o mailach: wysyłka idzie z office@vibekrakow.pl przez serwer Vibe (wyslijZVibe);
 * awaryjnie MailApp z konta Google, który liczy się do limitu Google
 * Workspace i liczy się do dziennego limitu (100 maili/dzień na zwykłym
 * koncie Gmail, więcej na Google Workspace) — dla startu w zupełności
 * wystarczy, ale warto o tym pamiętać przy większej skali.
 */

const CALENDAR_ID = "primary"; // Twój główny kalendarz Google
const COMPANY_NAME = "Katowice Pyrzowice Airport Transfers";
const COMPANY_PHONE = "+48 728 814 659";
const OWNER_EMAIL = "office@vibekrakow.pl"; // skrzynka Vibe Krakow (SOR → zakładka Poczta) — tu przychodzi powiadomienie o KAŻDEJ nowej rezerwacji
const SENDER_EMAIL = "office@vibekrakow.pl"; // nadawca wszystkich maili
// Maile idą przez serwer pocztowy Vibe (MyDevil) — funkcja Netlify vibe-mail-mcp, nie przez Gmaila.
const VIBE_MAIL_URL = "https://vibe-mail-mcp.netlify.app/rezerwacja-mail";
const VIBE_MAIL_KEY = "WKLEJ_KLUCZ"; // klucz tylko w Apps Script, nie w publicznym repo

// Wysyła maila z office@vibekrakow.pl. Gdyby serwer Vibe nie odpowiedział — awaryjnie z Gmaila (MailApp),
// żeby żadna rezerwacja nie przepadła.
function wyslijZVibe(m) {
  try {
    const res = UrlFetchApp.fetch(VIBE_MAIL_URL, {
      method: "post", contentType: "application/json", headers: { "x-token": VIBE_MAIL_KEY },
      payload: JSON.stringify(m), muteHttpExceptions: true,
    });
    const out = JSON.parse(res.getContentText() || "{}");
    if (out.ok) return;
    console.error("Vibe SMTP błąd:", res.getResponseCode(), res.getContentText());
  } catch (err) {
    console.error("Vibe SMTP niedostępny:", err.message);
  }
  const fb = { to: m.to, subject: m.subject, name: m.name };
  if (m.html) fb.htmlBody = m.html; else fb.body = m.text;
  if (m.replyTo) fb.replyTo = m.replyTo;
  else fb.replyTo = SENDER_EMAIL;
  MailApp.sendEmail(fb);
}
// ==== SOR (logistyka.przewoz-osob-krakow.pl) — każda rezerwacja zakładana automatycznie ====
// Klucz API NIE jest w kodzie: Apps Script → Ustawienia projektu → Właściwości skryptu → KT_API_KEY
const SOR_ENDPOINT = "https://logistyka.przewoz-osob-krakow.pl/api/rezerwacje";
const SOR_LOTNISKO = "Lotnisko Katowice-Pyrzowice (KTW)";
const SOR_AUTA = { cap_3: "Sedan", cap_8: "Van", cap_20: "Minibus", cap_30: "Minibus", cap_60: "Minibus" };
const SOR_MIASTA = { krakow: "Kraków", zakopane: "Zakopane" };

function sorPayload(data, flightOrigin) {
  const dt = String(data.datetime || "");
  const adres = data.address || (data.notes ? String(data.notes).replace(/^Adres:\s*/, "") : "");
  const miasto = SOR_MIASTA[data.city] || data.city || "";
  let skad = "", dokad = "", odbior = "";
  if (data.routeType === "airport") {
    if (data.direction === "to_airport") { skad = miasto; dokad = SOR_LOTNISKO; odbior = adres ? `${miasto}, ${adres}` : miasto; }
    else { skad = SOR_LOTNISKO; dokad = adres ? `${miasto}, ${adres}` : miasto; odbior = SOR_LOTNISKO; }
  } else if (data.routeType) {
    const kz = data.kzDirection === "zakopane_to_krakow";
    skad = kz ? "Zakopane" : "Kraków"; dokad = kz ? "Kraków" : "Zakopane";
    odbior = adres ? `${skad}, ${adres}` : skad;
  }
  const cena = Number(data.priceValue) || 0;
  const uwagi = [
    "Rezerwacja ze strony krakow-transfers.com",
    `Trasa (formularz): ${data.route || "-"}`,
    adres ? `Adres: ${adres}` : "",
    flightOrigin ? `Lot z: ${flightOrigin}` : "",
    cena ? "" : "CENA NA ZAPYTANIE — ustal z klientem",
    "Płatność: u kierowcy (gotówka/karta)",
  ].filter(Boolean).join("\n");
  const p = {
    data: dt.slice(0, 10),
    godzina: dt.slice(11, 16),
    liczba_osob: parseInt(data.passengers, 10) || 1,
    cena: cena,
    waluta: "PLN",
    imie_nazwisko: `${data.firstName || ""} ${data.lastName || ""}`.trim() || "-",
    skad: skad || data.route || "",
    dokad: dokad,
    adres_odbioru: odbior,
    numer_lotu: data.flightNo || "",
    typ_auta: SOR_AUTA[data.vehicleCode] || data.vehicle || "",
    telefon: data.phone || "",
    email: data.email || "",
    uwagi: uwagi,
    jezyk: data.lang || "",
    oplacone: false,
    zewnetrzny_id: `KT-WEB-${dt}-${String(data.phone || "").replace(/\D/g, "")}`,
  };
  Object.keys(p).forEach(k => { if (p[k] === "") delete p[k]; });
  return p;
}

// Zakłada rezerwację w SOR. Zwraca krótki opis wyniku (trafia do maila [KT-REZ]); nigdy nie przerywa rezerwacji.
function wyslijDoSOR(data, flightOrigin) {
  const key = PropertiesService.getScriptProperties().getProperty("KT_API_KEY");
  if (!key) return "SOR: brak klucza KT_API_KEY w ustawieniach skryptu — nie wysłano";
  try {
    const res = UrlFetchApp.fetch(SOR_ENDPOINT, {
      method: "post", contentType: "application/json", headers: { "X-API-Key": key },
      payload: JSON.stringify(sorPayload(data, flightOrigin)), muteHttpExceptions: true,
    });
    const code = res.getResponseCode();
    let out = {}; try { out = JSON.parse(res.getContentText() || "{}"); } catch (e) {}
    if (code === 201) return `SOR: założona rezerwacja #${out.reservation_id}` + (out.price_pln ? ` (${out.price_pln} zł)` : "");
    if (code === 200 && out.status === "exists") return `SOR: rezerwacja już była (#${out.reservation_id}) — duplikat zgłoszenia`;
    return `SOR: BŁĄD HTTP ${code} — ${res.getContentText().slice(0, 300)} — ZAŁÓŻ RĘCZNIE`;
  } catch (err) {
    return `SOR: BŁĄD połączenia — ${err.message} — ZAŁÓŻ RĘCZNIE`;
  }
}

// Test ręczny z edytora (tworzy prawdziwą rezerwację w SOR — potem ją usuń).
function testSOR() {
  console.log(wyslijDoSOR({
    firstName: "TEST", lastName: "Claude (usunąć)", phone: "+48539004008", email: "office@vibekrakow.pl",
    flightNo: "FR1234", route: "Z lotniska do miasta (Kraków)", routeType: "airport", city: "krakow",
    direction: "from_airport", address: "Rynek Główny 1", passengers: "2", vehicleCode: "cap_3",
    priceValue: 250, datetime: "2026-12-31T12:00", lang: "pl",
  }, null));
}

const OWNER_SUBJECT_TAG = "[KT-REZ]"; // stały znacznik w temacie — po nim SOR/robocik i filtry rozpoznają rezerwacje z krakow-transfers.com

// Klucz API do sprawdzania skąd leci dany numer lotu (opcjonalne — zostaw puste, żeby wyłączyć).
// Załóż darmowe konto na aviationstack.com -> Dashboard -> "Your API Access Key" -> wklej poniżej.
// Darmowy plan: 100 zapytań/miesiąc. Przy większej liczbie rezerwacji trzeba przejść na płatny plan.
const AVIATIONSTACK_API_KEY = "";

// Sprawdza skąd leci dany numer lotu (np. "FR1234"). Zwraca np. "Londyn (STN)" albo null, jeśli się nie uda.
function lookupFlightOrigin(flightNo) {
  if (!AVIATIONSTACK_API_KEY || !flightNo) return null;
  try {
    const clean = flightNo.replace(/\s+/g, "").toUpperCase();
    const url = `https://api.aviationstack.com/v1/flights?access_key=${AVIATIONSTACK_API_KEY}&flight_iata=${encodeURIComponent(clean)}`;
    const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    const data = JSON.parse(res.getContentText());

    if (!data.data || data.data.length === 0) return null;

    const flight = data.data[0];
    const airportName = flight.departure && flight.departure.airport;
    const iata = flight.departure && flight.departure.iata;
    if (!airportName) return null;

    return iata ? `${airportName} (${iata})` : airportName;
  } catch (err) {
    console.error("Błąd sprawdzania lotu:", err.message);
    return null; // nie przerywamy całej rezerwacji, jeśli sprawdzenie lotu się nie uda
  }
}

// Krótkie etykiety pól e-maila w kilku językach — dopasowane do języka rezerwacji (data.lang)
// UWAGA: pełne tłumaczenie e-maila jest tylko dla pl/en/de (najważniejsze rynki na start).
// Rezerwacje w pozostałych językach (fr/it/es/mt/uk/ar) dostaną e-mail po angielsku (fallback).
// Chcesz dodać pełne tłumaczenie dla reszty? Dopisz kolejne klucze wg tego samego wzoru.
const EMAIL_LABELS = {
  pl: { subject: "Potwierdzenie rezerwacji transferu", greeting: "Dzień dobry", intro: "Dziękujemy za rezerwację! Oto podsumowanie:",
        name: "Imię i nazwisko", phone: "Telefon",
        route: "Trasa", datetime: "Data i godzina", passengers: "Liczba osób", vehicle: "Pojazd", price: "Cena",
        payment: "Sposób płatności", paymentValue: "Gotówką lub kartą bezpośrednio u kierowcy — brak przedpłaty online.",
        address: "Adres", flight: "Numer lotu", flightFrom: "skąd", contact: "W razie pytań napisz do nas na WhatsApp", regards: "Do zobaczenia!" },
  en: { subject: "Your transfer booking confirmation", greeting: "Hello", intro: "Thank you for your booking! Here's your summary:",
        name: "Full name", phone: "Phone",
        route: "Route", datetime: "Date & time", passengers: "Passengers", vehicle: "Vehicle", price: "Price",
        payment: "Payment method", paymentValue: "Cash or card directly to the driver — no online prepayment required.",
        address: "Address", flight: "Flight number", flightFrom: "from", contact: "If you have any questions, message us on WhatsApp", regards: "See you soon!" },
  de: { subject: "Bestätigung Ihrer Transferbuchung", greeting: "Hallo", intro: "Vielen Dank für Ihre Buchung! Hier ist Ihre Zusammenfassung:",
        name: "Name", phone: "Telefon",
        route: "Strecke", datetime: "Datum & Uhrzeit", passengers: "Personenzahl", vehicle: "Fahrzeug", price: "Preis",
        payment: "Zahlungsart", paymentValue: "Bar oder Karte direkt beim Fahrer — keine Online-Vorauszahlung.",
        address: "Adresse", flight: "Flugnummer", flightFrom: "ab", contact: "Bei Fragen schreiben Sie uns auf WhatsApp", regards: "Bis bald!" },
};

function getEmailLabels(lang) {
  return EMAIL_LABELS[lang] || EMAIL_LABELS.en;
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const cal = CalendarApp.getCalendarById(CALENDAR_ID);

    const flightOrigin = data.flightNo ? lookupFlightOrigin(data.flightNo) : null;

    const title = `Transfer: ${data.firstName || ""} ${data.lastName || ""} (${data.route || "trasa nieokreślona"})`;
    const start = data.datetime ? new Date(data.datetime) : new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000); // domyślnie 1h blok w kalendarzu

    const description = [
      `Imię i nazwisko: ${data.firstName || ""} ${data.lastName || ""}`,
      `E-mail: ${data.email || "-"}`,
      `Telefon: ${data.phone || "-"}`,
      `Numer lotu: ${data.flightNo || "-"}${flightOrigin ? ` (skąd: ${flightOrigin})` : ""}`,
      `Trasa: ${data.route || "-"}`,
      `Pojazd: ${data.vehicle || "-"}`,
      `Cena: ${data.price || "-"}`,
      `Płatność: u kierowcy (gotówka/karta)`,
      `Uwagi: ${data.notes || "-"}`,
    ].join("\n");

    cal.createEvent(title, start, end, { description: description });

    // Rezerwacja w SOR (wynik dopisany do maila [KT-REZ])
    const sorWynik = wyslijDoSOR(data, flightOrigin);

    // Powiadomienie do Ciebie — wysyłane zawsze, niezależnie od tego, czy klient podał e-mail
    sendOwnerNotification(data, title, flightOrigin, sorWynik);

    // Potwierdzenie dla klienta — tylko jeśli podał e-mail
    if (data.email) {
      sendConfirmationEmail(data, flightOrigin);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function sendOwnerNotification(data, title, flightOrigin, sorWynik) {
  const dateStr = data.datetime
    ? Utilities.formatDate(new Date(data.datetime), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm")
    : "-";

  const name = `${data.firstName || ""} ${data.lastName || ""}`.trim() || "-";
  const address = data.notes ? String(data.notes).replace(/^Adres:\s*/, "") : "";

  // Stały format: każda linia "POLE: wartość", zawsze te same pola w tej samej kolejności
  // (puste = "-"), żeby rezerwację dało się automatycznie przenieść do SOR.
  const body = [
    `ZRODLO: krakow-transfers.com`,
    `DATA: ${dateStr}`,
    `TRASA: ${data.route || "-"}`,
    `OSOBY: ${data.passengers || "-"}`,
    `POJAZD: ${data.vehicle || "-"}`,
    `CENA: ${data.price || "-"}`,
    `PLATNOSC: u kierowcy (gotówka/karta)`,
    `LOT: ${data.flightNo || "-"}${flightOrigin ? ` (skąd: ${flightOrigin})` : ""}`,
    `ADRES: ${address || "-"}`,
    `KLIENT: ${name}`,
    `TELEFON: ${data.phone || "-"}`,
    `EMAIL: ${data.email || "-"}`,
    `JEZYK: ${data.lang || "-"}`,
    ``,
    sorWynik || "SOR: nie wysłano",
    ``,
    `Odpowiedź na tego maila trafi bezpośrednio do klienta (jeśli podał e-mail).`,
  ].join("\n");

  const shortDate = data.datetime
    ? Utilities.formatDate(new Date(data.datetime), Session.getScriptTimeZone(), "dd.MM HH:mm")
    : "brak daty";

  const mail = {
    to: OWNER_EMAIL,
    subject: `${OWNER_SUBJECT_TAG} ${shortDate} ${data.route || "trasa nieokreślona"} — ${data.passengers || "?"} os. — ${name}`,
    body: body,
    name: "Kraków Transfers – rezerwacja",
  };
  if (data.email) mail.replyTo = data.email;
  wyslijZVibe({ to: mail.to, subject: mail.subject, text: mail.body, name: mail.name, replyTo: mail.replyTo });
}

function sendConfirmationEmail(data, flightOrigin) {
  const L = getEmailLabels(data.lang);
  const dateStr = data.datetime
    ? Utilities.formatDate(new Date(data.datetime), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm")
    : "-";

  const rows = [
    [L.name, `${data.firstName || ""} ${data.lastName || ""}`.trim()],
    [L.phone, data.phone || "-"],
    [L.route, data.route || "-"],
    [L.datetime, dateStr],
    [L.passengers, data.passengers || "-"],
    [L.vehicle, data.vehicle || "-"],
    [L.price, data.price || "-"],
  ];
  if (data.notes) rows.push([L.address, data.notes.replace("Adres: ", "")]);
  if (data.flightNo) {
    rows.push([L.flight, flightOrigin ? `${data.flightNo} (${L.flightFrom}: ${flightOrigin})` : data.flightNo]);
  }

  const rowsHtml = rows.map(([label, value]) =>
    `<tr><td style="padding:6px 12px 6px 0;color:#5A6472;font-size:14px;">${label}</td>` +
    `<td style="padding:6px 0;font-weight:600;font-size:14px;">${value}</td></tr>`
  ).join("");

  const htmlBody = `
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;">
      <div style="background:#0F2038;padding:20px 24px;border-radius:12px 12px 0 0;">
        <span style="color:#EEEAE1;font-size:16px;font-weight:700;">${COMPANY_NAME}</span>
      </div>
      <div style="border:1px solid #E1DCCE;border-top:none;padding:24px;border-radius:0 0 12px 12px;">
        <p>${L.greeting} ${data.firstName || ""},</p>
        <p>${L.intro}</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">${rowsHtml}</table>
        <div style="background:#FAF8F2;border-radius:8px;padding:14px 16px;margin:16px 0;">
          <strong>${L.payment}:</strong><br>${L.paymentValue}
        </div>
        <p style="color:#5A6472;font-size:13px;">${L.contact}: <strong>${COMPANY_PHONE}</strong></p>
        <p>${L.regards}<br>${COMPANY_NAME}</p>
      </div>
    </div>
  `;

  wyslijZVibe({ to: data.email, subject: `${L.subject} — ${COMPANY_NAME}`, html: htmlBody, name: COMPANY_NAME, zapisz: true });
}

function doGet(e) {
  const template = HtmlService.createTemplateFromFile("Index");
  template.events = getUpcomingEvents();
  return template.evaluate().setTitle("Rezerwacje — Katowice Pyrzowice Airport Transfers");
}

function getUpcomingEvents() {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  const now = new Date();
  const in60days = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000);
  const events = cal.getEvents(now, in60days);

  return events.map(ev => ({
    title: ev.getTitle(),
    start: Utilities.formatDate(ev.getStartTime(), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm"),
    description: ev.getDescription(),
  }));
}

