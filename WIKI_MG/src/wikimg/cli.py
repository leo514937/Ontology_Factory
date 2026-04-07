from __future__ import annotations

import argparse
from pathlib import Path

from wikimg.core import (
    WikiError,
    create_document,
    delete_document,
    discover_workspace,
    doctor,
    init_workspace,
    launch_editor,
    move_document,
    normalize_layer,
    render_rows,
    rename_document,
    resolve_document,
    scan_documents,
    search_documents,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wikimg",
        description="Manage a layered Markdown wiki from the command line.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Workspace root or a path inside the workspace.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize a new wiki workspace.")

    new_parser = subparsers.add_parser("new", help="Create a new document.")
    new_parser.add_argument("layer", help="Document layer: common, domain, private.")
    new_parser.add_argument("title", help="Document title.")
    new_parser.add_argument("--slug", help="Optional path-like slug.")
    new_parser.add_argument("--edit", action="store_true", help="Open the new file in an editor.")
    new_parser.add_argument("--editor", help="Editor command override.")

    list_parser = subparsers.add_parser("list", help="List documents.")
    list_parser.add_argument("--layer", help="Optional layer filter.")

    show_parser = subparsers.add_parser("show", help="Print a document.")
    show_parser.add_argument("reference", help="Document reference.")
    show_parser.add_argument("--path", action="store_true", help="Print only the file path.")

    edit_parser = subparsers.add_parser("edit", help="Open a document in an editor.")
    edit_parser.add_argument("reference", help="Document reference.")
    edit_parser.add_argument("--editor", help="Editor command override.")

    rename_parser = subparsers.add_parser("rename", help="Rename a document.")
    rename_parser.add_argument("reference", help="Document reference.")
    rename_parser.add_argument("title", help="New title.")
    rename_parser.add_argument("--slug", help="Optional new slug.")

    move_parser = subparsers.add_parser("move", help="Move a document to another layer.")
    move_parser.add_argument("reference", help="Document reference.")
    move_parser.add_argument("layer", help="Target layer.")
    move_parser.add_argument("--slug", help="Optional slug override in the target layer.")

    delete_parser = subparsers.add_parser("delete", help="Delete a document.")
    delete_parser.add_argument("reference", help="Document reference.")
    delete_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion without prompting.",
    )

    search_parser = subparsers.add_parser("search", help="Search documents.")
    search_parser.add_argument("query", help="Search text.")
    search_parser.add_argument("--layer", help="Optional layer filter.")
    search_parser.add_argument(
        "--content",
        action="store_true",
        help="Search inside Markdown body content too.",
    )

    subparsers.add_parser("doctor", help="Validate the workspace.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            workspace = init_workspace(Path(args.root))
            print(f"Initialized wiki workspace at {workspace.root}")
            return 0

        workspace = discover_workspace(Path(args.root))

        if args.command == "new":
            document = create_document(workspace, args.layer, args.title, slug=args.slug)
            print(f"Created {document.ref} -> {document.path}")
            if args.edit:
                launch_editor(document.path, editor=args.editor)
            return 0

        if args.command == "list":
            layer = normalize_layer(args.layer) if args.layer else None
            documents = scan_documents(workspace, layer=layer)
            if not documents:
                print("No documents found.")
                return 0
            rows = [("LAYER", "REF", "TITLE", "UPDATED")]
            rows.extend(
                (document.layer, document.ref, document.title, document.updated_at)
                for document in documents
            )
            print(render_rows(rows))
            return 0

        if args.command == "show":
            document = resolve_document(workspace, args.reference)
            if args.path:
                print(document.path)
            else:
                print(document.path.read_text(encoding="utf-8"), end="")
            return 0

        if args.command == "edit":
            document = resolve_document(workspace, args.reference)
            launch_editor(document.path, editor=args.editor)
            print(f"Edited {document.ref}")
            return 0

        if args.command == "rename":
            document = rename_document(workspace, args.reference, args.title, slug=args.slug)
            print(f"Renamed document -> {document.ref}")
            return 0

        if args.command == "move":
            document = move_document(workspace, args.reference, args.layer, slug=args.slug)
            print(f"Moved document -> {document.ref}")
            return 0

        if args.command == "delete":
            if not args.yes:
                raise WikiError("Refusing to delete without --yes.")
            document = delete_document(workspace, args.reference)
            print(f"Deleted {document.ref}")
            return 0

        if args.command == "search":
            layer = normalize_layer(args.layer) if args.layer else None
            documents = search_documents(
                workspace,
                args.query,
                layer=layer,
                content=args.content,
            )
            if not documents:
                print("No documents matched.")
                return 0
            rows = [("LAYER", "REF", "TITLE", "UPDATED")]
            rows.extend(
                (document.layer, document.ref, document.title, document.updated_at)
                for document in documents
            )
            print(render_rows(rows))
            return 0

        if args.command == "doctor":
            issues = doctor(workspace)
            if not issues:
                print("Workspace looks healthy.")
                return 0
            for issue in issues:
                print(f"- {issue}")
            return 1

        parser.error(f"Unsupported command: {args.command}")
        return 2
    except WikiError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
