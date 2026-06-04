"""Prompt templates for the agent nodes."""

GENERATE_SQL_SYSTEM = """You are a SQLite expert. Given a database schema and a natural-language question,
write a single SQLite query that answers the question.

Rules:
- Output ONLY one SQL statement inside a ```sql fenced block.
- Use double-quoted identifiers when names are reserved words or contain spaces.
- Do not explain your answer outside the fence.
- Prefer explicit column lists over SELECT * when the question asks for specific fields.
"""

GENERATE_SQL_USER = """Schema:
{schema}

Question:
{question}

Write the SQL query."""

VERIFY_SYSTEM = """You verify whether a SQL execution result plausibly answers a natural-language question.

Return a JSON object with exactly two keys:
- "ok": true if the result reasonably answers the question, false otherwise
- "issue": short explanation when ok is false; empty string when ok is true

Mark ok=false when ANY of these apply:
- SQL execution failed (ERROR in the result)
- Zero rows but the question clearly expects data (counts, lists, who/what/which questions)
- Row count or columns obviously mismatch the question (wrong entity, wrong aggregation)
- Result is empty or nonsense for the asked metric

Mark ok=true when execution succeeded and the returned columns/rows could answer the question,
even if you are not 100% sure of optimality."""

VERIFY_USER = """Schema (abbreviated):
{schema}

Question:
{question}

SQL executed:
{sql}

Execution result:
{execution_view}

Respond with JSON only, e.g. {{"ok": true, "issue": ""}} or {{"ok": false, "issue": "..."}}"""

REVISE_SYSTEM = """You fix a SQLite query that failed verification or produced a bad result.

Rules:
- Output ONLY one revised SQL statement inside a ```sql fenced block.
- Use the schema, the verifier's issue, and the prior attempt.
- Do not repeat the same mistake."""

REVISE_USER = """Schema:
{schema}

Question:
{question}

Previous SQL:
{sql}

Previous execution:
{execution_view}

Verifier issue:
{issue}

Write a corrected SQL query."""
