# Płatności online — Stripe + Comarch Betterfly

Backend, który: przyjmuje płatność online (Stripe), a po jej potwierdzeniu automatycznie
wystawia i wysyła fakturę w Comarch Betterfly oraz (opcjonalnie) zapisuje rezerwację
w Twoim Kalendarzu Google.

## Zanim zaczniesz — pytanie do księgowego

Usługi przewozu osób są **wyłączone** z popularnego zwolnienia z kasy fiskalnej dla
płatności online (§4 ust. 1 pkt 1 rozporządzenia MF o zwolnieniach z kas rejestrujących) —
w przeciwieństwie do większości sklepów internetowych. Zanim włączysz to na produkcji
z prawdziwymi płatnościami klientów, zapytaj księgowego:

> "Czy przy transferach lotniskowych opłacanych online kartą/BLIK muszę ewidencjonować
> sprzedaż na kasie fiskalnej (paragon), czy w moim przypadku wystarczy faktura?"

Jeśli odpowiedź brzmi "tak, potrzebujesz kasy" — to nie przekreśla tego kodu, tylko
oznacza, że trzeba dopisać dodatkowy krok: integrację z kasą fiskalną online (są
dostawcy oferujący to jako usługę/API, część da się połączyć z Comarch Betterfly przez
moduł POS). Daj mi znać, jak dostaniesz odpowiedź, dopiszę tę część.

## Co zawiera ten folder

- `server.js` — właściwy backend (Express)
- `package.json` — zależności
- `.env.example` — lista sekretów do skonfigurowania (skopiuj do `.env` i uzupełnij)

## Krok 1 — dane z Twojego konta Comarch Betterfly

W panelu Betterfly znajdź i zapisz:
1. **Token API** — Ustawienia → API → wygeneruj token
2. **ID produktu/usługi** — dodaj w katalogu produkt np. "Transfer lotniskowy", zapisz jego ID
3. **ID formy płatności "Płatność online"** — Ustawienia → Formy płatności

Zanim uruchomisz to na produkcji, **zweryfikuj w dokumentacji API Betterfly** (Pomoc →
Dokumentacja API → Kontrahenci), czy pola w funkcji `getOrCreateContractor` w `server.js`
(`Name`, `Email`, `IsPerson`) odpowiadają dokładnie temu, czego oczekuje Twoja wersja API —
korzystałem z ogólnie dostępnej dokumentacji faktur, ale dokumentacja endpointu
"Kontrahenci" może mieć nieco inne nazwy pól.

## Krok 2 — dane z konta Stripe

1. Dashboard Stripe → Developers → API keys → skopiuj **Secret key**
2. Włącz metody płatności BLIK i Przelewy24 dla polskich klientów (Stripe → Settings → Payment methods)
3. Webhook dodasz dopiero PO wdrożeniu (patrz Krok 4) — wtedy Stripe poda Ci "Signing secret"

## Krok 3 — wdrożenie (Render.com — najprostsze, darmowy plan wystarczy na start)

1. Załóż konto na render.com, połącz ze swoim repozytorium (ten folder jako osobne repo lub subfolder)
2. New → Web Service → wskaż ten folder
3. Build command: `npm install`
4. Start command: `npm start`
5. W sekcji Environment dodaj wszystkie zmienne z `.env.example` (bez samego `.env.example` —
   wartości wpisujesz ręcznie w panelu Render, nigdy w kodzie)
6. Deploy — Render poda Ci publiczny adres, np. `https://xtrip-payments.onrender.com`

## Krok 4 — podłączenie webhooka Stripe

1. Stripe Dashboard → Developers → Webhooks → Add endpoint
2. URL: `https://xtrip-payments.onrender.com/webhook`
3. Zdarzenie do nasłuchiwania: `checkout.session.completed`
4. Skopiuj wygenerowany "Signing secret" → wklej jako `STRIPE_WEBHOOK_SECRET` w Render → redeploy

## Krok 5 — podłączenie do strony

Gdy backend już działa i przetestujesz go (Stripe ma tryb testowy z kartami próbnymi —
nie trzeba ryzykować prawdziwych pieniędzy), daj mi znać. Dopiszę na stronie przycisk
"Zapłać online", który wywoła `/create-checkout-session` i przekieruje klienta na
stronę płatności Stripe.

Celowo NIE wpiąłem jeszcze tego przycisku do `index.html` — wolałem poczekać, aż
potwierdzisz kwestię kasy fiskalnej i przetestujesz backend w trybie testowym.
