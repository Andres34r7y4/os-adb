"""
===============================================================================
OS-ADB: Architecture Decision Buffer
Author: Andrés Delgado
GitHub: https://github.com/Andres34r7y4
LinkedIn: https://www.linkedin.com/in/andresdelgado-architect/
Architecture: Strict Layered Pattern (Domain -> Engine -> Adapters -> UI)
===============================================================================
"""
import asyncio
from pathlib import Path

from ui.buffer_screen import BufferScreen
from ui.dialogs import AddDecisionScreen, ConfirmDeleteScreen, HelpScreen
from ui.home_screen import HomeScreen
from textual.widgets import Input


def _run(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ADB_DB", str(tmp_path / "tui.db"))


async def _open_buffer(app, pilot):
    await app.push_screen(BufferScreen())
    await pilot.pause()
    assert isinstance(app.screen, BufferScreen)
    return app.screen


def test_tui_mounts_with_empty_state(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            assert isinstance(app.screen, HomeScreen)
            screen = await _open_buffer(app, pilot)
            assert len(screen.decisions) == 0
            assert screen.selected is None

    _run(scenario)


def test_tui_add_modal_validation_and_save(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            screen = await _open_buffer(app, pilot)
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(app.screen, AddDecisionScreen)
            # empty save is rejected, modal stays open
            app.screen.query_one("#btn-save").press()
            await pilot.pause()
            assert isinstance(app.screen, AddDecisionScreen)
            assert len(screen.decisions) == 0
            # valid save persists, closes modal and selects the record
            app.screen.query_one("#f-title", Input).value = "TUI Decision"
            app.screen.query_one("#f-justification", Input).value = "Because tests"
            app.screen.query_one("#btn-save").press()
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)
            assert len(screen.decisions) == 1
            assert screen.selected.title == "TUI Decision"

    _run(scenario)


def test_tui_filter_and_search_shortcut(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            screen = await _open_buffer(app, pilot)
            screen.service.record_decision(title="Alpha One", context="c", justification="j", tag="alpha")
            screen.service.record_decision(title="Beta Two", context="c", justification="j", tag="beta")
            screen.refresh_data()
            assert len(screen.filtered) == 2
            await pilot.press("/")
            await pilot.pause()
            assert app.screen.focused.id == "search-input"
            screen.filter_text = "alpha"
            screen.apply_filter()
            assert len(screen.filtered) == 1
            assert screen.filtered[0].tag == "alpha"
            screen.filter_text = ""
            screen.apply_filter()
            assert len(screen.filtered) == 2

    _run(scenario)


def test_tui_export_action(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)

    async def scenario():
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            screen = await _open_buffer(app, pilot)
            screen.service.record_decision(title="Export Me", context="c", justification="j", tag="demo")
            screen.refresh_data()
            screen.action_export_md()
            content = Path("ADR_LOG.md").read_text(encoding="utf-8")
            assert "Export Me" in content

    _run(scenario)


def test_tui_delete_confirmed_and_cancelled(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            screen = await _open_buffer(app, pilot)
            screen.service.record_decision(title="Keep Me", context="c", justification="j")
            doomed = screen.service.record_decision(title="Delete Me", context="c", justification="j")
            screen.refresh_data()
            screen.select_decision(doomed.id)
            # cancel path: modal opens, Cancel keeps the record
            await pilot.press("d")
            await pilot.pause()
            assert isinstance(app.screen, ConfirmDeleteScreen)
            await pilot.click("#del-no")
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)
            assert screen.service.get_decision(doomed.id) is not None
            # confirm path: record is gone and list refreshes
            screen.select_decision(doomed.id)
            await pilot.press("d")
            await pilot.pause()
            await pilot.click("#del-yes")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)
            assert screen.service.get_decision(doomed.id) is None
            assert len(screen.decisions) == 1

    _run(scenario)


def test_tui_help_opens_and_closes(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.brand import BANNER, SOCIALS, TAGLINE
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            screen = await _open_buffer(app, pilot)
            assert BANNER.strip() and SOCIALS.strip() and TAGLINE.strip()
            await pilot.press("?")
            await pilot.pause()
            assert isinstance(app.screen, HelpScreen)
            # pressing ? again must not stack another help screen
            await pilot.press("?")
            await pilot.pause()
            assert len(app.screen_stack) == 4  # default + home + buffer + help
            # q inside help closes it instead of quitting the app
            await pilot.click("#help-ok")
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)
            # escape in buffer goes back home
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, HomeScreen)

    _run(scenario)


def test_tui_home_minimal_and_start(tmp_path, monkeypatch):
    _isolated_db(tmp_path, monkeypatch)

    async def scenario():
        from ui.brand import BANNER, SOCIALS, TAGLINE
        from ui.tui_app import ADBTuiApp

        app = ADBTuiApp()
        async with app.run_test() as pilot:
            assert isinstance(app.screen, HomeScreen)
            assert BANNER.strip() in str(app.screen.query_one(".home-logo").render())
            assert SOCIALS.strip() in str(app.screen.query_one(".home-socials").render())
            assert TAGLINE.strip() in str(app.screen.query_one(".home-tagline").render())
            # Comenzar button opens the buffer, escape returns home
            await pilot.click("#home-start")
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, HomeScreen)
            # keyboard also starts
            await pilot.press("b")
            await pilot.pause()
            assert isinstance(app.screen, BufferScreen)

    _run(scenario)
