from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from card import Card
    from game import Game

from collections import defaultdict
from textdisplay import Textbox
from threading import Thread

import random
import time


class Player:
    def __init__(self, name: str, owner: Game) -> None:
        self._display_thread: Thread = Thread(target=self._update_display)
        self._hand: list[Card] = []
        self._owner: Game = owner
        self._ui_textboxes: dict[str, Textbox] = {}

        self.is_alive: bool = True
        self.name: str = name
        self.show_hand: bool = False
        self.turns_left: int = 0

        self._ui_textboxes["activity"] = Textbox(location=(0, 27), hidden=True, size=(89, 8))
        self._ui_textboxes["inventory"] = Textbox(location=(90, 18), hidden=True, size=(30, 17))
        self._ui_textboxes["turns"] = Textbox(location=(0, 10), hidden=True, size=(89, 1))

        self._initialize_textboxes()
        self._display_thread.start()
    
    def _initialize_textboxes(self) -> None:
        for name, textbox in self._ui_textboxes.items():
            self._owner.display_handler.add_textbox(
                self.name + "_" + name, 
                textbox)

    def _update_display(self) -> None:
        '''Display handler for the player textbox'''
        while self._owner.alive:
            if not self.is_alive:
                self._ui_textboxes["activity"].update_text("You are dead. :(")
            
            if self.show_hand:
                self._ui_textboxes["inventory"].update_text(self._format_hand())
            
            self._ui_textboxes["turns"].update_text(f"Card draw(s) remaining: {self.turns_left}")

            self._ui_textboxes["activity"].update_visibility(self.is_active())
            self._ui_textboxes["inventory"].update_visibility(self.is_active())
            self._ui_textboxes["turns"].update_visibility(self.is_active())
            time.sleep(0.05)
    
    def _format_hand(self) -> str:
        counts: defaultdict[str, int] = defaultdict(lambda: 0)
        for card in self._hand:
            counts[card.name] += 1
        
        string: str = "Hand: \n"
        for name, amount in counts.items():
            string += f"{name} x {amount}\n"
        
        return string

    def is_active(self) -> bool:
        try:
            return self._owner.active_player == self
        except AttributeError as _:
            return False

    def owner(self) -> Game:
        '''Returns the game that this player is playing'''
        return self._owner

    def card_count(self, card: Card | str) -> int:
        '''Counts the number of cards in the hand and returns the count'''
        count: int = 0
        for holding in self._hand:
            if card == holding:
                count += 1

        return count

    def take_random_card(self) -> Card:
        '''Removes a random card from the hand and returns the card removed'''
        chosen: Card = random.choice(self._hand)
        self.remove_card(chosen)
        return chosen

    def remove_card(self, card: Card | str) -> None:
        '''Removes a given card from the hand, given an instance of the card or the card name'''
        if isinstance(card, str):
            for index, card_chosen in enumerate(self._hand):
                if card_chosen.name == card:
                    self._hand.pop(index)
                    break
        else:
            for index, card_chosen in enumerate(self._hand):
                if card_chosen.name == card.name:
                    self._hand.pop(index)

    def discard_card(self, card: Card | str) -> None:
        '''Discards a given card from the hand, given an instance of the card or the card name'''
        if isinstance(card, str):
            for hand_card in self._hand:
                if hand_card.name == card:
                    hand_card.discard()
                    return
            
            return

        if card in self._hand:
            card.discard()

    def receive_card(self, card: Card, drawn: bool = True) -> None:
        self._hand.append(card)
        card.transfer_ownership(self)
        if drawn:
            card.on_draw()
            
        return

    def explode(self) -> None:
        self.is_alive = False
        for card in self._hand.copy():
            self.discard_card(card)

    def take_turn(self) -> None:
        self._owner.swap_active(self)
        if self.turns_left == 0:
            self.turns_left += 1
        
        while self.turns_left:
            chosen: str = self._owner.ask_question("[P]lay or [D]raw? > ").lower()
            if chosen not in ["p", "d"]:
                continue

            if chosen == "d":
                self._owner.deck.draw_card(self)
                self._owner.ask_question("> ")
                self.turns_left -= 1
                continue

            played_card: Card | None = self.choose_card(prompt="Which card? > ", playable=True)
            if not played_card:
                continue

            played_card.on_play()
    
    def hand_size(self) -> int:
        return len(self._hand)
    
    def add_activity(self, string: str) -> None:
        self._ui_textboxes["activity"].append_text(string)
    
    def choose_card(self, prompt: str, forced: bool = False, playable: bool = True) -> Card | None:
        options: list[str] = []
        cards: list[Card] = []
        valid_options: list[str] = []
        for card in self._hand:
            if (card.can_play() or not playable) and card not in cards:
                options.append(f"[{len(options) + 1}]. {card.name}")
                valid_options.append(f"{len(options)}")
                cards.append(card)

        if not forced:
            options.append(f"[{len(options) + 1}]. Cancel")
            valid_options.append(f"{len(options)}")

        question: list[str] = ["", "", "", "", "", "", "", ""]
        for index, option in enumerate(options):
            question[index % 8] += option.ljust(20)
        self._ui_textboxes["activity"].append_text("\n".join(question))

        while True:
            option_chosen: str = self._owner.ask_question(prompt)
            if option_chosen not in valid_options:
                continue

            if option_chosen == valid_options[-1] and not forced:
                break

            chosen_card: Card = cards[int(option_chosen) - 1]
            break

        self._ui_textboxes["activity"].delete_line(8)
        try:
            return chosen_card
        except UnboundLocalError as _:
            return None
