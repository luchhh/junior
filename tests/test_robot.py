import json
from unittest.mock import MagicMock, patch, call

import numpy as np

from lib.robot import Robot

FAKE_AUDIO = (np.zeros(16000), 16000)


def make_gpt(response=None):
    return MagicMock(
        chat_with_audio=MagicMock(return_value=response),
        chat=MagicMock(return_value=response),
    )


def make_source(audio_items=None):
    return MagicMock(
        __iter__=MagicMock(return_value=iter(audio_items or [FAKE_AUDIO]))
    )


def make_transcriber(text=None):
    return MagicMock(transcribe=MagicMock(return_value=text))


def make_robot(gpt=None, source=None, tts=None, firmware=None, transcriber=None, stt="openai"):
    return Robot(
        tts=tts if tts is not None else MagicMock(),
        system_prompt="test prompt",
        source=source if source is not None else make_source(),
        gpt=gpt if gpt is not None else make_gpt(),
        firmware=firmware if firmware is not None else MagicMock(),
        transcriber=transcriber if transcriber is not None else make_transcriber(),
        stt=stt,
    )


@patch("lib.robot.soundfile.write")
class TestRun:
    def test_forward(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "forward", "ms": 500}])))
        robot.run()
        robot.firmware.forward.assert_called_once_with(0.5)

    def test_backward(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "backward", "ms": 1000}])))
        robot.run()
        robot.firmware.reverse.assert_called_once_with(1.0)

    def test_left(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "left", "ms": 300}])))
        robot.run()
        robot.firmware.left_turn.assert_called_once_with(0.3)

    def test_right(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "right", "ms": 200}])))
        robot.run()
        robot.firmware.right_turn.assert_called_once_with(0.2)

    def test_speak_pauses_and_resumes_source(self, mock_write):
        tts = MagicMock()
        source = make_source()
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "speak", "body": "Hello"}])), tts=tts, source=source)
        robot.run()
        source.pause.assert_called_once()
        tts.speak.assert_called_once_with("Hello")
        source.resume.assert_called_once()

    def test_speak_resumes_even_if_tts_raises(self, mock_write):
        tts = MagicMock(speak=MagicMock(side_effect=RuntimeError("TTS failed")))
        source = make_source()
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "speak", "body": "Hello"}])), tts=tts, source=source)
        robot.run()
        source.resume.assert_called_once()

    def test_clears_firmware_before_executing(self, mock_write):
        firmware = MagicMock()
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "forward", "ms": 100}])), firmware=firmware)
        robot.run()
        assert firmware.mock_calls[0] == call.clear()

    def test_multiple_commands_in_order(self, mock_write):
        tts = MagicMock()
        firmware = MagicMock()
        robot = make_robot(
            gpt=make_gpt(json.dumps([{"command": "forward", "ms": 500}, {"command": "speak", "body": "Done"}])),
            tts=tts,
            firmware=firmware,
        )
        robot.run()
        firmware.forward.assert_called_once_with(0.5)
        tts.speak.assert_called_once_with("Done")

    def test_invalid_json_does_not_raise(self, mock_write):
        robot = make_robot(gpt=make_gpt("not json"))
        robot.run()

    def test_invalid_command_does_not_raise(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([{"command": "fly", "ms": 100}])))
        robot.run()

    def test_audio_written_to_tmp_file(self, mock_write):
        robot = make_robot(gpt=make_gpt(json.dumps([])))
        robot.run()
        mock_write.assert_called_once()
        assert mock_write.call_args[0][0] == "/tmp/robot_command.wav"

    def test_gpt_called_with_system_prompt(self, mock_write):
        gpt = make_gpt(json.dumps([]))
        robot = make_robot(gpt=gpt)
        robot.run()
        gpt.chat_with_audio.assert_called_once_with("test prompt", "/tmp/robot_command.wav")

    def test_whisper_transcribes_and_executes(self, mock_write):
        gpt = make_gpt(json.dumps([{"command": "forward", "ms": 500}]))
        firmware = MagicMock()
        robot = make_robot(gpt=gpt, firmware=firmware, transcriber=make_transcriber("move forward"), stt="whisper")
        robot.run()
        gpt.chat.assert_called_once_with("test prompt", "move forward")
        firmware.forward.assert_called_once_with(0.5)

    def test_whisper_skips_empty_transcription(self, mock_write):
        gpt = make_gpt()
        robot = make_robot(gpt=gpt, transcriber=make_transcriber(None), stt="whisper")
        robot.run()
        gpt.chat.assert_not_called()
