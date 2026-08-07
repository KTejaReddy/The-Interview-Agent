# Datasets

Place the three mandatory datasets in this directory (`backend/data/`).

```
backend/data/
├── curriculum.json    # REQUIRED — the training curriculum
├── candidate.json     # REQUIRED — candidate records
└── technical-spec.md  # REQUIRED — the technical specification
```

The application **reads these files at startup and never modifies them**.
No fields are renamed, removed or invented.

## Expected shapes

The loaders are intentionally tolerant — they accept several common field
spellings and degrade gracefully when a field is absent — but the files
should look like this:

### curriculum.json

```json
{
  "days": [
    {
      "id": 1,
      "title": "Introduction to Python",
      "module": "Programming Fundamentals",
      "objectives": ["Understand variables and types"],
      "tools": ["Python 3", "VS Code"],
      "learning_goals": ["Write a first script"],
      "topics": ["variables", "conditionals", "loops"]
    }
  ]
}
```

A top-level array of day objects is also accepted. The retriever exposes
`objectives`, `tools`, `module`, `learning_goals` and `topics` verbatim for
each requested day.

### candidate.json

```json
{
  "candidates": [
    {
      "id": "candidate-1",
      "name": "Alex Doe",
      "role": "Junior Python Developer",
      "experience": 1.5,
      "education": "B.Sc. Computer Science",
      "missions": [
        {
          "topic": "python-loops",
          "status": "passed",
          "attempts": 1
        }
      ],
      "passed": ["python-basics"],
      "failed": ["oops-concepts"],
      "skipped": ["algorithms"],
      "signals": {"python-basics": ["strong", "passed"]}
    }
  ]
}
```

A top-level array of candidates is also accepted. The candidate analyzer
uses whichever fields are present and neutral defaults for the rest — the
interview adapts to **any** candidate in the file.

### technical-spec.md

Any markdown file. Its content is loaded read-only and kept available to
the feedback generator and API layer so the project stays aligned with the
specification document.

## Health check

`GET /api/health` reports whether each dataset loaded, how many curriculum
days and candidates were found, and whether the LLM is configured.
