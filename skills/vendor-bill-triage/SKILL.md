---
name: vendor-bill-triage
description: Triage incomplete vendor bills (Lieferantenrechnungen) in Odoo. Use when the user asks to check, complete or clean up draft vendor bills, or when account.move records with move_type in_invoice / in_refund are missing partner, accounts, taxes, analytic distribution, dates or the PDF.
---

# Vendor bill triage

Goal: every draft vendor bill is either complete and ready for a person to post, or clearly flagged with what is missing. You prepare, a person posts.

## 1. Find the drafts

```
search_records(
  model="account.move",
  domain=[["move_type", "in", ["in_invoice", "in_refund"]], ["state", "=", "draft"]],
  fields=["name", "ref", "partner_id", "invoice_date", "date", "invoice_date_due",
          "amount_untaxed", "amount_tax", "amount_total", "currency_id",
          "message_main_attachment_id", "journal_id"],
  order="invoice_date asc, id asc",
  limit=200,
)
```

Field names differ slightly between Odoo versions. If a field is rejected, check `get_model_schema("account.move")` and adapt.

## 2. Check each bill

For every draft, check these points and note the result:

| Check | How | Problem if |
|---|---|---|
| PDF attached | `message_main_attachment_id`, or `ir.attachment` with `res_model = account.move`, `res_id = <id>` | No document. Do not complete a bill without a source document. |
| Partner | `partner_id` set, and matches vendor name / VAT id on the PDF | Empty, or a different company than on the PDF |
| Invoice number | `ref` set, and not already used by another bill of the same partner | Empty or duplicate (possible double booking) |
| Dates | `invoice_date` set; `date` in an open period; due date plausible | Empty, in the future, or in a locked period |
| Lines | `account.move.line` with `move_id = <id>` and `display_type = product` | No lines, or lines on a suspense / default account |
| Accounts | Line `account_id` fits the cost type and matches earlier bills of the same partner | Different from history without a reason |
| Taxes | Line `tax_ids` match the rate on the PDF | Missing, different rate, or reverse charge / foreign vendor |
| Analytic | `analytic_distribution` set where the company uses analytics | Empty while earlier bills of this partner had it |
| Amounts | `amount_untaxed`, `amount_tax`, `amount_total` match the PDF to the cent | Any difference |

Use the partner's last 3 to 5 posted bills as reference for account, tax and analytic. Take values from there only when they are consistent.

## 3. Prepare the draft

Only with `ODOO_ALLOW_WRITES=1`, and only on `state = draft`:

- Fill fields that are unambiguous from the PDF or from consistent history.
- Change one bill at a time. Read it back with `get_record` after the update.
- Never change a bill that is posted or cancelled.

Stop and ask (Freigabe) instead of writing when:

- the tax treatment is not clear,
- the amount is unusual for this vendor,
- the PDF and Odoo disagree,
- several partners or accounts would fit.

## 4. Report

Start with numbers, then details:

```
12 Entwürfe geprüft. 7 vollständig, 3 ergänzt, 2 brauchen Freigabe.

Ergänzt:
- account.move 1234 (Vendor GmbH, RE-2024-118): Steuer 19 % gesetzt (vorher leer), Analytik "Projekt A" (vorher leer)

Freigabe nötig:
- account.move 1240 (Foreign Ltd): Reverse Charge oder 19 %? PDF zeigt keine USt.
- account.move 1251: Betrag 4.980,00 EUR, sonst ca. 400 EUR/Monat.
```

Posting stays with the user in Odoo.
