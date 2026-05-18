# COVERAGE REPORT — Chunk H: /academic-research:fetch Slash-Command
PR #140 · Iteration 1 · 2026-05-18

---

## AC1: Frontmatter (description, allowed-tools, argument-hint)

**PASS**

- `commands/fetch.md` created in PR diff (new file, 150 lines).
- YAML frontmatter block present at lines 1–10 of `commands/fetch.md`.
- `description` field: multi-line block describing all 4 input types and all 4 output stati (success, pickup_required, captcha, no_match). Non-empty, >10 chars. ✓
- `allowed-tools: Read, Write, Agent(book-fetcher)` — exact match to spec. ✓
- `argument-hint: <isbn|doi|url|titel>` — exact match to spec. ✓

Test evidence:
- `tests/test_fetch_command.py::test_command_file_exists` — asserts file exists.
- `tests/test_fetch_command.py::test_frontmatter_agent_book_fetcher` — asserts `Agent(book-fetcher)` in allowed-tools.
- `tests/test_fetch_command.py::test_frontmatter_argument_hint` — asserts hint present and contains isbn/doi/url keyword.
- `tests/test_fetch_command.py::test_frontmatter_description_nonempty` — asserts description non-empty and length >10.

---

## AC2: Input-Parsing (ISBN-10/13, DOI, URL, Freitext-Titel)

**PASS**

Implementation: `commands/fetch.md` Schritt 1 (lines ~53–67) defines the 6-priority parse rules:
1. `isbn:`-prefix → isbn
2. `http://` / `https://` → url
3. `^10.\d{4,}/` → doi
4. digits-only cleaned = `97[89]\d{10}` → isbn (ISBN-13)
5. digits-only cleaned = `\d{9}[\dX]` → isbn (ISBN-10)
6. fallback → title

The `parse_identifier()` function in `tests/test_fetch_command.py` (lines ~68–106) mirrors this logic and is exercised by 6 parser tests.

Test evidence:
- `tests/test_fetch_command.py::test_parser_isbn13` — `978-3-16-148410-0` → `('isbn', ...)`
- `tests/test_fetch_command.py::test_parser_isbn10` — `0306406152` → `('isbn', ...)`
- `tests/test_fetch_command.py::test_parser_doi` — `10.1007/...` → `('doi', ...)`
- `tests/test_fetch_command.py::test_parser_url` — `https://...` → `('url', ...)`
- `tests/test_fetch_command.py::test_parser_title` — `Advanced Machine Learning` → `('title', ...)`
- `tests/test_fetch_command.py::test_parser_isbn_prefix` — `isbn: 0-306-40615-2` → `('isbn', '0-306-40615-2')`

All 6 parse paths from spec §2 covered.

---

## AC3: book-fetcher spawn (mock acceptable pre-G-merge)

**PASS**

Implementation: `commands/fetch.md` Schritt 3 (lines ~80–103) instructs calling `Agent(book-fetcher)` with payload `<identifier_type>: <identifier_value>\noutput_path: <output_path>` and awaiting the result JSON schema.

