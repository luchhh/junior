import pytest
from pydantic import ValidationError

from lib.models import MovementCommand, SpeakCommand, CommandList


class TestMovementCommand:
    def test_valid_commands(self):
        for direction in ["forward", "backward", "left", "right"]:
            cmd = MovementCommand(command=direction, ms=500)
            assert cmd.command == direction
            assert cmd.ms == 500

    def test_zero_ms_is_valid(self):
        cmd = MovementCommand(command="forward", ms=0)
        assert cmd.ms == 0

    def test_negative_ms_rejected(self):
        with pytest.raises(ValidationError):
            MovementCommand(command="forward", ms=-1)

    def test_invalid_command_rejected(self):
        with pytest.raises(ValidationError):
            MovementCommand(command="spin", ms=500)


class TestSpeakCommand:
    def test_valid(self):
        cmd = SpeakCommand(command="speak", body="Hello!")
        assert cmd.body == "Hello!"

    def test_empty_body_rejected(self):
        with pytest.raises(ValidationError):
            SpeakCommand(command="speak", body="")


class TestCommandList:
    def test_parses_movement(self):
        commands = CommandList(root=[{"command": "forward", "ms": 1000}]).root
        assert len(commands) == 1
        assert isinstance(commands[0], MovementCommand)

    def test_parses_speak(self):
        commands = CommandList(root=[{"command": "speak", "body": "Hi"}]).root
        assert isinstance(commands[0], SpeakCommand)

    def test_mixed_commands(self):
        commands = CommandList(root=[
            {"command": "forward", "ms": 500},
            {"command": "speak", "body": "Done"},
        ]).root
        assert isinstance(commands[0], MovementCommand)
        assert isinstance(commands[1], SpeakCommand)

    def test_empty_list(self):
        commands = CommandList(root=[]).root
        assert commands == []

    def test_invalid_command_rejected(self):
        with pytest.raises(ValidationError):
            CommandList(root=[{"command": "fly", "ms": 100}])
