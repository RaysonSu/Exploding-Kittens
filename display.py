from __future__ import annotations

from threading import Thread
import time
import os


class Display:
    def __init__(self, width: int = 80, height: int = 24, fps: float = 10.0) -> None:
        self._grid: list[str] = [" " * width for _ in range(height)]
        self._cols: int = width
        self._rows: int = height
        self._diplay_thread: Thread = Thread(target=self._update_display)
        self._update_rate: float = 1 / fps
        self._alive: bool = True
        self._paused: bool = False
        self._rendering: bool = False

        self._diplay_thread.start()

        columns: int
        lines: int
        columns, lines = self._terminal_size()

        while columns != width or lines != height:
            self._wait_until_not_rendering()
            self._paused = True
            self.clear()
            self.make_border()
            self.write_string_horizontal(
                f"Incorrect terminal size: {columns}x{lines}, expected: {width}x{height}",
                (self._cols // 2, self._rows // 2),
                "c"
            )
            self._paused = False
            time.sleep(self._update_rate)
            columns, lines = self._terminal_size()

        self._clear_screen()
        self.clear()

    @staticmethod
    def _terminal_size() -> tuple[int, int]:
        size: os.terminal_size = os.get_terminal_size()
        return size.columns, size.lines

    def _update_display(self) -> None:
        while self._alive:
            time.sleep(self._update_rate)
            if self._paused:
                continue

            self._rendering = True
            self._clear_screen()
            print("\n".join([row[:self._cols]
                  for row in self._grid[:self._rows]]), end="")
            self._rendering = False

    def force_display_update(self) -> None:
        self._clear_screen()
        print("\n".join([row[:self._cols]
                         for row in self._grid[:self._rows]]), end="")

    def _print_with_line_clear(self, string: str):
        width = os.get_terminal_size().columns
        if len(string) > width:
            string = string[:width - 3] + "..."
        print("\r" + " " * width + "\r" + string, end="")

    def _clear_screen(self) -> None:
        print("\033[H\033[3J", end="")

    def _wait_until_not_rendering(self) -> None:
        while self._rendering:
            pass

    def _wait_until_rendered(self) -> None:
        prev_state: bool = self._rendering
        while prev_state and not self._rendering:
            prev_state = self._rendering

    def clear(self) -> None:
        self._grid = [" " * self._cols for _ in range(self._rows)]
        return

    def write_string_horizontal(self, string: str, location: tuple[int, int], alignment: str = "l") -> None:
        self._wait_until_not_rendering()
        if alignment not in ["l", "c", "r"]:
            self.close()
            raise ValueError(
                f"Horizontal alignment not supported: {repr(alignment)}")

        col: int
        row: int
        col, row = location

        if alignment == "c":
            col -= len(string) // 2
        elif alignment == "r":
            col -= len(string)

        if row >= self._rows:
            return

        ending: int = col + len(string)
        extra_chars: int = max(0, ending - self._cols)

        if col < 0:
            string = string[min(len(string), -col):]
            col = 0

        if extra_chars > 0:
            string = string[:-extra_chars]

        for char_col, char in enumerate(string, col):
            if char == "\x00":
                continue

            self._grid[row] = self._grid[row][:char_col] + \
                char + self._grid[row][char_col + 1:]

    def write_string_vertical(self, string: str, location: tuple[int, int], alignment: str = "t") -> None:
        self._wait_until_not_rendering()
        if alignment not in ["t", "m", "b"]:
            raise ValueError(
                f"Vertical alignment not supported: {repr(alignment)}")

        col: int
        row: int
        col, row = location

        if alignment == "m":
            row -= len(string) // 2
        elif alignment == "b":
            row -= len(string)

        if col >= self._cols:
            return

        ending: int = row + len(string)
        extra_chars: int = max(0, ending - self._rows)

        if extra_chars > 0:
            string = string[:-extra_chars]

        for row_num, char in enumerate(string, row):
            if char == "\x00":
                continue

            self._grid[row_num] = self._grid[row_num][:col] + \
                char + self._grid[row_num][col + 1:]

    def draw_pattern(self, pattern: str, location: tuple[int, int], alignment: str = "tl") -> None:
        if alignment[0] not in "tmb" or alignment[1] not in "lcr" or len(alignment) != 2:
            self.close()
            raise ValueError(
                f"Alignment type not supported: {repr(alignment)}")

        pattern_grid: list = pattern.split("\n")
        width: int = max(map(len, pattern_grid))
        height: int = len(pattern_grid)

        new_location_x: int
        new_location_y: int
        new_location_x, new_location_y = location

        if alignment[0] == "m":
            new_location_y -= height // 2
        elif alignment[0] == "b":
            new_location_y -= height

        if alignment[1] == "c":
            new_location_x -= width // 2
        elif alignment[1] == "r":
            new_location_x -= height

        for y, row in enumerate(pattern_grid, new_location_y):
            self.write_string_horizontal(row, (new_location_x, y))

    def read_input(self, location: tuple[int, int], promopt: str = "") -> str:
        self._paused = True
        time.sleep(self._update_rate)
        self._wait_until_rendered()
        escape = f"\033[{location[1] + 1};{location[0] + 1}H"
        print(escape, end="")
        ret: str = input(promopt)
        self._paused = False

        return ret

    def make_border(self) -> None:
        self.write_string_horizontal("-" * self._cols, (0, 0))
        self.write_string_horizontal("-" * self._cols, (0, self._rows - 1))
        self.write_string_vertical("|" * self._rows, (0, 0))
        self.write_string_vertical("|" * self._rows, (self._cols - 1, 0))
        self.write_string_horizontal("+", (0, 0))
        self.write_string_horizontal("+", (self._cols - 1, 0))
        self.write_string_horizontal("+", (0, self._rows - 1))
        self.write_string_horizontal("+", (self._cols - 1, self._rows - 1))

    def close(self) -> None:
        self._alive = False
        self._diplay_thread.join()
