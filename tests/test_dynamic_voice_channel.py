import unittest
import discord

from databot.features.dynamic_channel import (
    IDENTIFIER,
    _filter_for_dynamic_channel,
    _dynamic_channel_base_name,
    _group_dynamic_channel,
)


class TestDynamicVoiceChannel(unittest.TestCase):
    def test_filter_for_dynamic_channel(self):
        not_dynamic_channel_names: list[str] = [
            "not_dynamic",
            f"not_dynamic{IDENTIFIER}",
            "not_dynamic1",
            f"not_{IDENTIFIER}1dynamic",
        ]
        dynamic_channel_names: list[str] = [
            f"dynamic{IDENTIFIER}1",
            f"dynamic {IDENTIFIER}2",
            f"dynamic {IDENTIFIER}123",
            f"dynamic {IDENTIFIER}12{IDENTIFIER}12",
        ]
        channels: list[MockVoiceChannel] = list(MockVoiceChannel(name) for name in not_dynamic_channel_names)
        channels.extend(MockVoiceChannel(name) for name in dynamic_channel_names)

        result: list[str] = map(lambda x: x.name, _filter_for_dynamic_channel(channels))
        self.assertEqual(sorted(result), sorted(dynamic_channel_names))

    def test_dynamic_channel_base_name(self):
        self.assertEqual(_dynamic_channel_base_name(MockVoiceChannel(f"dynamic {IDENTIFIER}12")), "dynamic ")
        self.assertEqual(
            _dynamic_channel_base_name(MockVoiceChannel(f"dynamic {IDENTIFIER}12 {IDENTIFIER}12")),
            f"dynamic {IDENTIFIER}12 ",
        )
        self.assertEqual(
            _dynamic_channel_base_name(MockVoiceChannel(f"not_dynamic{IDENTIFIER}")), f"not_dynamic{IDENTIFIER}"
        )
        self.assertEqual(
            _dynamic_channel_base_name(MockVoiceChannel(f"not_dynamic{IDENTIFIER}12|")), f"not_dynamic{IDENTIFIER}12|"
        )

    def test_group_dynamic_channel(self):
        to_mock_vcs = lambda vcs: list(map(lambda x: MockVoiceChannel(x), vcs))
        channels_1: list[str] = to_mock_vcs(
            [
                f"dynamic {IDENTIFIER}1",
                f"dynamic {IDENTIFIER}2",
                f"dynamic {IDENTIFIER}123",
                f"dynamic {IDENTIFIER}12",
            ]
        )
        channels_2 = to_mock_vcs(
            [
                f"testing {IDENTIFIER}1",
                f"testing {IDENTIFIER}2",
                f"testing {IDENTIFIER}123",
                f"testing {IDENTIFIER}12",
            ]
        )
        channels = [*channels_1, *channels_2]
        expected_result = {
            "dynamic ": dict(zip((1, 2, 123, 12), channels_1)),
            "testing ": dict(zip((1, 2, 123, 12), channels_2)),
        }
        result = _group_dynamic_channel(channels)
        self.maxDiff = None
        self.assertEqual(result, expected_result)


class MockVoiceChannel(discord.VoiceChannel):
    def __init__(self, name: str):
        self.name: str = name