Per task note: book-fetcher (chunk G, PR #137) is on a separate branch; mock pattern is acceptable pre-merge. The PR description explicitly states "Mockt book-fetcher-Aufruf — Real-Integration nach Merge von #137 (Chunk G)."

Test evidence: `tests/test_fetch_command.py` isolates parser and builder helpers without calling the agent — this is the correct mock pattern. No test flags missing because mock is explicitly permitted.

---

## AC4: Status `success` → literature_state.md + Vault

**PASS**

Implementation: `commands/fetch.md` "Bei success" section (lines ~107–124) specifies:
1. Read `file_path` from result.
2. Append CSL-style markdown block to `./literature_state.md` via Write-Tool.
3. Output confirmation to user.

The block includes: title, year, Typ: book, ISBN/DOI, PDF, Quelle, Hinzugefuegt (ISO-8601).

Test evidence:
- `tests/test_fetch_command.py::test_literature_state_block_structure` — asserts block contains all required fields: `## <title> (<year>)`, `**Typ:** book`, identifier, `**PDF:**`, `**Quelle:**`, `**Hinzugefuegt:**`.

---

## AC5: Status `pickup_required` → pickup_queue.json entry

**PASS**

Implementation: `commands/fetch.md` "Bei pickup_required oder no_match" section (lines ~126–147) specifies reading `~/.academic-research/pickup_queue.json`, appending JSON entry with all 6 required fields (identifier, identifier_type, bib_pickup_url, reason, ts, source), writing back via Write-Tool, and outputting user message.

Test evidence:
- `tests/test_fetch_command.py::test_pickup_entry_required_fields` — asserts all 6 required fields present in generated dict, and that identifier / identifier_type values are correct.

---

## AC6: Status `captcha` → screenshot display + user pause

**PASS**

Implementation: `commands/fetch.md` "Bei captcha" section (lines ~149–160) specifies:
1. Display screenshot path if present.
2. Inform user with "weiter" / "abbrechen" options.
3. Wait for user input.
4. "weiter" → treat as pickup_required; "abbrechen" → abort.

No dedicated unit test for captcha branching exists in the PR diff. However, the spec §7 does not list a captcha-flow unit test in the 12 test cases — the captcha path is a conversational/interactive flow in the command file itself, not a testable pure function. The implementation is fully specified in `commands/fetch.md`. This is acceptable; the spec's test list (tests 1–12) does not include a captcha unit test.

**Note:** Minor gap — no test exercises captcha branch even at a stub level. Not blocking given spec design, but noted.

---

## AC7: Status `no_match` → pickup_required treatment

**PASS**

Implementation: `commands/fetch.md` "Bei pickup_required oder no_match" section explicitly groups both statuses and handles them identically. The description frontmatter also states `no_match (kein Treffer -> ebenfalls pickup_required-Eintrag)`. This addresses OQ21 resolution.

Test evidence: `tests/test_fetch_command.py::test_pickup_entry_required_fields` covers the pickup entry structure. The no_match path is handled by the same code branch as pickup_required in the command, so the same test covers the data contract.

---

## AC8: Eval cases (3 cases: ISBN, DOI, URL) under evals/fetch/

**PASS**

- `evals/fetch/evals.json` created in PR diff (new file, 45 lines).
- 3 cases present:
  - `fc-01`: ISBN-13 `978-3-16-148410-0` → `equals:isbn` ✓
  - `fc-02`: DOI `10.1007/978-3-662-54347-6` → `equals:doi` ✓
  - `fc-03`: HTTPS-URL `https://link.springer.com/book/10.1007/978-3-662-54347-6` → `equals:url` ✓
- Each case has `id`, `input`, `expected` fields.
- `type: input_parsing` matches spec §6.

Test evidence:
- `tests/test_fetch_command.py::test_evals_file_exists` — asserts file exists.
- `tests/test_fetch_command.py::test_evals_schema` — asserts ≥3 cases, each with id/input/expected fields.

---

## Extra Checks

### Frontmatter description covers output stati

`commands/fetch.md` description field explicitly lists all 4 stati with their meaning:
- `success (PDF in Vault und literature_state.md aufgenommen)`
- `pickup_required (Fernleihe-Eintrag in ~/.academic-research/pickup_queue.json angelegt)`
- `captcha (Screenshot anzeigen, manuelle Entscheidung abwarten)`
- `no_match (kein Treffer -> ebenfalls pickup_required-Eintrag)`

AC: PASS.

### Test suite count

PR claims 15/15 fetch-tests passed. `tests/test_fetch_command.py` has exactly 15 test functions (`test_command_file_exists` through `test_evals_schema`). Consistent. ✓

### Mock pattern

`parse_identifier()` and helper functions in `tests/test_fetch_command.py` mirror the command logic for testable isolation. No LLM/Agent call made in tests. Correct pattern for pre-G-merge state. ✓

---

## Summary

| AC | Result | Evidence |
|---|---|---|
| AC1 Frontmatter | PASS | commands/fetch.md:1-10 + 4 frontmatter tests |
| AC2 Input-Parsing | PASS | commands/fetch.md:53-67 + 6 parser tests |
| AC3 book-fetcher spawn | PASS | commands/fetch.md:80-103 (mock acceptable) |
| AC4 success handler | PASS | commands/fetch.md:107-124 + test_literature_state_block_structure |
| AC5 pickup_required handler | PASS | commands/fetch.md:126-147 + test_pickup_entry_required_fields |
| AC6 captcha handler | PASS | commands/fetch.md:149-160 (no unit test, acceptable per spec design) |
| AC7 no_match handler | PASS | commands/fetch.md:126-147 (grouped with pickup_required) |
| AC8 Evals (3 cases) | PASS | evals/fetch/evals.json + test_evals_file_exists + test_evals_schema |

**Overall: PASS** — 0 critical, 0 high findings. One minor note: captcha interactive flow has no stub-level unit test, but this is consistent with the spec's test plan which omits it by design.
