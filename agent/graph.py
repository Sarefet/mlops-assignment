"""LangGraph agent: text-to-SQL with verify+revise loop."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from agent import prompts
from agent.execution import ExecutionResult, execute_sql
from agent.schema import render_schema

MAX_ITERATIONS = 3

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")
LLM_API_KEY = os.environ.get("OPENAI_API_KEY", "not-needed")


@dataclass
class AgentState:
    question: str
    db_id: str
    schema: str = ""
    sql: str = ""
    execution: ExecutionResult | None = None
    verify_ok: bool = False
    verify_issue: str = ""
    iteration: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)


def llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=VLLM_MODEL,
        base_url=VLLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0.0,
        timeout=300,
        max_retries=1,
    )


def _attach_schema(state: AgentState) -> dict:
    return {"schema": render_schema(state.db_id)}


def _extract_sql(text: str) -> str:
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return (fenced.group(1) if fenced else text).strip()


def _parse_verify_json(text: str) -> tuple[bool, str]:
    """Parse {"ok": bool, "issue": str} from model output."""
    text = text.strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\"ok\"[^{}]*\}", text, re.DOTALL)
        if not match:
            return False, "verifier returned unparseable response"
        try:
            obj = json.loads(match.group(0))
        except json.JSONDecodeError:
            return False, "verifier returned unparseable response"
    ok = bool(obj.get("ok", False))
    issue = str(obj.get("issue", "") or "")
    return ok, issue


def generate_sql_node(state: AgentState) -> dict:
    response = llm().invoke([
        ("system", prompts.GENERATE_SQL_SYSTEM),
        ("user", prompts.GENERATE_SQL_USER.format(
            schema=state.schema,
            question=state.question,
        )),
    ])
    sql = _extract_sql(response.content)
    return {
        "sql": sql,
        "iteration": state.iteration + 1,
        "history": state.history + [{"node": "generate_sql", "sql": sql}],
    }


def execute_node(state: AgentState) -> dict:
    return {"execution": execute_sql(state.db_id, state.sql)}


def verify_node(state: AgentState) -> dict:
    execution = state.execution
    execution_view = execution.render() if execution else "No execution yet."
    response = llm().invoke([
        ("system", prompts.VERIFY_SYSTEM),
        ("user", prompts.VERIFY_USER.format(
            schema=state.schema[:4000],
            question=state.question,
            sql=state.sql,
            execution_view=execution_view,
        )),
    ])
    verify_ok, verify_issue = _parse_verify_json(response.content)
    if execution and not execution.ok:
        verify_ok = False
        verify_issue = verify_issue or execution.error or "SQL execution failed"
    return {
        "verify_ok": verify_ok,
        "verify_issue": verify_issue,
        "history": state.history + [{
            "node": "verify",
            "ok": verify_ok,
            "issue": verify_issue,
        }],
    }


def revise_node(state: AgentState) -> dict:
    execution_view = state.execution.render() if state.execution else "No execution."
    response = llm().invoke([
        ("system", prompts.REVISE_SYSTEM),
        ("user", prompts.REVISE_USER.format(
            schema=state.schema,
            question=state.question,
            sql=state.sql,
            execution_view=execution_view,
            issue=state.verify_issue,
        )),
    ])
    sql = _extract_sql(response.content)
    return {
        "sql": sql,
        "iteration": state.iteration + 1,
        "history": state.history + [{
            "node": "revise",
            "sql": sql,
            "issue": state.verify_issue,
        }],
    }


def route_after_verify(state: AgentState) -> str:
    if state.verify_ok or state.iteration >= MAX_ITERATIONS:
        return "end"
    return "revise"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("attach_schema", _attach_schema)
    g.add_node("generate_sql", generate_sql_node)
    g.add_node("execute", execute_node)
    g.add_node("verify", verify_node)
    g.add_node("revise", revise_node)

    g.add_edge(START, "attach_schema")
    g.add_edge("attach_schema", "generate_sql")
    g.add_edge("generate_sql", "execute")
    g.add_edge("execute", "verify")
    g.add_conditional_edges(
        "verify",
        route_after_verify,
        {"revise": "revise", "end": END},
    )
    g.add_edge("revise", "execute")
    return g.compile()


graph = build_graph()
