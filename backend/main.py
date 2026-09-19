import logging
import time

from fastapi import FastAPI

from controller import process_webhook
from dialogflow_contract import WebhookRequest
from phase8_controller import (
    handles_phase8_tag,
    process_phase8_webhook,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "symptomscout.phase8"
)


app = FastAPI(
    title="SymptomScout Controller",
    version="1.1.0",
    description=(
        "Non-diagnostic Dialogflow CX webhook "
        "for symptom communication, dialogue "
        "control, structured review, and "
        "patient confirmation."
    ),
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "symptomscout",
        "phase": "8",
    }


@app.post("/dialogflow/webhook")
def dialogflow_webhook(
    request: WebhookRequest,
) -> dict:

    started = time.perf_counter()

    tag = (
        request.fulfillment_info.tag
        or ""
    ).strip()

    # Phase 8 requests are handled separately.
    # Everything else remains controlled by
    # the proven Phase 7 controller.
    if handles_phase8_tag(tag):

        response = (
            process_phase8_webhook(
                request
            )
        )

    else:

        response = process_webhook(
            request
        )

    response_parameters = (
        response
        .get("sessionInfo", {})
        .get("parameters", {})
        if isinstance(
            response,
            dict,
        )
        else {}
    )

    action = (
        response_parameters.get(
            "p8_action"
        )
        or response_parameters.get(
            "p7_action"
        )
        or "unknown"
    )

    session_id = (
        request.session_info.session
        or ""
    )

    session_tail = (
        session_id[-8:]
        if session_id
        else ""
    )

    page_name = (
        request.page_info.display_name
        if request.page_info
        else ""
    )

    duration_ms = (
        time.perf_counter()
        - started
    ) * 1000

    # Do NOT log symptom content.
    logger.info(
        (
            "webhook session=%s "
            "page=%s "
            "tag=%s "
            "action=%s "
            "duration_ms=%.2f"
        ),
        session_tail,
        page_name,
        tag,
        action,
        duration_ms,
    )

    return response
