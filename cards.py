from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from game import Game

from card import Card
from deck import Deck

class Cat(Card):
    def __init__(self, owner: Player | Deck, name: str) -> None:
        super().__init__(owner)
        self.name: str = name

    def can_play(self) -> bool:
        if isinstance(self._owner, Deck):
            return False

        if self._owner.card_count(self) < 2:
            return False
        
        for player in self._owner.owner().players:
            if player == self._owner:
                continue

            if player.hand_size() > 0:
                return True

        return False

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")
        
        game: Game = self._owner.owner()
        owner: Player = self._owner

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            game.add_activity(f"{owner.name} played two {self.name}, but {noper.name} noped it!\n")
            owner.discard_card(self.name)
            owner.discard_card(self.name)
            return False
        
        
        target: str
        target_player: Player
        while True:
            target = game.ask_question("Who would you like to steal from? > ")
            if not game.is_player(target):
                continue
            
            target_player = game.get_player(target)
            if not target_player.is_alive:
                continue

            if target_player.hand_size() == 0:
                continue

            break

        card_stolen: Card = target_player.take_random_card()

        owner.receive_card(card_stolen, False)

        game.add_activity(f"{owner.name} played two {self.name}s, and stole from {target}.\n")
        owner.add_activity(f"You stole a {card_stolen.name} from {target}.\n")
        target_player.add_activity(f"{target} stole a {card_stolen.name} from you.\n")
        owner.discard_card(self.name)
        owner.discard_card(self.name)

        return True

class Favor(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Favor"

    def can_play(self) -> bool:
        if isinstance(self._owner, Deck):
            return False

        for player in self._owner.owner().players:
            if player == self._owner:
                continue

            if player.hand_size() > 0:
                return True

        return False

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")
        
        game: Game = self._owner.owner()

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            game.add_activity(f"{self._owner.name} played a {self.name}, but {noper.name} noped it!\n")
            self.discard()
            return False
        
        
        target: str
        target_player: Player
        while True:
            target = game.ask_question("Who would you like to steal from? > ")
            if not game.is_player(target):
                continue
            
            target_player = game.get_player(target)
            if not target_player.is_alive:
                continue

            if target_player.hand_size() == 0:
                continue

            break
        
        current_player: Player = self._owner
        game.swap_active(target_player)

        card_stolen: Card | None = target_player.choose_card(
            prompt=f"{current_player.name} is asking you a favor, choose a card. > ",
            forced=True,
            playable=False)
        if not card_stolen:
            raise ValueError("Oh crap!, favor's gone wrong :(")
        target_player.remove_card(card_stolen)
        game.swap_active(current_player)

        owner: Player = self._owner
        owner.receive_card(card_stolen, False)

        game.add_activity(f"{self._owner.name} played a {self.name}, and stole from {target}.\n")
        owner.add_activity(f"You stole a {card_stolen.name} from {target}.\n")
        target_player.add_activity(f"{owner.name} stole a {card_stolen.name} from you.\n")
        self.discard()
        return True


class Nope(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Nope"

    def can_play(self) -> bool:
        return False

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        return super().on_play()

class Skip(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Skip"

    def can_play(self) -> bool:
        return True

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, but {noper.name} noped it!\n")
            self.discard()
            return False
        
        self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, and skipped a turn.\n")
        self._owner.turns_left -= 1
        self.discard()
        return True

class Shuffle(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Shuffle"

    def can_play(self) -> bool:
        return True

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, but {noper.name} noped it!\n")
            self.discard()
            return False
        
        self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, and shuffled the deck.\n")
        self._owner.owner().deck.shuffle()
        self.discard()
        return True

class SeeTheFuture(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "See The Future"

    def can_play(self) -> bool:
        return True

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, but {noper.name} noped it!\n")
            self.discard()
            return False
        
        self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}.\n")
        activity_log: str = f"You saw: (top) "
        activity_log += ", ".join([
            f"{order}: {card.name}" 
            for order, card
            in enumerate(self._owner.owner().deck.top_cards(), 1)])
        activity_log += " (bottom)"
        self._owner.add_activity(activity_log + "\n")
        
        self.discard()
        return True

class Attack(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Attack"

    def can_play(self) -> bool:
        return True

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")
        
        owner: Player = self._owner
        game: Game = owner.owner()

        noped: bool
        noper: Player
        noped, noper = self.nope_check()
        if noped:
            game.add_activity(f"{owner.name} played a {self.name}, but {noper.name} noped it!\n")
            self.discard()
            return False
        
        if owner.turns_left == 1:
            owner.turns_left -= 1
        game.add_activity(f"{owner.name} played a {self.name}, forcing {game.next_player().name} to take {self._owner.turns_left + 2} turns.\n")
        game.next_player().turns_left = self._owner.turns_left + 2
        owner.turns_left = 0
        self.discard()
        return True

class Defuse(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Defuse"

    def can_play(self) -> bool:
        return False

    def on_draw(self) -> None:
        return super().on_draw()

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")

        return False

class Kitten(Card):
    def __init__(self, owner: Player | Deck) -> None:
        super().__init__(owner)
        self.name = "Exploding Kitten"

    def can_play(self) -> bool:
        return False

    def on_draw(self) -> None:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't draw cards.")

        game: Game = self._owner.owner()
        owner: Player = self._owner
        deck: Deck = game.deck

        question: str = "Whops, you've exploded, would you like to play a defuse? "
        chosen: str = ""
        valid: list[str]

        if owner.card_count("Defuse") >= 1:
            question += "[y/n] > "
            valid = ["y", "n"]
        else:
            question += "[n] > "
            valid = ["n"]

        while chosen not in valid:
            chosen = game.ask_question(question)

        if chosen == "n":
            game.add_activity(f"{owner.name} drew a kitten and exploded.\n")
            owner.explode()
            return
        
        owner.discard_card("Defuse")
        game.add_activity(f"{owner.name} drew a kitten, but defused it.\n")
        new_location: str = ""
        chosen_location: int
        while True:
            new_location = game.ask_question("Where would you like to place the Kitten? (1 for top, 2 for next etc.) > ")
            if not new_location.isnumeric():
                continue
            
            chosen_location = int(new_location)
            if chosen_location > deck.size() + 1:
                continue
            
            owner.remove_card(self)
            deck.insert_card(self, chosen_location - 1)
            break

    def on_play(self) -> bool:
        if isinstance(self._owner, Deck):
            raise ValueError("Decks can't play cards!")

        return False


# class Foo(Card):
#     def __init__(self, owner: Player | Deck) -> None:
#         super().__init__(owner)
#         self.name = "Foo"

#     def can_play(self) -> bool:
#         return True

#     def on_draw(self) -> None:
#         return super().on_draw()

#     def on_play(self) -> bool:
#         if isinstance(self._owner, Deck):
#             raise ValueError("Decks can't play cards!")

#         noped: bool
#         noper: Player
#         noped, noper = self.nope_check()
#         if noped:
#             self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}, but {noper.name} noped it!\n")
#             self.discard()
#             return False
        
#         self._owner.owner().add_activity(f"{self._owner.name} played a {self.name}.\n")
#         self.discard()
#         return True
