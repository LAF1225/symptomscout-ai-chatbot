import logging
import time

from fastapi import FastAPI

from controller import process_webhook
from dialogflow_contract import WebhookRequest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(
    "symptomscout.phase7"
)


app = FastAPI(
    title="SymptomScout Phase 7 Controller",
    version="1.0.0",
    description=(
        "Non-diagnostic conversational control webhook "
        "for Dialogflow CX."
    ),
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "symptomscout-phase7",
    }


@app.post("/dialogflow/webhook")
def dialogflow_webhook(
    request: WebhookRequest,
) -> dict:

    start_time = time.perf_counter()

    response = process_webhook(
        request
    )

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    session = (
        request.session_info.session
        or ""
    )

    session_id = (
        session.rsplit("/", 1)[-1]
        if session
        else "unknown"
    )

    # Log only a shortened identifier.
    session_tail = session_id[-8:]

    page_name = (
        request.page_info.display_name
        if request.page_info
        else ""
    )

    tag = (
        request.fulfillment_info.tag
        or ""
    )

    action = (
        response
        .get("sessionInfo", {})
        .get("parameters", {})
        .get("p7_action", "")
    )

    logger.info(
        "webhook session=%s page=%s tag=%s action=%s duration_ms=%.2f",
        session_tail,
        page_name,
        tag,
        action,
        duration_ms,
    )

    return response
