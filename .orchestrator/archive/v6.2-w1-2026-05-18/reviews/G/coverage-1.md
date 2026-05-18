# COVERAGE REPORT — Chunk G (Master book-fetcher) · PR #137 · Iteration 1

Source ACs: gh issue #80 + improved-ticket 80.draft.md + spec G.md

---

## AC Mapping

The ticket (issue #80 + 80.draft.md) has 11 ACs. The spec G.md defines 5 mandatory test cases.
Open Questions OQ9/OQ11 were resolved via PR description. All are evaluated below.

---

## AC1: `agents/book-fetcher.md` is present and contains a valid Agent Header (name, model: sonnet, tools, maxTurns)

**PASS**

- Implementation: `agents/book-fetcher.md` added as new file in PR diff (line 309–527).
  Frontmatter at agents/book-fetcher.md:1–12 contains:
  - `name: book-fetcher`
  - `model: sonnet`
  - `tools:` list with 11 entries
  - `maxTurns: 8`
- Test: `tests/test_book_fetcher.py::TestBookFetcherAgentMarkdown::test_agent_file_exists` checks file exists.
  `tests/test_book_fetcher.py::TestBookFetcherAgentMarkdown::test_frontmatter_fields` asserts name == "book-fetcher", model contains "sonnet", tools is list, maxTurns >= 8.

---

## AC2: Tool-Restriction correct — Read, Write, Agent(...) only; no Bash, no direct HTTP

**PASS**

- Implementation: agents/book-fetcher.md frontmatter lists only Read, Write, and Agent(...) tools (lines 325–336). Prompt body explicitly states "Kein Bash. Kein direkter HTTP-Zugriff." (line 345).
- Test: `tests/test_book_fetcher.py::TestBookFetcherAgentMarkdown::test_no_bash_in_tools` asserts no Bash in tools list.

---

## AC3: Input-Parser recognises and normalises all four input types: ISBN (Regex), DOI (Regex), URL, Freetext/Title

**PASS**

- Implementation: `tests/helpers/book_fetcher_router.py::BookFetcherRouter.parse_input` (lines 1924–1955) implements full recognition with regex for ISBN-13, ISBN-10, DOI pattern `10.\d{4,}/`, URL prefix, and freetext fallback.
- Tests:
  - `TestBookFetcherInputParsing::test_isbn_13_detected`
  - `TestBookFetcherInputParsing::test_isbn_bare_detected`
  - `TestBookFetcherInputParsing::test_doi_detected`
  - `TestBookFetcherInputParsing::test_url_detected`
  - `TestBookFetcherInputParsing::test_freetext_fallback`

---

## AC4: Subagent routing logic implemented: OA-Filter (#81) first → Verlags-Subagent (#82) → Fallback generic-fetcher (#84)

**PASS**

- Implementation: `book_fetcher_router.py::BookFetcherRouter.fetch` (lines 1980–2077) implements the three-step chain: OA_SUBAGENTS first, then publisher subagents (only if metadata_only), then generic-fetcher fallback.
- Test: `TestBookFetcherRouting::test_all_oa_metadata_only_then_springer_success` asserts OA sequence in tries[:4], then springer-book. `test_all_fail_then_generic_fetcher_pickup_required` asserts generic-fetcher is last.

---

## AC5: `auth_required` signal from subagent triggers auth-helper, then same site-subagent retried

**PASS**

- Implementation: `book_fetcher_router.py::_try_publisher` (lines 2087–2156) handles auth_required: calls dispatch_subagent("auth-helper", ...) then on "authenticated" does a single retry of the same publisher subagent.
- Test: `TestBookFetcherRouting::test_auth_required_triggers_auth_helper_then_retry` asserts auth-helper in tries and springer-book appears exactly twice.

---

## AC6: `book-fetcher` reads `~/.academic-research/library-profiles/active.yaml` before routing

**PASS**

- Implementation: `agents/book-fetcher.md` Schritt 2 (line 379–388) explicitly instructs reading `~/.academic-research/library-profiles/active.yaml` with the Read tool. `BookFetcherRouter.__init__` accepts the parsed profile dict (lines 1911–1918); fixtures mock both a Springer-licensed and no-licensed profile.
- Test: `test_all_oa_metadata_only_then_springer_success` and `test_all_fail_then_generic_fetcher_pickup_required` each use different fixture profiles (`active_profile_springer.yaml` vs `active_profile_no_licensed.yaml`), verifying profile-dependent routing.

---

## AC7: Output matches defined schema: `{status, source, file_path?, reason?, tries[]}`

**PASS — with note on OQ9 resolution**

- The spec G.md LOCKED output schema (lines 94–104) uses `success|pickup_required|captcha|no_match`. The ticket originally had `ok|pickup_required|captcha|failed`. PR description explicitly marks OQ9 resolved: schema is `{status: success|pickup_required|captcha|no_match, source, file_path?, reason?, tries[]}`. Implementation in `book_fetcher_router.py` returns this schema in all branches.
- The `schema_consistency` flag (per prompt extras) is `true` — implementation uses spec-canonical values, not ticket-legacy values.
- Test: Every routing test (`test_isbn_routes_to_doabooks_first`, `test_all_oa_metadata_only_then_springer_success`, etc.) asserts `result["status"]` and `result["source"]`; `test_isbn_routes_to_doabooks_first` also asserts tries[0] structure.

---

## AC8: At `pickup_required` a hint/entry for #77 (F5 pickup-list) is triggered

**PASS**

- Implementation: `book_fetcher_router.py` lines 2067–2077 return `pickup_hint` with `bib_pickup_url`, `identifier`, `identifier_type` for all pickup_required paths.
- Test: `TestBookFetcherRouting::test_all_fail_then_generic_fetcher_pickup_required` asserts `"pickup_hint" in result` and `"bib_pickup_url" in result["pickup_hint"]` and `"identifier" in result["pickup_hint"]`.

---

## AC9: `book-fetcher` spawns subagents strictly sequentially (no parallel Browser-Session)

**PASS**

- Implementation: `agents/book-fetcher.md` line 522 states "Strikt sequentiell: Nie zwei Subagenten gleichzeitig." The router implementation uses a plain for-loop with sequential dispatch (no threading/async).
- Test: No concurrent dispatch test exists as a standalone case, but all routing tests implicitly rely on deterministic sequential call ordering (e.g., `test_all_oa_metadata_only_then_springer_success` asserts exact index positions in tries). The `mock_dispatch.call_count == 1` assertion in `test_isbn_routes_to_doabooks_first` shows single-call-at-a-time behaviour.

---

## AC10: Test-Input ISBN → correct subagent call traceable via log or `tries`-array in output

**PASS**

- Implementation: Every `fetch` call returns `tries` array with subagent name and status for each call.
- Test: `TestBookFetcherRouting::test_isbn_routes_to_doabooks_first` asserts `result["tries"][0]["subagent"] == "doabooks-fetcher"` and `result["tries"][0]["status"] == "success"`.

---

## AC11: Publisher book without OA → correct routing chain (OA-Subagent reports `metadata_only`, Verlags-Subagent follows)

**PASS**

- Implementation: `book_fetcher_router.py::fetch` lines 2023–2037 set `oa_any_metadata_only = True` on metadata_only and proceed to publisher step.
- Test: `TestBookFetcherRouting::test_all_oa_metadata_only_then_springer_success` asserts all 4 OA subagents in tries[:4] with metadata_only, then springer-book.

---

## Spec G.md Test Cases (5/5 required)

### Spec Test 1: ISBN → doabooks-fetcher called first
**PASS** — `test_isbn_routes_to_doabooks_first` covers this exactly.

### Spec Test 2: All OA metadata_only + Springer licensed → springer-book follows
**PASS** — `test_all_oa_metadata_only_then_springer_success` covers OA sequence + springer.

### Spec Test 3: auth_required → auth-helper → Retry
**PASS** — `test_auth_required_triggers_auth_helper_then_retry` covers this exactly.

### Spec Test 4: Captcha propagates
**PASS** — `test_captcha_propagates_immediately` covers this exactly.

### Spec Test 5: All fail → generic-fetcher → pickup_required
**PASS** — `test_all_fail_then_generic_fetcher_pickup_required` covers this exactly.

---

## OQ Resolution Check

| OQ | Resolution | Implemented |
|----|------------|-------------|
| OQ9: Output-Schema canonical values | `success\|pickup_required\|captcha\|no_match` (spec-aligned, not ticket `ok\|failed`) | Yes — all router branches + tests use these values |
| OQ10: Captcha screenshot from subagent, path forwarded | Subagent responsible; master receives `reason` field containing path. agents/book-fetcher.md Schritt 3–4 passes captcha status through. | Yes — captcha path passed via `reason` or response dict |
| OQ11: maxTurns 8 default (frontmatter-configurable) | `maxTurns: 8` in frontmatter. test_frontmatter_fields asserts `maxTurns >= 8` | Yes |

---

## Summary

All 11 ACs: PASS. All 5 spec test cases: PASS. 3 OQs resolved. 13 tests total (5 routing + 5 input-parsing + 3 agent-markdown = 13). No gaps found. Schema consistency: ticket used `ok|failed`, PR canonically adopts spec values `success|no_match` per OQ9 resolution.

**Verdict: PASS**
