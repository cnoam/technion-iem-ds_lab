# set and get Message of the Day
# use persistent storage (in host's file system)
import os


class Motd():
    """save and load a string in a file """
    PATH = '/logs'

    def __init__(self):
        self.message = self._load()

    def set_message(self, s):
        if s is not None and len(s) > 0:
            self._save(s)
        else:
            try:
                os.unlink(self.PATH+'/motd')
            except FileNotFoundError:
                pass

    def get_message(self) -> str:
        return self._load()

    def _save(self, s):
        with open(self.PATH + ('/motd'),'w') as out:
            out.write(s)
        self.message = s

    def _load(self):
        """load the message or return None"""
        s = None
        try:
            with open(self.PATH + ('/motd'),'r') as inp:
                s = inp.read()
        except (FileNotFoundError,PermissionError):
            pass
        return s


if __name__ == '__main__':
    m = Motd()
    m.set_message("yes we can")
    assert m.message == "yes we can"
    assert Motd().get_message() == "yes we can"
