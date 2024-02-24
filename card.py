from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game import Game
    from player import Player

from deck import Deck
from random import choice

import abc


class Card(metaclass=abc.ABCMeta):
    def __init__(self, owner: Player | Deck) -> None:
        self._owner: Player | Deck = owner
        self.name: str
        pass

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, str):
            return self.name == __value

        if not isinstance(__value, type(self)):
            return False

        return self.name == __value.name

    def owner(self) -> Player | Deck:
        '''Returns the player / deck that contains this card'''
        return self._owner

    def transfer_ownership(self, new_owner: Player | Deck) -> None:
        '''Transfers ownership to the player / deck specified'''
        self._owner = new_owner

    def nope_check(self) -> tuple[bool, Player]:
        '''Checks if a player wants to nope this card, returns a tuple containing if the card in noped, and the player noping'''
        options: list[Player] = []
        game: Game = self._owner.owner()

        if isinstance(self._owner, Deck):
            raise ValueError("Cards in deck can't be noped")
        
        current_player: int = game.players.index(self._owner)
        
        for player_index, player in enumerate(game.players):
            if player is self._owner:
                continue

            if not player.is_alive:
                continue

            game.swap_active(player_index)

            question: str = f"{self._owner.name} just played a {self.name}. Would you like to use a nope? "
            chosen: str = ""
            valid: list[str]

            if player.card_count('Nope') >= 1:
                question += "[y/n] > "
                valid = ["y", "n"]
            else:
                question += "[n] > "
                valid = ["n"]

            while chosen not in valid:
                chosen = game.ask_question(question)

            if chosen == "y":
                options.append(player)
        
        game.swap_active(current_player)

        if options == []:
            return (False, self._owner)

        chosen_player: Player = choice(options)
        nope: Card = chosen_player.get_card("Nope")

        noped: bool
        noper: Player
        
        chosen_player.remove_card(nope)
        noped, noper = nope.nope_check()
        game.discard_pile.add_card(nope)
        nope.transfer_ownership(game.discard_pile)

        if noped:
            game.add_activity(f"{chosen_player.name} tried to nope {self._owner.name}'s card, but {noper.name} noped that!\n")
            return (False, chosen_player)
        
        return (True, chosen_player)

    def discard(self) -> None:
        if isinstance(self._owner, Deck):
            raise NotImplementedError("Discarding from deck not implemented")

        player: Player = self._owner
        discard_pile: Deck = player.owner().discard_pile

        player.remove_card(self)
        discard_pile.add_card(self)
        self.transfer_ownership(discard_pile)

    @abc.abstractmethod
    def can_play(self) -> bool:
        if isinstance(self._owner, Deck):
            return False

        return self._owner.card_count(self) >= 1

    @abc.abstractmethod
    def on_play(self) -> bool:
        '''Plays the card, and returns if it was succesful or not.'''
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards")

        self._owner.remove_card(self)
        self._owner.owner().add_activity(f"{self._owner.name.capitalize()} played a {self.name}")
        return True

    @abc.abstractmethod
    def on_draw(self) -> None:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards")
