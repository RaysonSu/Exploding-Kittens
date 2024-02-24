from __future__ import annotations

from cards import *
from deck import Deck
from player import Player
from textdisplay import TextDisplay, Textbox
from threading import Thread

import time

class Game:
    def __init__(self) -> None:
        self._display_thread: Thread = Thread(target=self._update_display)
        self._names: list[str] = []
        self._player_order: list[int] = []
        self._ui_textboxes: dict[str, Textbox] = {}

        self.active_player: Player | None = None
        self.alive: bool = True
        self.deck: Deck = Deck(self)
        self.discard_pile: Deck = Deck(self)
        self.display_handler: TextDisplay = TextDisplay(fps=15, width=120, height=36)
        self.players: list[Player] = []

        self._ui_textboxes["active"] = Textbox(location=(0, 0), size=(89, 1))
        self._ui_textboxes["activity"] = Textbox(location=(0, 18), size=(89, 9))
        self._ui_textboxes["deck_status"] = Textbox(location=(0, 9), size=(89, 1))
        self._ui_textboxes["discard_status"] = Textbox(location=(90, 0), size=(30, 18))
        self._ui_textboxes["player_status"] = Textbox(location=(0, 2), size=(89, 6))

        self._initialize_textboxes()
        self._display_thread.start()

        time.sleep(0.1)

        self.play()
    
    def _initialize_textboxes(self) -> None:
        for name, textbox in self._ui_textboxes.items():
            self.display_handler.add_textbox(
                "game" + "_" + name, 
                textbox)
    
    def _update_display(self) -> None:
        while self.alive:
            if self.active_player:
                self._ui_textboxes["active"].update_text(f"Active player: {self.active_player.name}")
                self._ui_textboxes["deck_status"].update_text(f"Card(s) remaining: {self.deck.size()}")
                self._ui_textboxes["discard_status"].update_text(self._format_discard_pile())
                self._ui_textboxes["player_status"].update_text(self._format_player_status())

            time.sleep(0.05)
    
    def _format_discard_pile(self) -> str:
        text: str = "Discard pile:\n"
        for card, amount in self.discard_pile.card_status():
            text += f"{card} x {amount}\n"
        
        return text
    
    def _format_player_status(self) -> str:
        text: str = ""
        for player in self.players:
            text += player.name + ": "
            if player.is_alive:
                text += "alive, "
                text += f"has {player.hand_size()} card(s)"
            else:
                text += "dead :("
            text += "\n"
        
        return text
    
    def _initialize_players(self) -> None:
        player_count: int = 0
        while player_count == 0:
            answer: str = self.ask_question("How many players? > ")
            if answer not in ["2", "3", "4", "5"]:
                continue
            
            player_count = int(answer)
        
        for i in range(player_count):
            while True:
                try:
                    self.add_player(self.ask_question(f"Player {i + 1}, what's your name? > "))
                    break
                except ValueError as _:
                    pass

    
    def _initialize_cards(self) -> None:
        for player in self.players:
            player.receive_card(Defuse(player))
        
        deck: list[tuple[type[Card] | str, int]] = [
            (Attack, 4),
            (Favor, 4),
            (Nope, 5),
            (Shuffle, 4),
            (Skip, 4),
            (SeeTheFuture, 4),
            ("Tacocat", 4),
            ("Watermeloncat", 4),
            ("Potatocat", 4),
            ("Beardcat", 4)
        ]

        for card_type, amount in deck:
            for _ in range(amount):
                if isinstance(card_type, str):
                    self.deck.add_card(Cat(self.deck, card_type))
                else:
                    self.deck.add_card(card_type(self.deck))
        
        self.deck.shuffle()
        
        for player in self.players:
            for _ in range(7):
                self.deck.draw_card(player, False)
        
        players: int = len(self.players)
        extra_defuses: int
        if players == 2:
            extra_defuses = 2
        else:
            extra_defuses = 6 - players
        
        for _ in range(extra_defuses):
            self.deck.add_card(Defuse(self.deck))
        
        for _ in range(players - 1):
            self.deck.add_card(Kitten(self.deck))

        self.deck.shuffle()
        
        assert self.active_player
        self.swap_active(self.active_player, True)
        for player in self.players:
            player.show_hand = True

    def play(self) -> None:
        self._initialize_players()
        self._initialize_cards()

        while self.players_alive() > 1:
            assert self.active_player
            self.active_player.take_turn()
            self.swap_active(self.next_player())
        
        for player in self.players:
            if player.is_alive:
                self.add_activity(f"{player.name} wins!")
        
        self.close()

    def close(self) -> None:
        time.sleep(0.2)
        self.display_handler.close()
        self.alive = False

    def add_player(self, name: str) -> Player:
        if name in self._names:
            raise ValueError("Name already taken")
        self._names.append(name)
        new_player: Player = Player(name, self)
        self._player_order.append(len(self._player_order))
        self.players.append(new_player)

        if not self.active_player:
            self.active_player = new_player

        return new_player
    
    def next_player(self) -> Player:
        if not self.active_player:
            return self.players[0]
        
        total_players: int = len(self.players)
        index: int = self.players.index(self.active_player) + 1
        index %= total_players

        while not self.players[index].is_alive:
            index += 1
            index %= total_players

        return self.players[index]

    def is_player(self, name: str) -> bool:
        for player in self.players:
            if player.name == name:
                return True

        return False
    
    def get_player(self, name: str) -> Player:
        for player in self.players:
            if player.name == name:
                return player
        
        raise ValueError(f"{name} is not a player")

    def swap_active(self, target: int | Player, force_question: bool = False) -> bool:
        if isinstance(target, Player):
            if not target.is_alive:
                raise ValueError(f"Can't swap to a dead player.")

            return self.swap_active(self.players.index(target), force_question)

        if target not in self._player_order:
            raise ValueError(f"Unexpected Player: {target}")

        if not self.players[target].is_alive:
            return False

        if self.players[target] == self.active_player and not force_question:
            return True

        self.active_player = None
        self.ask_question(f"Swap to {self.players[target].name}. > ")
        self.active_player = self.players[target]

        return True

    def ask_question(self, question: str, location: tuple[int, int] = (0, 35)) -> str:
        time.sleep(0.1)
        self.display_handler.force_display_update()
        return self.display_handler.read_input(location, question)
    
    def add_activity(self, text: str | list[str]) -> None:
        if isinstance(text, list):
            for line in text:
                self.add_activity(line)
            return
        
        self._ui_textboxes["activity"].append_text(text)
    
    def players_alive(self) -> int:
        ret: int = 0
        for player in self.players:
            if player.is_alive:
                ret += 1
        
        return ret
    
    # def integrity_check(self) -> None:
    #     for player in self.players:
    #         for card in player._hand:
    #             assert card._owner == player
        
    #     for card in self.deck._cards:
    #         assert card._owner == self.deck
        
    #     for card in self.discard_pile._cards:
    #         assert card._owner == self.discard_pile
