---
name: bank-and-payment-match
description: Match unreconciled bank statement lines and customer or vendor payments in Odoo to open invoices and bills. Use when the user asks about open bank lines, unmatched payments, Kontoabgleich, offene Posten or which invoice a payment belongs to.
---

# Bank and payment matching

Goal: for each open bank line or payment, find the open item it belongs to. Only clear 1:1 matches count as matched. Everything else becomes a short candidate list for a person.

The connector cannot run Odoo's reconcile action. You find and propose matches. The person reconciles in Odoo (bank reconciliation view), or you prepare fields on draft records if the user asks.

## 1. Open bank lines

```
search_records(
  model="account.bank.statement.line",
  domain=[["is_reconciled", "=", false]],
  fields=["date", "amount", "currency_id", "payment_ref", "partner_id",
          "partner_name", "account_number", "journal_id"],
  order="date asc",
  limit=200,
)
```

## 2. Open items

Customer invoices and vendor bills that are posted and not fully paid:

```
search_records(
  model="account.move",
  domain=[["state", "=", "posted"],
          ["move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]],
          ["payment_state", "in", ["not_paid", "partial"]]],
  fields=["name", "ref", "partner_id", "invoice_date", "invoice_date_due",
          "amount_total", "amount_residual", "currency_id", "payment_reference"],
  limit=200,
)
```

For payments not yet matched, use `account.payment` with `is_matched = false` or `is_reconciled = false`, depending on the Odoo version (check `get_model_schema`).

`search_records` returns 20 rows by default and at most 200. Page with `offset` if there are more.

## 3. Match rules

A match is **unambiguous** only if all of these hold:

1. The amount equals `amount_residual` exactly (same currency, to the cent).
2. The invoice number or payment reference appears in `payment_ref`, **or** the partner is identical and there is exactly one open item with that amount.
3. No other open item fits the same line.

Anything else is a **candidate**:

- same amount, several open items of the same partner,
- partial payment or overpayment,
- amount differs by a small amount (fees, Skonto, rounding),
- partner unknown, only a name or IBAN in the line,
- sum of several invoices (collective transfer).

Never treat a difference as a write-off on your own. Skonto, fees and rounding need the user's decision.

Payment provider payouts (Stripe, PayPal) are not normal customer payments. Handle them with the `stripe-fee-booking` skill.

## 4. Report

```
18 offene Bankzeilen. 11 eindeutig, 5 mit Kandidaten, 2 ohne Treffer.

Eindeutig (bitte in Odoo abgleichen):
- 03.09. +1.190,00 EUR "RE 2024-0815" -> account.move 812 (Kunde AG), Rest 1.190,00

Kandidaten:
- 05.09. +500,00 EUR "Kunde AG": account.move 820 (500,00) oder 834 (500,00)
- 06.09. +2.380,00 EUR: Summe aus 841 (1.190,00) + 842 (1.190,00)?

Ohne Treffer:
- 07.09. -89,90 EUR "Lastschrift XY": keine offene Rechnung. Fehlt eine Lieferantenrechnung?
```
