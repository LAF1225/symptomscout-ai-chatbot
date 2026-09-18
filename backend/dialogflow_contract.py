from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DialogflowBaseModel(BaseModel):
    """
    Base model for Dialogflow payloads.

    Dialogflow may include undocumented/internal fields.
    We deliberately ignore anything we do not need.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


class FulfillmentInfo(DialogflowBaseModel):
    tag: str = ""


class ParameterInfo(DialogflowBaseModel):
    display_name: str = Field(default="", alias="displayName")
    required: bool = False
    state: str | None = None
    value: Any = None
    just_collected: bool = Field(default=False, alias="justCollected")


class FormInfo(DialogflowBaseModel):
    parameter_info: list[ParameterInfo] = Field(
        default_factory=list,
        alias="parameterInfo",
    )


class PageInfo(DialogflowBaseModel):
    current_page: str = Field(default="", alias="currentPage")
    display_name: str = Field(default="", alias="displayName")
    form_info: FormInfo | None = Field(default=None, alias="formInfo")


class SessionInfo(DialogflowBaseModel):
    session: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class WebhookRequest(DialogflowBaseModel):
    fulfillment_info: FulfillmentInfo = Field(
        default_factory=FulfillmentInfo,
        alias="fulfillmentInfo",
    )

    page_info: PageInfo | None = Field(
        default=None,
        alias="pageInfo",
    )

    session_info: SessionInfo = Field(
        default_factory=SessionInfo,
        alias="sessionInfo",
    )

    text: str | None = None
    transcript: str | None = None