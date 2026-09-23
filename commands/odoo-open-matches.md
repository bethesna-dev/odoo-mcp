---
description: List unreconciled bank lines and unmatched payments in Odoo with match candidates
---

List open bank statement lines and unmatched payments that need review, using the `odoo` MCP tools and the `bank-and-payment-match` skill.

1. Search `account.bank.statement.line` with `is_reconciled = false`, oldest first, limit 200.
2. Search posted `account.move` invoices and bills with `payment_state in (not_paid, partial)` as open items.
3. Search `account.payment` records that are not yet matched (field name depends on the Odoo version, check the schema).
4. Sort every line into:
   - **eindeutig**: exact amount, reference or single partner match, no other candidate
   - **Kandidaten**: several possible items, partial payments, small differences, collective transfers
   - **ohne Treffer**: nothing fits
5. Lines from Stripe or other payment providers go into their own section and follow the `stripe-fee-booking` skill. Never match a net payout directly to one invoice.
6. This command is read-only. Do not reconcile, write off or change records. Reconciliation happens in Odoo.

Report numbers first, then the three lists with `date | amount | reference | proposed account.move id(s)`.

Follow the `odoo-accounting-safety` rule. Extra filter from the user (journal, date range, partner): $ARGUMENTS
