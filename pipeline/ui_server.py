"""Local HTTP server for the Growth OS browser interface."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pipeline.channels import all_channel_status
from pipeline.ui_service import CreatorDiscoveryUIService, UIServiceError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = PROJECT_ROOT / "ui"
MAX_BODY_BYTES = 128 * 1024


class CreatorDiscoveryRequestHandler(BaseHTTPRequestHandler):
    service: CreatorDiscoveryUIService

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler interface
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._serve_file(UI_ROOT / "index.html")
            return
        if path in {"/styles.css", "/app.js", "/effects.js"}:
            self._serve_file(UI_ROOT / path.removeprefix("/"))
            return
        if path == "/api/health":
            self._json_response({"status": "ok"})
            return
        if path == "/api/bootstrap":
            self._json_response(self.service.bootstrap())
            return
        if path == "/api/data-sources":
            # channel_status() reads the environment by variable name and returns
            # a boolean, so no credential value can reach this response.
            self._json_response({"channels": all_channel_status()})
            return
        if path.startswith("/api/creators/"):
            record_id = path.removeprefix("/api/creators/").strip("/")
            try:
                self._json_response(self.service.creator_detail(record_id))
            except UIServiceError as exc:
                self._json_response(
                    {"error": {"code": exc.code, "message": str(exc)}},
                    HTTPStatus.NOT_FOUND,
                )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler interface
        path = urlparse(self.path).path
        try:
            payload = self._read_json_body()
            if path == "/api/search-plan":
                result = self.service.generate_search_plan(payload.get("original_brief"))
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path == "/api/icp/generate":
                result = self.service.generate_icp_hypotheses(
                    payload,
                    provider_mode=payload.get("provider_mode", "mock"),
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path == "/api/icp/edit":
                result = self.service.edit_icp_hypothesis(
                    hypothesis_id=payload.get("hypothesis_id"),
                    version=payload.get("version"),
                    changes=payload.get("changes"),
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path == "/api/icp/select":
                result = self.service.select_icp_hypothesis(
                    hypothesis_id=payload.get("hypothesis_id"),
                    version=payload.get("version"),
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path == "/api/icp/criteria/confirm":
                result = self.service.confirm_icp_criteria(
                    criteria_id=payload.get("criteria_id"),
                    payload=payload.get("criteria") or {},
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path == "/api/run-discovery":
                result = self.service.run_discovery(
                    workflow_id=payload.get("workflow_id"),
                    actions=payload.get("actions"),
                    mode=payload.get("mode"),
                    confirm_live=payload.get("confirm_live", False),
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            if path.startswith("/api/creators/") and path.endswith("/review"):
                record_id = path.removeprefix("/api/creators/").removesuffix("/review").strip("/")
                result = self.service.submit_creator_review(
                    record_id=record_id,
                    status=payload.get("status"),
                    structured_reason=payload.get("structured_reason"),
                    comment=payload.get("comment"),
                )
                self._json_response(result, HTTPStatus.CREATED)
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except UIServiceError as exc:
            self._json_response(
                {"error": {"code": exc.code, "message": str(exc)}},
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            self._json_response(
                {"error": {"code": "invalid_request", "message": "Request body must be valid JSON."}},
                HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - final safety boundary
            self.log_error("Unhandled API failure: %s", exc.__class__.__name__)
            self._json_response(
                {"error": {"code": "internal_error", "message": "The local UI service failed safely."}},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError("invalid request length")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise TypeError("JSON body must be an object")
        return value

    def _serve_file(self, path: Path) -> None:
        if not path.is_file() or path.parent != UI_ROOT:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json_response(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[ui] {self.address_string()} - {format % args}")


def build_server(
    *, host: str, port: int, database_path: str | Path
) -> ThreadingHTTPServer:
    service = CreatorDiscoveryUIService(database_path)
    handler = type(
        "ConfiguredCreatorDiscoveryRequestHandler",
        (CreatorDiscoveryRequestHandler,),
        {"service": service},
    )
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Growth OS UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--database-path",
        default=str(PROJECT_ROOT / "data" / "creator_discovery_os_v1.db"),
    )
    args = parser.parse_args()
    server = build_server(
        host=args.host,
        port=args.port,
        database_path=args.database_path,
    )
    print(f"Growth OS: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
