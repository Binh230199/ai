from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("rules", "relationships", "items"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return candidate
    raise ValueError(f"Unsupported JSON structure in {value!r}")


def node_id(rule_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", rule_id)
    return f"R_{cleaned}"


def escape_label(value: str) -> str:
    return value.replace('"', "'")


def build_graph(rule_records, relationships) -> str:
    lines = ["graph TD"]
    seen_nodes: set[str] = set()

    for rule in rule_records:
        rule_identifier = str(rule.get("rule_id", "unknown"))
        title = str(rule.get("title", ""))
        label = escape_label(f"{rule_identifier}: {title}".strip())
        identifier = node_id(rule_identifier)
        seen_nodes.add(identifier)
        lines.append(f'  {identifier}["{label}"]')

    for relation in relationships:
        source = str(relation.get("source_rule", "unknown"))
        target = str(relation.get("target_rule", "unknown"))
        rel_type = escape_label(str(relation.get("relationship", "related")))
        source_id = node_id(source)
        target_id = node_id(target)
        if source_id not in seen_nodes:
            lines.append(f'  {source_id}["{escape_label(source)}"]')
            seen_nodes.add(source_id)
        if target_id not in seen_nodes:
            lines.append(f'  {target_id}["{escape_label(target)}"]')
            seen_nodes.add(target_id)
        lines.append(f"  {source_id} -->|{rel_type}| {target_id}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Mermaid rule graph from normalized rules and relationships."
    )
    parser.add_argument("rules", help="Path to rules-normalized.json")
    parser.add_argument("relationships", help="Path to rule-relationships.json")
    parser.add_argument("output", help="Output Mermaid file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rules_path = Path(args.rules)
    relationships_path = Path(args.relationships)
    output_path = Path(args.output)

    rule_records = ensure_list(load_json(rules_path))
    relationships = ensure_list(load_json(relationships_path))
    graph = build_graph(rule_records, relationships)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(graph, encoding="utf-8")
    print(f"Wrote Mermaid graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
