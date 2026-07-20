# Controlled Preflight demonstration packages

These three packages present different report states for the same fictional subject. Every assignment fact, identifier, location, comparable, report statement, and conclusion is synthetic. Five owner-supplied residential reference photos were selected to exclude addresses, signs, vehicles, people, and personal portraits, then re-encoded without EXIF metadata. They are not evidence from a real appraisal assignment.

Each ZIP includes a three-page extractable report PDF, five sanitized photographs, a README, and—except for the intentionally incomplete scenario—structured XML. Source files are retained under `scenarios/`; the sanitized canonical photos are under `photo_sources/`.

Upload a ZIP through **Preflight > New review**:

| Package | Intended outcome | Stable deterministic result |
| --- | --- | --- |
| `coappraiser-demo-01-ready.zip` | Same subject, aligned evidence | One advisory baseline finding; XML, PDF, commentary, and photos align. |
| `coappraiser-demo-02-reconcile.zip` | Same subject, reconcile evidence | Four predictable rule-based warnings plus direct photo/narrative conflicts involving the rear deck, enclosure, and exterior description. |
| `coappraiser-demo-03-incomplete.zip` | Same subject, missing export plus incomplete comparable commentary | One critical deterministic finding because the XML export is intentionally missing; GPT-5.6 separately reviews the rendered comparable commentary. |

GPT-5.6 may add evidence-grounded interpretive findings in its separate UI section. The deterministic outcomes above remain predictable.

## Public demo replay

The public `/demo/` route performs package opening, file inventory, evidence extraction, and deterministic checks for every visitor. It does **not** call the OpenAI API. Instead, `demo/snapshots/` contains one paid, scored GPT-5.6 result for each exact package hash. The progress page identifies the recorded-model stage, and the result page exposes the same evidence, decision, and workfile interface as an authenticated review.

Refresh the snapshots only after the packages or review prompt intentionally change:

```powershell
$env:COAPPRAISER_LLM_PROVIDER="openai"
$env:COAPPRAISER_LLM_MODEL="gpt-5.6"
python manage.py evaluate_gpt56 --repeat 1 --confirm-paid-api --strict
python manage.py build_demo_snapshots
```

The first command makes three paid model requests and must pass all evaluation gates. The second command hash-locks those accepted outputs to the three packages. Runtime rejects a package whose hash no longer matches its snapshot.

Rebuild all source files and ZIPs from the repository root:

```powershell
pip install -r demo\requirements.txt
python demo\build_scenario_packages.py
```

The reports, XML, and assignment data are generated demonstration artifacts, not appraisal reports or value opinions. Do not replace the sanitized canonical photos with identifiable assignment images.
