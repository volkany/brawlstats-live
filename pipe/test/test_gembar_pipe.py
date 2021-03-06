#!/usr/bin/env python3
from state.enum.screen import Screen
from state.game_state import GameState
from state.stream_config import StreamConfig
from pipe.gembar_pipe import GembarPipe

stream_config = StreamConfig(resolution=480,
                             max_fps=0,
                             screen_box=((0, 0), (852, 480)))

def test_should_set_state():
    state = GameState(stream_config=stream_config,
                      screen=Screen.GEMGRAB_INGAME)
    pipe = GembarPipe()
    pipe._matcher_blue.classify = lambda *_: 0.28
    pipe._matcher_red.classify = lambda *_: 0.5

    changes = pipe.process(None, state)
    assert changes == {
        "blue_gems": 3,
        "red_gems": 5,
    }


def test_should_reset_state():
    state = GameState(stream_config=stream_config,
                      screen=Screen.PLAY_AGAIN)
    pipe = GembarPipe()
    changes = pipe.process(None, state)
    assert changes == {
        "blue_gems": 0,
        "red_gems": 0,
    }


def test_should_ignore_wrong_screen():
    state = GameState(stream_config=stream_config,
                      screen=Screen.MAIN_MENU)
    pipe = GembarPipe()

    changes = pipe.process(None, state)
    assert changes == {}


def test_should_ignore_failing_match():
    state = GameState(stream_config=stream_config,
                      screen=Screen.GEMGRAB_INGAME)
    pipe = GembarPipe()
    pipe._matcher_blue.classify = lambda *_: None
    pipe._matcher_red.classify = lambda *_: None

    changes = pipe.process(None, state)
    assert changes == {}