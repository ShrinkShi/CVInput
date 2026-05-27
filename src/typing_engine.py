import time

from pynput.keyboard import Controller, Key

from .constants import (
    DEFAULT_NEWLINE_SHIFT_ENTER_METHOD,
    NEWLINE_METHOD_AUTO,
    NEWLINE_METHOD_KEYBOARD,
    NEWLINE_METHOD_PYNPUT,
    NEWLINE_METHOD_PYAUTOGUI,
    NEWLINE_METHOD_WIN32_SCAN,
    NEWLINE_METHOD_WIN32_VK,
)
from .debug_logger import debug_log
from .win_input import (
    SCAN_LSHIFT,
    SCAN_RETURN,
    VK_LSHIFT,
    VK_RETURN,
    is_available as win32_input_available,
    send_key_event,
    send_scan_event,
)


class TypingEngine:
    KEY_COMBINATION_DELAY = 0.01
    WIN32_SHIFT_PREHOLD_DELAY = 0.08
    WIN32_ENTER_HOLD_DELAY = 0.03
    WIN32_SHIFT_POSTHOLD_DELAY = 0.18

    def __init__(self):
        self.controller = Controller()

    def type_text(
        self,
        text,
        interval,
        stop_event,
        release_keys,
        newline_with_shift_enter=True,
        newline_shift_enter_method=DEFAULT_NEWLINE_SHIFT_ENTER_METHOD,
        on_progress=None,
        input_source="unknown",
    ):
        self._release_trigger_keys(release_keys)
        time.sleep(0.05)
        total = len(text)
        done = 0
        for index, char in enumerate(text):
            if stop_event.is_set():
                break
            if char == "\n":
                resolved_method = self.resolve_newline_method(newline_shift_enter_method)
                debug_log(
                    "NEWLINE_BEHAVIOR",
                    "newline_detected",
                    index=index,
                    input_source=input_source,
                    newline_with_shift_enter=bool(newline_with_shift_enter),
                    strategy="SHIFT_ENTER" if newline_with_shift_enter else "ENTER",
                    method=newline_shift_enter_method if newline_with_shift_enter else "pynput",
                    resolved_method=resolved_method if newline_with_shift_enter else "pynput",
                )
                # Message editors often submit on Enter; this setting types a real Shift+Enter newline instead.
                self.type_newline(
                    newline_with_shift_enter,
                    newline_shift_enter_method,
                    index=index,
                    input_source=input_source,
                )
            elif char == "\t":
                self.controller.press(Key.tab)
                self.controller.release(Key.tab)
            else:
                self.controller.type(char)
            done += 1
            if on_progress:
                on_progress(done, total)
            time.sleep(interval)

    def type_newline(
        self,
        newline_with_shift_enter,
        newline_shift_enter_method=DEFAULT_NEWLINE_SHIFT_ENTER_METHOD,
        index=None,
        input_source="unknown",
    ):
        resolved_method = self.resolve_newline_method(newline_shift_enter_method) if newline_with_shift_enter else NEWLINE_METHOD_PYNPUT
        debug_log(
            "NEWLINE_BEHAVIOR",
            "newline_key_sequence_start",
            index=index,
            input_source=input_source,
            strategy="SHIFT_ENTER" if newline_with_shift_enter else "ENTER",
            method=newline_shift_enter_method if newline_with_shift_enter else "pynput",
            resolved_method=resolved_method,
        )
        if not newline_with_shift_enter:
            try:
                debug_log("NEWLINE_BEHAVIOR", "enter_press", index=index, input_source=input_source)
                self.controller.press(Key.enter)
                debug_log("NEWLINE_BEHAVIOR", "enter_release", index=index, input_source=input_source)
                self.controller.release(Key.enter)
                debug_log("NEWLINE_BEHAVIOR", "newline_key_sequence_end", index=index, input_source=input_source)
            except Exception as e:
                debug_log("NEWLINE_BEHAVIOR", "newline_key_sequence_error", index=index, input_source=input_source, error=str(e))
                raise
            return

        if resolved_method == NEWLINE_METHOD_WIN32_SCAN and win32_input_available():
            self._type_shift_enter_win32_scan(index, input_source)
            return

        if resolved_method == NEWLINE_METHOD_WIN32_VK and win32_input_available():
            self._type_shift_enter_win32_vk(index, input_source)
            return

        if resolved_method == NEWLINE_METHOD_PYAUTOGUI:
            self._type_shift_enter_pyautogui(index, input_source)
            return

        if resolved_method == NEWLINE_METHOD_KEYBOARD:
            self._type_shift_enter_keyboard(index, input_source)
            return

        if resolved_method in (NEWLINE_METHOD_WIN32_SCAN, NEWLINE_METHOD_WIN32_VK):
            debug_log(
                "NEWLINE_BEHAVIOR",
                "sendinput_unavailable_fallback",
                index=index,
                input_source=input_source,
                requested_method=newline_shift_enter_method,
                resolved_method=resolved_method,
                fallback="pynput",
            )
        self._type_shift_enter_pynput(index, input_source)

    def resolve_newline_method(self, method):
        if method == NEWLINE_METHOD_AUTO:
            return NEWLINE_METHOD_PYAUTOGUI
        return method

    def _type_shift_enter_pynput(self, index, input_source):
        shift_pressed = False
        enter_pressed = False
        try:
            debug_log("NEWLINE_BEHAVIOR", "shift_press", index=index, input_source=input_source, method="pynput")
            self.controller.press(Key.shift)
            shift_pressed = True
            time.sleep(self.KEY_COMBINATION_DELAY)
            debug_log("NEWLINE_BEHAVIOR", "enter_press", index=index, input_source=input_source, method="pynput")
            self.controller.press(Key.enter)
            enter_pressed = True
            debug_log("NEWLINE_BEHAVIOR", "enter_release", index=index, input_source=input_source, method="pynput")
            self.controller.release(Key.enter)
            enter_pressed = False
            time.sleep(self.KEY_COMBINATION_DELAY)
            debug_log("NEWLINE_BEHAVIOR", "newline_key_sequence_end", index=index, input_source=input_source, method="pynput")
        except Exception as e:
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_key_sequence_error",
                index=index,
                input_source=input_source,
                method="pynput",
                error=str(e),
            )
            raise
        finally:
            if enter_pressed:
                debug_log(
                    "NEWLINE_BEHAVIOR",
                    "enter_release_finally",
                    index=index,
                    input_source=input_source,
                    method="pynput",
                )
                self._release_key_safely(Key.enter)
            if shift_pressed:
                debug_log("NEWLINE_BEHAVIOR", "shift_release", index=index, input_source=input_source, method="pynput")
                self._release_key_safely(Key.shift)

    def _type_shift_enter_win32_vk(self, index, input_source):
        method = "win32_vk"
        shift_pressed = False
        enter_pressed = False
        try:
            sent, last_error = send_key_event(VK_LSHIFT)
            self._log_sendinput_action("shift_press", index, input_source, method, sent, last_error)
            shift_pressed = True
            time.sleep(self.WIN32_SHIFT_PREHOLD_DELAY)
            sent, last_error = send_key_event(VK_RETURN)
            self._log_sendinput_action("enter_press", index, input_source, method, sent, last_error)
            enter_pressed = True
            time.sleep(self.WIN32_ENTER_HOLD_DELAY)
            sent, last_error = send_key_event(VK_RETURN, key_up=True)
            self._log_sendinput_action("enter_release", index, input_source, method, sent, last_error)
            enter_pressed = False
            time.sleep(self.WIN32_SHIFT_POSTHOLD_DELAY)
            sent, last_error = send_key_event(VK_LSHIFT, key_up=True)
            self._log_sendinput_action("shift_release", index, input_source, method, sent, last_error)
            shift_pressed = False
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_key_sequence_end",
                index=index,
                input_source=input_source,
                method=method,
                shift_prehold_ms=int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
                shift_posthold_ms=int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
            )
        except Exception as e:
            error_data = self._sendinput_error_data(e)
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_key_sequence_error",
                index=index,
                input_source=input_source,
                method=method,
                **error_data,
            )
            raise
        finally:
            if enter_pressed or shift_pressed:
                self._release_win32_vk_shift_enter_safely(index, input_source)

    def _type_shift_enter_win32_scan(self, index, input_source):
        method = "win32_scan"
        shift_pressed = False
        enter_pressed = False
        try:
            sent, last_error = send_scan_event(SCAN_LSHIFT)
            self._log_sendinput_action("shift_press", index, input_source, method, sent, last_error)
            shift_pressed = True
            time.sleep(self.WIN32_SHIFT_PREHOLD_DELAY)
            sent, last_error = send_scan_event(SCAN_RETURN)
            self._log_sendinput_action("enter_press", index, input_source, method, sent, last_error)
            enter_pressed = True
            time.sleep(self.WIN32_ENTER_HOLD_DELAY)
            sent, last_error = send_scan_event(SCAN_RETURN, key_up=True)
            self._log_sendinput_action("enter_release", index, input_source, method, sent, last_error)
            enter_pressed = False
            time.sleep(self.WIN32_SHIFT_POSTHOLD_DELAY)
            sent, last_error = send_scan_event(SCAN_LSHIFT, key_up=True)
            self._log_sendinput_action("shift_release", index, input_source, method, sent, last_error)
            shift_pressed = False
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_key_sequence_end",
                index=index,
                input_source=input_source,
                method=method,
                shift_prehold_ms=int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
                shift_posthold_ms=int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
            )
        except Exception as e:
            error_data = self._sendinput_error_data(e)
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_key_sequence_error",
                index=index,
                input_source=input_source,
                method=method,
                **error_data,
            )
            raise
        finally:
            if enter_pressed or shift_pressed:
                self._release_win32_scan_shift_enter_safely(index, input_source)

    def _type_shift_enter_pyautogui(self, index, input_source):
        method = "pyautogui"
        try:
            import pyautogui
        except ImportError as e:
            self._log_library_unavailable(index, input_source, method, e)
            raise RuntimeError("pyautogui is not installed; install requirements.txt before using this newline method") from e

        shift_pressed = False
        enter_pressed = False
        try:
            pyautogui.keyDown("shift")
            self._log_library_action("shift_press", index, input_source, method)
            shift_pressed = True
            time.sleep(self.WIN32_SHIFT_PREHOLD_DELAY)
            pyautogui.keyDown("enter")
            self._log_library_action("enter_press", index, input_source, method)
            enter_pressed = True
            time.sleep(self.WIN32_ENTER_HOLD_DELAY)
            pyautogui.keyUp("enter")
            self._log_library_action("enter_release", index, input_source, method)
            enter_pressed = False
            time.sleep(self.WIN32_SHIFT_POSTHOLD_DELAY)
            pyautogui.keyUp("shift")
            self._log_library_action("shift_release", index, input_source, method)
            shift_pressed = False
            self._log_library_action("newline_key_sequence_end", index, input_source, method)
        except Exception as e:
            self._log_library_error(index, input_source, method, e)
            raise
        finally:
            if enter_pressed:
                self._release_library_key_safely(pyautogui.keyUp, "enter", index, input_source, method)
            if shift_pressed:
                self._release_library_key_safely(pyautogui.keyUp, "shift", index, input_source, method)

    def _type_shift_enter_keyboard(self, index, input_source):
        method = "keyboard"
        try:
            import keyboard as keyboard_lib
        except ImportError as e:
            self._log_library_unavailable(index, input_source, method, e)
            raise RuntimeError("keyboard is not installed; install requirements.txt before using this newline method") from e

        shift_pressed = False
        enter_pressed = False
        try:
            keyboard_lib.press("shift")
            self._log_library_action("shift_press", index, input_source, method)
            shift_pressed = True
            time.sleep(self.WIN32_SHIFT_PREHOLD_DELAY)
            keyboard_lib.press("enter")
            self._log_library_action("enter_press", index, input_source, method)
            enter_pressed = True
            time.sleep(self.WIN32_ENTER_HOLD_DELAY)
            keyboard_lib.release("enter")
            self._log_library_action("enter_release", index, input_source, method)
            enter_pressed = False
            time.sleep(self.WIN32_SHIFT_POSTHOLD_DELAY)
            keyboard_lib.release("shift")
            self._log_library_action("shift_release", index, input_source, method)
            shift_pressed = False
            self._log_library_action("newline_key_sequence_end", index, input_source, method)
        except Exception as e:
            self._log_library_error(index, input_source, method, e)
            raise
        finally:
            if enter_pressed:
                self._release_library_key_safely(keyboard_lib.release, "enter", index, input_source, method)
            if shift_pressed:
                self._release_library_key_safely(keyboard_lib.release, "shift", index, input_source, method)

    def _log_sendinput_action(self, event_name, index, input_source, method, sent, last_error):
        debug_log(
            "NEWLINE_BEHAVIOR",
            event_name,
            index=index,
            input_source=input_source,
            method=method,
            sendinput_return=sent,
            sendinput_sent=sent,
            get_last_error=last_error,
            shift_prehold_ms=int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
            shift_posthold_ms=int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
        )

    def _log_library_action(self, event_name, index, input_source, method):
        debug_log(
            "NEWLINE_BEHAVIOR",
            event_name,
            index=index,
            input_source=input_source,
            method=method,
            sendinput_return=None,
            get_last_error=None,
            shift_prehold_ms=int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
            shift_posthold_ms=int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
        )

    def _log_library_unavailable(self, index, input_source, method, error):
        debug_log(
            "NEWLINE_BEHAVIOR",
            "newline_method_unavailable",
            index=index,
            input_source=input_source,
            method=method,
            error=str(error),
        )

    def _log_library_error(self, index, input_source, method, error):
        debug_log(
            "NEWLINE_BEHAVIOR",
            "newline_key_sequence_error",
            index=index,
            input_source=input_source,
            method=method,
            error=str(error),
            shift_prehold_ms=int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
            shift_posthold_ms=int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
        )

    def _release_library_key_safely(self, release_key, key, index, input_source, method):
        try:
            release_key(key)
        except Exception as e:
            debug_log(
                "NEWLINE_BEHAVIOR",
                "newline_release_cleanup_failed",
                index=index,
                input_source=input_source,
                method=method,
                key=key,
                error=str(e),
            )

    def _sendinput_error_data(self, error):
        data = {
            "error": str(error),
            "shift_prehold_ms": int(self.WIN32_SHIFT_PREHOLD_DELAY * 1000),
            "shift_posthold_ms": int(self.WIN32_SHIFT_POSTHOLD_DELAY * 1000),
        }
        if hasattr(error, "sent"):
            data["sendinput_return"] = error.sent
            data["sendinput_sent"] = error.sent
        if hasattr(error, "last_error"):
            data["get_last_error"] = error.last_error
        if hasattr(error, "expected"):
            data["sendinput_expected"] = error.expected
        return data

    def _release_win32_vk_shift_enter_safely(self, index, input_source):
        try:
            send_key_event(VK_RETURN, key_up=True)
            send_key_event(VK_LSHIFT, key_up=True)
        except Exception:
            debug_log("NEWLINE_BEHAVIOR", "win32_vk_release_cleanup_failed", index=index, input_source=input_source)

    def _release_win32_scan_shift_enter_safely(self, index, input_source):
        try:
            send_scan_event(SCAN_RETURN, key_up=True)
            send_scan_event(SCAN_LSHIFT, key_up=True)
        except Exception:
            debug_log("NEWLINE_BEHAVIOR", "win32_scan_release_cleanup_failed", index=index, input_source=input_source)

    def _release_trigger_keys(self, release_keys):
        for key in release_keys:
            self._release_key_safely(key)

    def _release_key_safely(self, key):
        try:
            self.controller.release(key)
        except Exception:
            pass
