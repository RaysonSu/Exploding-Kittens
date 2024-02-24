from __future__ import annotations

from display import Display
from threading import Thread

import time


class Textbox:
    def __init__(self,
                 text: str = "",
                 location: tuple[int, int] = (0, 0),
                 hidden: bool = False,
                 size: tuple[int, int] = (1, 1),
                 alignment: str = "tl",
                 priority: int = 0) -> None:

        self._alignment: str = alignment
        self._hidden: bool = hidden
        self._location: tuple[int, int] = location
        self._priority: int = priority
        self._text: str = text

        self._width: int
        self._height: int
        self._width, self._height = size

    def update_visibility(self, visiblilty: bool) -> None:
        self._hidden = not visiblilty

    def update_text(self, text: str) -> None:
        self._text = text

    def append_text(self, text: str) -> None:
        self._text += text

    def delete_line(self, lines: int = 1) -> None:
        self._text = "".join(self._text.splitlines(True)[:-lines])

    def update_location(self, location: tuple[int, int]) -> None:
        self._location = location

    def move(self, amount: tuple[int, int]) -> None:
        self._location = (self._location[0] + amount[0],
                          self._location[1] + amount[1])

    def resize(self, size: tuple[int, int]) -> None:
        self._width, self._height = size

    def realign(self, alignment: str) -> None:
        self._alignment = alignment

    def display_text(self, display: Display) -> None:
        if self._hidden:
            return

        pattern: list[str] = [""]
        for char in self._text:
            if char == "\n":
                pattern[-1] += " " * (self._width - len(pattern[-1]))
                pattern.append("")
                continue

            if len(pattern[-1]) == self._width:
                pattern.append("")

            pattern[-1] += char

        pattern = pattern[-self._height:]

        display.draw_pattern("\n".join(pattern), self._location,
                             self._alignment)


class TextDisplay:

    def __init__(self,
                 width: int = 80,
                 height: int = 24,
                 fps: float = 10.0) -> None:
        self._display: Display = Display(width, height, fps)
        self._textboxes: dict[str, Textbox] = {}
        self._update_rate: float = 1 / fps
        self._active: bool = True
        self._update_thread: Thread = Thread(target=self._update_display)
        self._update_thread.start()

    def _update_display(self) -> None:
        while self._active:
            self._display.clear()
            textboxes: list[Textbox] = list(self._textboxes.values())
            textboxes.sort(key=lambda box: box._priority)
            for textbox in textboxes:
                textbox.display_text(self._display)
            time.sleep(self._update_rate)

    def force_display_update(self) -> None:
        self._display.clear()
        textboxes: list[Textbox] = list(self._textboxes.values())
        textboxes.sort(key=lambda box: box._priority)
        for textbox in textboxes:
            textbox.display_text(self._display)
        self._display.force_display_update()

    def add_textbox(self, name: str, textbox: Textbox) -> None:
        if name in self._textboxes:
            raise ValueError(f"{repr(name)} already taken as a textbox name.")

        self._textboxes[name] = textbox

    def delete_textbox(self, name: str) -> None:
        if name not in self._textboxes:
            raise ValueError(f"{repr(name)} is not a textbox name.")

        del self._textboxes[name]

    def get_textbox(self, name: str) -> Textbox:
        return self._textboxes[name]

    def read_input(self, location: tuple[int, int], promopt: str = "") -> str:
        box_name: str = 'prompt'
        while True:
            try:
                self.add_textbox(box_name, Textbox(
                    text=promopt,
                    location=location,
                    size=(len(promopt), 1)))
                break
            except ValueError:
                box_name += "i"

        self.force_display_update()
        ret: str = self._display.read_input(
            (location[0] + len(promopt), location[1]))
        self.delete_textbox(box_name)
        return ret

    def close(self) -> None:
        self._active = False
        self._update_thread.join()
        self._display.close()
