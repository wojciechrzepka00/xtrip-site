// server.js
// Backend: Stripe Checkout -> (po udanej płatności) -> faktura w Comarch Betterfly -> mail do klienta
// + opcjonalny zapis rezerwacji do Kalendarza Google (Apps Script z folderu google-calendar-system/)
//
// WAŻNE — przeczytaj przed uruchomieniem:
// 1. To wymaga prawdziwego hostingu backendu (Render / Railway / Fly.io / VPS) — NIE działa
//    jako część statycznej strony na GitHub Pages/Netlify. Klucze poniżej muszą być sekretami
//    środowiskowymi (Render/Railway mają do tego wbudowaną sekcję "Environment Variables") —
//    NIGDY nie wklejaj ich do kodu ani do repozytorium.
// 2. Sekcja tworząca kontrahenta w Comarch Betterfly (getOrCreateContractor) używa nazw pól
//    opartych na typowej konwencji API Comarch — ZANIM wdrożysz na produkcję, zweryfikuj
//    dokładne nazwy pól w swoim panelu: Pomoc -> Dokumentacja API -> Kontrahenci, bo mogą się
//    różnić w Twojej wersji API.
// 3. Zanim włączysz to na produkcji z prawdziwymi pieniędzmi klientów: potwierdź z księgowym,
//    czy przy przewozie osób opłacanym online wymagany jest też paragon fiskalny (patrz
//    rozmowa / README.md w tym folderze) — jeśli tak, ten skrypt trzeba będzie rozszerzyć
//    o integrację z kasą fiskalną, zanim zacznie realnie obsługiwać płatności klientów.

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const Stripe = require('stripe');

const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
const app = express();

app.use(cors());

// --- 1) Tworzenie sesji płatności Stripe ---
// Frontend (formularz na stronie) wywołuje ten endpoint z danymi rezerwacji.
app.post('/create-checkout-session', express.json(), async (req, res) => {
  try {
    const {
      firstName, lastName, email, phone,
      routeLabel, city, passengers, datetime, address, flightNo,
      priceZl, // cena w PLN wyliczona po stronie frontendu (patrz uwaga niżej)
    } = req.body;

    // UWAGA BEZPIECZEŃSTWA: w wersji produkcyjnej NIE ufaj cenie przysłanej z przeglądarki
    // (użytkownik mógłby ją zmienić w kodzie strony). Najlepiej przenieść tu tę samą logikę
    // cenową co w index.html (obiekt PRICING) i przeliczyć cenę od zera na serwerze,
    // a przysłaną wartość jedynie traktować jako podgląd/weryfikację zgodności.
    if (!priceZl || priceZl <= 0) {
      return res.status(400).json({ error: 'Nieprawidłowa cena' });
    }

    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      payment_method_types: ['card', 'blik', 'p24'],
      customer_email: email,
      line_items: [
        {
          price_data: {
            currency: 'pln',
            product_data: {
              name: `Transfer: ${routeLabel || 'Katowice Pyrzowice Airport Transfers'}`,
              description: `${passengers || ''} os. · ${datetime || ''}`,
            },
            unit_amount: Math.round(priceZl * 100), // Stripe liczy w groszach
          },
          quantity: 1,
        },
      ],
      success_url: process.env.SUCCESS_URL,
      cancel_url: process.env.CANCEL_URL,
      metadata: {
        firstName: firstName || '',
        lastName: lastName || '',
        phone: phone || '',
        email: email || '',
        routeLabel: routeLabel || '',
        city: city || '',
        passengers: String(passengers || ''),
        datetime: datetime || '',
        address: address || '',
        flightNo: flightNo || '',
        priceZl: String(priceZl),
      },
    });

    res.json({ url: session.url });
  } catch (err) {
    console.error('Błąd tworzenia sesji Stripe:', err.message);
    res.status(500).json({ error: 'Nie udało się utworzyć sesji płatności' });
  }
});

