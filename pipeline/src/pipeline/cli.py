from __future__ import annotations

import argparse

from pipeline.runner import (
    run_batch_pipeline,
    run_engineering_doc_pipeline,
    run_pipeline,
    run_wiki_batch,
    run_wiki_pipeline,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ontology Factory pipelines, including the engineering-doc fast path.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Single input document path.")
    group.add_argument("--input-dir", help="Batch input directory.")
    parser.add_argument("--mode", choices=["wiki", "structured", "engineering-doc"], default="wiki", help="Pipeline mode.")
    parser.add_argument("--glob", default="*.txt", help="Glob used for batch mode.")
    parser.add_argument("--preprocess-config", default=None, help="Optional preprocess config path.")
    parser.add_argument("--pipeline-config", default=None, help="Optional pipeline config path.")
    parser.add_argument("--force-reingest", action="store_true", help="Reprocess duplicated content hash inputs.")
    parser.add_argument("--project-id", default=None, help="Optional xiaogugit project id for engineering-doc mode.")
    parser.add_argument("--filename", default=None, help="Optional xiaogugit filename for engineering-doc mode.")
    parser.add_argument("--xiaogugit-root", default=None, help="Optional xiaogugit storage root for engineering-doc mode.")
    parser.add_argument("--document-title", default=None, help="Optional document title override for engineering-doc mode.")
    args = parser.parse_args()

    if args.mode == "engineering-doc":
        if args.input_dir:
            parser.error("--mode engineering-doc only supports --input")
        result = run_engineering_doc_pipeline(
            args.input,
            preprocess_config=args.preprocess_config,
            pipeline_config=args.pipeline_config,
            xiaogugit_root=args.xiaogugit_root,
            project_id=args.project_id,
            filename=args.filename,
            document_title=args.document_title,
        )
    elif args.mode == "wiki":
        if args.input_dir:
            result = run_wiki_batch(
                args.input_dir,
                glob=args.glob,
                preprocess_config=args.preprocess_config,
                pipeline_config=args.pipeline_config,
                force_reingest=args.force_reingest,
            )
        else:
            result = run_wiki_pipeline(
                args.input,
                preprocess_config=args.preprocess_config,
                pipeline_config=args.pipeline_config,
                force_reingest=args.force_reingest,
            )
    else:
        if args.input_dir:
            result = run_batch_pipeline(
                args.input_dir,
                glob=args.glob,
                preprocess_config=args.preprocess_config,
                pipeline_config=args.pipeline_config,
                force_reingest=args.force_reingest,
            )
        else:
            result = run_pipeline(
                args.input,
                preprocess_config=args.preprocess_config,
                pipeline_config=args.pipeline_config,
                force_reingest=args.force_reingest,
            )

    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
