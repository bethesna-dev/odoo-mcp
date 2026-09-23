---
description: List draft vendor bills in Odoo and triage what is missing
---

List and triage draft vendor bills (Lieferantenrechnungen im Entwurf) using the `odoo` MCP tools and the `vendor-bill-triage` skill.

1. Search `account.move` with `move_type in (in_invoice, in_refund)` and `state = draft`, oldest first, limit 200.
2. For each bill check: PDF attached, partner, vendor reference (and duplicates), invoice date and accounting date, lines with account, taxes and analytic distribution, totals.
3. Do **not** write anything unless the user explicitly asks to complete bills and `ODOO_ALLOW_WRITES=1` is set. Even then, only fill values that are unambiguous, and never touch posted bills.
4. Report numbers first:
   - total drafts, complete, incomplete, needs Freigabe
   - a table: `account.move id | partner | ref | total | missing / problem`
   - a short list of questions the user has to decide

Follow the `odoo-accounting-safety` rule. If the user passed extra text (e.g. a partner name or a month), use it to narrow the domain: $ARGUMENTS
