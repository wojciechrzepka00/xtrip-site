/**
 * KATOWICE PYRZOWICE AIRPORT TRANSFERS — system rezerwacji
 * -----------------------------------------------------------
 * Ten plik wklejasz do Google Apps Script (script.google.com).
 * Działa na TWOIM koncie Google — to ono jest "loginem" do systemu.
 *
 * Co robi:
 * 1) doPost(e)  — odbiera zgłoszenie z formularza na stronie, tworzy
 *                 wydarzenie w Twoim Kalendarzu Google I WYSYŁA klientowi
 *                 e-mail z potwierdzeniem rezerwacji (z Twojego konta Gmail).
 * 2) doGet(e)   — wyświetla panel (Index.html) z listą najbliższych
 *                 rezerwacji i przyciskiem "Kopiuj dane dla kierowcy".
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
 * UWAGA o mailach: MailApp.sendEmail wysyła z Twojego konta Gmail/Google
 * Workspace i liczy się do dziennego limitu (100 maili/dzień na zwykłym
 * koncie Gmail, więcej na Google Workspace) — dla startu w zupełności
 * wystarczy, ale warto o tym pamiętać przy większej skali.
 */

const CALENDAR_ID = "primary"; // Twój główny kalendarz Google
const COMPANY_NAME = "Katowice Pyrzowice Airport Transfers";
const COMPANY_PHONE = "+48 728 814 659";

// Krótkie etykiety pól e-maila w kilku językach — dopasowane do języka rezerwacji (data.lang)
// UWAGA: pełne tłumaczenie e-maila jest tylko dla pl/en/de (najważniejsze rynki na start).
// Rezerwacje w pozostałych językach (fr/it/es/mt/uk/ar) dostaną e-mail po angielsku (fallback).
// Chcesz dodać pełne tłumaczenie dla reszty? Dopisz kolejne klucze wg tego samego wzoru.
const EMAIL_LABELS = {
  pl: { subject: "Potwierdzenie rezerwacji transferu", greeting: "Dzień dobry", intro: "Dziękujemy za rezerwację! Oto podsumowanie:",
        route: "Trasa", datetime: "Data i godzina", passengers: "Liczba osób", vehicle: "Pojazd", price: "Cena",
        payment: "Sposób płatności", paymentValue: "Gotówką lub kartą bezpośrednio u kierowcy — brak przedpłaty online.",
        address: "Adres", flight: "Numer lotu", contact: "W razie pytań napisz do nas na WhatsApp", regards: "Do zobaczenia!" },
  en: { subject: "Your transfer booking confirmation", greeting: "Hello", intro: "Thank you for your booking! Here's your summary:",
        route: "Route", datetime: "Date & time", passengers: "Passengers", vehicle: "Vehicle", price: "Price",
        payment: "Payment method", paymentValue: "Cash or card directly to the driver — no online prepayment required.",
        address: "Address", flight: "Flight number", contact: "If you have any questions, message us on WhatsApp", regards: "See you soon!" },
  de: { subject: "Bestätigung Ihrer Transferbuchung", greeting: "Hallo", intro: "Vielen Dank für Ihre Buchung! Hier ist Ihre Zusammenfassung:",
        route: "Strecke", datetime: "Datum & Uhrzeit", passengers: "Personenzahl", vehicle: "Fahrzeug", price: "Preis",
        payment: "Zahlungsart", paymentValue: "Bar oder Karte direkt beim Fahrer — keine Online-Vorauszahlung.",
        address: "Adresse", flight: "Flugnummer", contact: "Bei Fragen schreiben Sie uns auf WhatsApp", regards: "Bis bald!" },
};

function getEmailLabels(lang) {
  return EMAIL_LABELS[lang] || EMAIL_LABELS.en;
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const cal = CalendarApp.getCalendarById(CALENDAR_ID);

    const title = `Transfer: ${data.firstName || ""} ${data.lastName || ""} (${data.route || "trasa nieokreślona"})`;
    const start = data.datetime ? new Date(data.datetime) : new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000); // domyślnie 1h blok w kalendarzu

    const description = [
      `Imię i nazwisko: ${data.firstName || ""} ${data.lastName || ""}`,
      `E-mail: ${data.email || "-"}`,
      `Telefon: ${data.phone || "-"}`,
      `Numer lotu: ${data.flightNo || "-"}`,
      `Trasa: ${data.route || "-"}`,
      `Pojazd: ${data.vehicle || "-"}`,
      `Cena: ${data.price || "-"}`,
      `Płatność: u kierowcy (gotówka/karta)`,
      `Uwagi: ${data.notes || "-"}`,
    ].join("\n");

    cal.createEvent(title, start, end, { description: description });

    if (data.email) {
      sendConfirmationEmail(data);
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

function sendConfirmationEmail(data) {
  const L = getEmailLabels(data.lang);
  const dateStr = data.datetime
    ? Utilities.formatDate(new Date(data.datetime), Session.getScriptTimeZone(), "dd.MM.yyyy HH:mm")
    : "-";

  const rows = [
    [L.route, data.route || "-"],
    [L.datetime, dateStr],
    [L.passengers, data.passengers || "-"],
    [L.vehicle, data.vehicle || "-"],
    [L.price, data.price || "-"],
  ];
  if (data.notes) rows.push([L.address, data.notes.replace("Adres: ", "")]);
  if (data.flightNo) rows.push([L.flight, data.flightNo]);

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

  MailApp.sendEmail({
    to: data.email,
    subject: `${L.subject} — ${COMPANY_NAME}`,
    htmlBody: htmlBody,
  });
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
