"""HTTP server wrapper for the notebook executor Lambda handler.

Replaces AWS Lambda invocation with a Flask HTTP endpoint.
Mocks AWS-only dependencies (ddtrace, Secrets Manager) before importing the handler.
"""

import json
import logging
import sys
import types
from contextlib import nullcontext
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Mock AWS/Datadog modules before importing lambda_function
# ---------------------------------------------------------------------------

# ddtrace — not needed outside AWS/Datadog infrastructure
_ddtrace = types.ModuleType("ddtrace")


class _MockTracer:
    def trace(self, *args, **kwargs):
        return nullcontext()


_ddtrace.tracer = _MockTracer()
sys.modules["ddtrace"] = _ddtrace

# datadog_lambda — Lambda-specific Datadog wrapper
_dd_lambda = types.ModuleType("datadog_lambda")
_dd_handler = types.ModuleType("datadog_lambda.handler")
_dd_handler.handler = None
_dd_lambda.handler = _dd_handler
sys.modules["datadog_lambda"] = _dd_lambda
sys.modules["datadog_lambda.handler"] = _dd_handler

# aws_secretsmanager_caching — only used for production DB creds
_sm = types.ModuleType("aws_secretsmanager_caching")


class _MockSecretCacheConfig:
    pass


class _MockSecretCache:
    def __init__(self, config=None, client=None):
        pass

    def get_secret_string(self, name):
        return "{}"


_sm.SecretCacheConfig = _MockSecretCacheConfig
_sm.SecretCache = _MockSecretCache
sys.modules["aws_secretsmanager_caching"] = _sm

# ---------------------------------------------------------------------------
# Now safe to import the handler
# ---------------------------------------------------------------------------

from flask import Flask, jsonify, request  # noqa: E402

from .lambda_function import lambda_handler  # noqa: E402

# Use the unwrapped handler to avoid sys.exit from configure_logger decorator
_handler = getattr(lambda_handler, "__wrapped__", lambda_handler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notebook-executor-server")

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return (
        jsonify(
            {
                "status": "healthy",
                "notebooks_available": ["dem", "slga", "weather"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


@app.route("/execute", methods=["POST"])
def execute():
    event = request.get_json(force=True)
    logger.info("Executing notebook: %s", event.get("notebook_name", "unknown"))

    try:
        result = _handler(event, None)
    except SystemExit:
        logger.exception("Notebook execution caused SystemExit")
        return jsonify({"error": "Notebook execution failed"}), 500
    except Exception as exc:
        logger.exception("Notebook execution error")
        return jsonify({"error": str(exc)}), 500

    status_code = result.get("statusCode", 200)
    body = result.get("body", {})

    # Lambda handler returns body as dict for 200, sometimes as JSON string for errors
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {"message": body}

    return jsonify(body), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9002, debug=False)
