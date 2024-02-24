from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from card import Card
    from game import Game
    from player import Player

from collections import defaultdict
from random import shuffle

class Deck:
    def __init__(self, owner: Game) -> None:
        self._cards: list[Card] = []
        self._owner: Game = owner

    def owner(self) -> Game:
        return self._owner

    def shuffle(self) -> None:
        shuffle(self._cards)

    def top_cards(self, amount: int = 3) -> list[Card]:
        return self._cards[:amount]

    def insert_card(self, card: Card, position: int) -> None:
        card.transfer_ownership(self)
        self._cards.insert(position, card)

    def add_card(self, card: Card) -> None:
        card.transfer_ownership(self)
        self._cards.insert(0, card)

    def discard_card(self, card: Card | str) -> bool:
        '''Removes a card from the deck given card name or card instance, returns if card was removed succesfully'''
        if not isinstance(card, str): # to appease circular imports
            try:
                self._cards.remove(card)
                return True
            except ValueError as _:
                return False
        
        for deck_card in self._cards:
            if deck_card.name == card:
                self._cards.remove(deck_card)
                return True
        
        return False

    def draw_card(self, player: Player, log: bool = True) -> None:
        '''Draws a card from the deck, and places it into the player's hand, then logs in players activity if nessary'''
        to_draw: Card = self._cards.pop(0)
        player.receive_card(to_draw)
        if log:
            name: str = to_draw.name
            if name[0].lower() in "aeiou":
                name = "an " + name
            else:
                name = "a " + name
            player.add_activity(f"You drew {name}.\n")

        return

    
    def card_status(self) -> list[tuple[str, int]]:
        counts: defaultdict[str, int] = defaultdict(lambda: 0)
        for card in self._cards:
            counts[card.name] += 1
        
        return [(name, amount) for name, amount in counts.items()]

    def size(self) -> int:
        return len(self._cards)