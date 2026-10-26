
from typing import Literal

from pydantic import BaseModel, Field


class TicketAnalysis(BaseModel):
    summary: str = Field(
        description="A concise summary of the customer's issue"
    )

    category: Literal[
        "technical", "billing", "account", "general"
    ]

    priority: Literal[
        "low", "medium", "high", "urgent"
    ]

    customer_issue: str = Field(
        description="The main problem the customer is experiencing"
    )

    recommended_action: str = Field(
        description="The next action the support team should take"
    )


class CustomerReply(BaseModel):
    customer_reply: str = Field(
        min_length=1,
        description=(
            "A professional, empathetic response drafted for "
            "the customer based on the ticket and available "
            "knowledge-base guidance. The response must not "
            "invent facts, promise unconfirmed outcomes, or "
            "claim that an action has already been completed."
        ),
    )
