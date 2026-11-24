# Dataset Preparation Instructions

> **Audience:** the upper part is for the team (process and quality rules).
> The text under the `## Generator Prompt` heading is given as-is to the model
> (Claude etc.) that generates the question-answer pairs.

## General principles

1. **The site content is the single source of truth.** Expected answers rely
   only on the public text of kerimbalci.com; the model's general knowledge or
   the output of a summarization tool does not count as a source.
2. **Every record has evidence.** The `evidence` field is a verbatim quote from
   the source page and is verified automatically by searching the page text.
   A record that cannot be verified does not enter the dataset.
3. **Source diversity.** Questions are spread over the whole site; at most 3
   questions per page. The biography page must not dominate the dataset.
4. **Paywall.** For paid articles only the public part is used.
5. **Language.** Questions, expected answers and evidence stay in Turkish: the
   chatbot answers a Turkish site in Turkish.
6. Schema and file layout: `dataset/factuality/README.md` and
   `dataset/hallucination/README.md`.
7. Evidence verification: `uv run python -m kerimbalci_com.dataset_builder verify <factuality|hallucination>`
   searches every record's `evidence` quote in the source page text.

## Categories and target ratios (factuality)

| Category | Ratio | What it tests |
|---|---|---|
| `direct_fact` | ~55% | A single fact stated clearly on the site |
| `false_premise` | ~25% | Correcting a false assumption (`false_claim` required) |
| `time_sensitive` | ~12% | Information that may change (`valid_as_of` required) |
| `unanswerable` | ~8% | Not inventing information that is not on the site |

The hallucination categories are described in `dataset/hallucination/README.md`.

## Process

Code: `src/kerimbalci_com/dataset_builder/` (settings: `SITE_URL`, `SITE_WORKDIR`).

1. **Crawl and convert to text:**
   `uv run python -m kerimbalci_com.dataset_builder crawl`
   `SITE_URL/sitemap.xml` → child sitemaps → all pages. script/style/nav/
   header/footer/form are removed from the HTML; the first line of every file
   is the metadata (og:title, article:published_time, article:tag) as JSON.
   Output: `SITE_WORKDIR/text/<stem>.txt` + `SITE_WORKDIR/manifest.json` (stem → URL).
2. **Group:** `uv run python -m kerimbalci_com.dataset_builder split --groups 4`
   Splits the texts into groups balanced by word count. Groups can be
   generated in parallel.
3. **Generate:** for each group, give the model the Generator Prompt below
   together with the group's file list and the category targets; save the
   outputs into one folder (e.g. `.cache/generated/A.json`, `B.json` …).
4. **Verify and merge:**
   `uv run python -m kerimbalci_com.dataset_builder merge .cache/generated`
   Every `evidence` is searched in the source text after Unicode NFC and
   whitespace normalization; records that are not found are rejected and
   logged. Passing records get an `id` (`fact-001`, `premise-001`,
   `unans-001`, `time-001`) and a `source_url` from the manifest. Hand-written
   records without a source (`source_url: null`) in the existing dataset are
   kept. Finally the schema is validated with `load_factuality()`.
5. **Manual fixes:** fix records found in review in the source JSON under
   `.cache/generated` and run `merge` again, so the fixes are not lost in the
   next generation.
6. **Review (human):** apply the checklist below.
7. **Test:** `uv run pytest tests/unit/test_datasets.py` (schema), then a small
   eval trial: `uv run pytest -m eval tests/factuality/ -k <category>`.

### Known pitfalls

- Pages may contain non-breaking spaces (`\xa0`) and decomposed Turkish
  letters (NFD); normalize when verifying.
- Because the footer is removed from the text, footer information such as
  social media links does not appear in it. Check `unanswerable` records that
  claim "X is not on the site" on the live site as well.
- Email addresses are obfuscated by Cloudflare (`[email protected]`); do not use
  them as evidence.
- The "latest post" order on tag pages is an assumption (newest first in
  Ghost); mark such records as `time_sensitive`.

### Review checklist

- [ ] The answer does not claim more than the `evidence` quote says.
- [ ] The false information in a `false_premise` question is really false and
      plausible (a mistake a user could actually make).
- [ ] The answer to an `unanswerable` question is nowhere on the site
      (searched on the live site).
- [ ] The `valid_as_of` date of `time_sensitive` records is current; outdated
      ones were re-verified.
- [ ] No duplicate or very similar questions.

## Generator Prompt

We are preparing a factuality test for a chatbot that answers questions about
kerimbalci.com. The text files you are given are the plain text of pages
downloaded from the site. The first line of every file is JSON metadata
(og:title, article:published_time, article:tag); the page text follows. For
paid articles the text may be cut at the paywall; use ONLY what is written in
the text.

**Strict rules**
1. Expected answers rely ONLY on the text in the file. Do not add anything
   from your general knowledge and do not infer.
2. In every record, the `evidence` field is a 1-2 sentence quote copied
   VERBATIM from the source text (character for character, same punctuation).
   A script will check that this quote appears in the file; if you change it,
   the record is dropped. Take the quote from a single paragraph.
3. Write the questions, expected answers and evidence in **Turkish**, natural,
   the way a site visitor would ask the chatbot. Questions about English
   articles can also be in Turkish.
4. Questions are short and focus on a single verifiable fact; rely on a claim,
   fact, name, date or number stated explicitly in the text. A view the author
   states explicitly ("the author argues X") is acceptable.
5. Spread the questions evenly over the files; no more than 3 questions from a
   single file.
6. Do not write repeated or very similar questions.
7. Before claiming that some information is NOT on the site, search all the
   files you were given.

**Categories**
- `direct_fact`: a fact question with a single correct answer.
- `false_premise`: the question assumes a fact from the text WRONGLY;
  `expected_output` says the premise is wrong and gives the correct
  information. The `false_claim` field is required (short form of the false
  claim). `evidence` shows the correct information.
- `unanswerable`: (only when requested) a question that looks related but whose
  answer is NOT on the site; `expected_output` says the information is not on
  the site and does not invent. `evidence`: the closest related context quote.
- `time_sensitive`: information that may change (membership content,
  publication dates, the latest post in a series, planned things).
  `valid_as_of`: the generation date (YYYY-MM-DD).

**Output:** Only a JSON list. Every record:

```json
{
  "input": "...",
  "expected_output": "1-3 sentences, complete and self-contained",
  "category": "direct_fact | false_premise | unanswerable | time_sensitive",
  "source_file": "<file>.txt",
  "evidence": "<verbatim quote>",
  "false_claim": "... (false_premise only)",
  "valid_as_of": "YYYY-MM-DD (time_sensitive only)"
}
```

Do not add `id` or `source_url`; they are assigned in the merge step.
