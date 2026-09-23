---
name: stripe-fee-booking
description: Book Stripe payouts, charges and fees correctly in Odoo as gross revenue, fee expense and bank transfer. Use when a bank line from Stripe appears, when the user mentions Stripe payouts, Stripe Gebühren, or when a payout amount does not match any invoice.
---

# Stripe fee booking

Stripe pays out **net**: gross charges minus fees minus refunds and disputes. The bank line therefore never matches a single invoice. Booking the payout as revenue hides the fees and understates revenue. Do not do that.

## The correct picture

For one payout:

```
gross charges (paid invoices)      1.000,00
- Stripe fees                        -29,50
- refunds / disputes                   0,00
= payout to bank                     970,50
```

In Odoo this means:

1. **Customer invoices** are settled at their full (gross) amount, usually through a Stripe clearing / transfer account or a Stripe journal.
2. **Fees** are booked as expense on the fee account (e.g. "Nebenkosten des Geldverkehrs"; SKR03 4970 or SKR04 6855, check the company's chart of accounts).
3. **The payout** moves the net amount from the Stripe clearing account to the bank account.

After the payout, the Stripe clearing account for that payout should be 0.

## Steps

1. Find the payout bank line: `account.bank.statement.line` with `payment_ref` containing "Stripe" (or the Stripe payout id `po_...`), `is_reconciled = false`.
2. Get the payout breakdown from the user or from a Stripe report (payout reconciliation export). You do not have Stripe access through this connector. **Do not estimate fees.**
3. Check that `gross - fees - refunds = payout` to the cent. If not, stop and report the difference.
4. Find the paid customer invoices (`account.move`, `out_invoice`, open or partially paid) that belong to the charges in this payout.
5. Check how the company already books Stripe (look at earlier reconciled Stripe lines and their counterpart accounts). Follow that pattern. If there is none, propose a setup and ask.
6. With `ODOO_ALLOW_WRITES=1`, prepare only **draft** entries (e.g. a draft `account.move` for the fees). A person posts and reconciles.

## Tax on fees

Stripe invoices its fees from an EU entity. Whether the fees carry VAT, are reverse charge or are exempt depends on the company and country. Do not guess. Use the tax the company already uses for Stripe fees, or ask the user to confirm with their Steuerberatung.

## Never

- Book the net payout as revenue.
- Put fees into a revenue account or net them against revenue.
- Invent a fee amount from a percentage.
- Close a difference with a write-off without Freigabe.

## Report

```
Stripe Auszahlung 12.09.: 970,50 EUR
Brutto 1.000,00 (4 Rechnungen: 901, 902, 905, 907), Gebühren 29,50, Erstattungen 0,00.
Summe passt. Gebühren-Entwurf angelegt: account.move 1302 (Entwurf).
Offen: Buchen und Abgleich in Odoo.
```
