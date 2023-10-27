from abc import ABC, abstractmethod

from .models import Session
from .types import StoreContainer, StoreValue


class StateStore(ABC):
    def __init__(self) -> None:
        """
        Create the container.
        """
        self.container: StoreContainer = {}

    @abstractmethod
    def all(self, session: Session) -> list[StoreValue]:
        """
        Get all entries for a session in the container.
        """

    @abstractmethod
    def append(self, session: Session, value: StoreValue) -> None:
        """
        Append an entry for a session to the container.
        """

    @abstractmethod
    def reset(self, session: Session) -> None:
        """
        Reset the container for a session back to empty.
        """


class TimeMemoryStore(StateStore):
    def all(self, session: Session) -> list[StoreValue]:
        domain = session.domain
        if domain not in self.container:
            # Trigger creation of dict for shop
            self.reset(session)
        return self.container[domain]

    def append(self, session: Session, value: StoreValue) -> None:
        domain = session.domain
        if domain not in self.container:
            # Trigger creation of dict for shop
            self.reset(session)
        self.container[domain].append(value)

    def reset(self, session: Session) -> None:
        self.container[session.domain] = []


class CostMemoryStore(StateStore):
    def all(self, session: Session) -> list[StoreValue]:
        domain = session.domain
        if domain not in self.container:
            # Trigger creation of dict for shop
            self.reset(session)
        return self.container[domain]

    def append(self, session: Session, value: StoreValue) -> None:
        domain = session.domain
        if domain not in self.container:
            # Trigger creation of dict for shop
            self.reset(session)
        self.container[domain].append(value)

    def reset(self, session: Session) -> None:
        self.container[session.domain] = []
