from __future__ import annotations

import argparse
import re
from pathlib import Path

from entity_relation.extractor import extract_relations
from ner.extractor import extract_entities


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；\n])")


def main() -> int:
    parser = argparse.ArgumentParser(description="Relation extraction command line interface.")
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser("extract", help="Extract relations from text.")
    extract_parser.add_argument("--input", required=True, help="Input plain text path.")
    extract_parser.add_argument("--output", default="", help="Optional output JSON path.")
    extract_parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout.")
    extract_parser.add_argument("--doc-id", default="", help="Optional document identifier.")
    extract_parser.add_argument("--query", default="", help="Optional query term to narrow extraction.")
    extract_parser.add_argument("--max-sentences", type=int, default=8, help="Used with --query to narrow extraction.")
    args = parser.parse_args()

    if args.command not in {"extract", None}:
        parser.error(f"unsupported command: {args.command}")

    input_path = Path(args.input)
    text = input_path.read_text(encoding="utf-8")
    if args.query.strip():
        text = _slice_text_by_query(text, args.query.strip(), max_sentences=max(1, int(args.max_sentences)))
    doc_id = args.doc_id or input_path.stem
    ner_document = extract_entities(text, doc_id=doc_id, use_llm=False, llm_client=None)
    relation_document = extract_relations(ner_document)
    rendered = relation_document.model_dump_json(indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    if args.stdout or not args.output:
        print(rendered)
    return 0


def _slice_text_by_query(text: str, query: str, *, max_sentences: int) -> str:
    sentences = [piece.strip() for piece in _SENTENCE_SPLIT_RE.split(text) if piece.strip()]
    direct = [sentence for sentence in sentences if query in sentence]
    if not direct:
        lowered = query.lower()
        direct = [sentence for sentence in sentences if lowered in sentence.lower()]
    return "\n".join(direct[:max_sentences]) or text


if __name__ == "__main__":
    raise SystemExit(main())
