"""
Data models for robot commands using Pydantic for validation.
"""
from pydantic import BaseModel, Field, RootModel
from typing import Literal, Union, List, Annotated


class MovementCommand(BaseModel):
    """Movement command with duration in milliseconds"""
    command: Literal["forward", "backward", "left", "right"]
    ms: int = Field(..., ge=0, description="Duration in milliseconds")


class SpeakCommand(BaseModel):
    """Speech command with text to speak"""
    command: Literal["speak"]
    body: str = Field(..., min_length=1, description="Text to speak")


# Discriminated union using 'command' field
Command = Annotated[Union[MovementCommand, SpeakCommand], Field(discriminator='command')]

# Helper for parsing list of commands
class CommandList(RootModel):
    root: List[Command]
