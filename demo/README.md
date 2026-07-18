# Synthetic Preflight demonstration packages

These three controlled residential appraisal packages contain no borrower, client, lender, appraiser, signature, credential, or real-property information. Each includes a three-page extractable report PDF and three labeled synthetic exhibits. Source files are retained under `scenarios/` for inspection.

Upload a ZIP through **Preflight > New review**:

| Package | Intended outcome | Stable deterministic result |
| --- | --- | --- |
| `coappraiser-demo-01-ready.zip` | Ready for appraiser review | One advisory baseline finding; XML, PDF, commentary, and exhibits are aligned. |
| `coappraiser-demo-02-reconcile.zip` | Reconcile before delivery | Four warnings: PDF/XML condition conflict, structured/narrative condition conflict, structured/narrative quality conflict, and incomplete comparable commentary. |
| `coappraiser-demo-03-incomplete.zip` | Incomplete package | One critical finding because the XML export is intentionally missing. |

GPT-5.6 may add evidence-grounded interpretive findings in its separate UI section. The deterministic outcomes above remain predictable.

Rebuild all source files and ZIPs from the repository root:

```powershell
pip install -r demo\requirements.txt
python demo\build_scenario_packages.py
```

The generated reports and exhibits are demonstration artifacts, not appraisal reports or value opinions.
