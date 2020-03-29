from abc import ABC, abstractmethod


class Observer(ABC):

    @abstractmethod
    def update(self, observable):
        pass


class Observable(ABC):
    """ Simple implementation of Observable. Not synchronized! """

    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def delete_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self)