// --- 2) Webhook Stripe — wywoływany automatycznie po zdarzeniach płatności ---
// WAŻNE: ten endpoint MUSI dostawać "surowe" body (nie JSON.parse), stąd express.raw() poniżej.
app.post(
  '/webhook',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    let event;
    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        req.headers['stripe-signature'],
        process.env.STRIPE_WEBHOOK_SECRET
      );
    } catch (err) {
      console.error('Nieprawidłowy podpis webhooka Stripe:', err.message);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    if (event.type === 'checkout.session.completed') {
      const session = event.data.object;
      const meta = session.metadata || {};

      try {
        await issueComarchInvoice(meta);
        console.log('Faktura Comarch Betterfly utworzona dla:', meta.email);
      } catch (err) {
        console.error('BŁĄD wystawiania faktury w Comarch Betterfly:', err.response?.data || err.message);
        // Tu warto dodać alert (np. mail do Ciebie), żeby wiedzieć, że trzeba wystawić fakturę ręcznie.
      }

      if (process.env.CALENDAR_WEBHOOK_URL) {
        try {
          await axios.post(process.env.CALENDAR_WEBHOOK_URL, {
            firstName: meta.firstName,
            lastName: meta.lastName,
            phone: meta.phone,
            flightNo: meta.flightNo,
            route: meta.routeLabel,
            vehicle: meta.city,
            datetime: meta.datetime,
            notes: `Adres: ${meta.address || '-'} | Zapłacono online: ${meta.priceZl} zł`,
          });
        } catch (err) {
          console.error('Błąd zapisu do Kalendarza Google:', err.message);
        }
      }
    }

    res.json({ received: true });
  }
);

// --- 3) Integracja z Comarch Betterfly: kontrahent + faktura ---

async function comarchRequest(method, path, data) {
  return axios({
    method,
    url: `${process.env.COMARCH_API_BASE}${path}`,
    headers: {
      Authorization: `Bearer ${process.env.COMARCH_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    data,
  });
}

// Znajduje kontrahenta po e-mailu lub tworzy nowego.
// UWAGA: nazwy pól (Name, Email, itd.) zweryfikuj w dokumentacji API -> Kontrahenci
// w swoim panelu Betterfly przed użyciem produkcyjnym.
async function getOrCreateContractor({ firstName, lastName, email }) {
  try {
    const search = await comarchRequest(
      'GET',
      `/contractors?$filter=Email eq '${email}'`
    );
    if (search.data && search.data.length > 0) {
      return search.data[0].Id;
    }
  } catch (err) {
    console.warn('Wyszukiwanie kontrahenta nie powiodło się, tworzę nowego:', err.message);
  }

  const created = await comarchRequest('POST', '/contractors', {
    Name: `${firstName} ${lastName}`.trim() || 'Klient indywidualny',
    Email: email,
    IsPerson: true,
  });
  return created.data.Id;
}

async function issueComarchInvoice(meta) {
  const contractorId = await getOrCreateContractor({
    firstName: meta.firstName,
    lastName: meta.lastName,
    email: meta.email,
  });

  const invoice = await comarchRequest('POST', '/invoices', {
    PurchasingPartyId: contractorId,
    PaymentTypeId: Number(process.env.COMARCH_PAYMENT_TYPE_ID),
    PaymentStatus: 1, // 1 = zapłacona w całości
    Items: [
      {
        ProductId: Number(process.env.COMARCH_PRODUCT_ID),
        Quantity: 1,
        ProductCurrencyPrice: Number(meta.priceZl),
      },
    ],
    Description: `${meta.routeLabel} — ${meta.passengers} os. — ${meta.datetime}`,
  });

  const invoiceId = invoice.data.Id;

  // Zatwierdzenie faktury (dopiero zatwierdzona faktura trafia realnie do obiegu / KSeF / e-mail klienta)
  await comarchRequest('PUT', '/invoices/confirm', { Id: invoiceId });

  return invoiceId;
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Serwer płatności działa na porcie ${PORT}`));
