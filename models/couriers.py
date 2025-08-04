

class Courier():
    def __init__(self, courierId, name) -> None:
        self.id = courierId
        self.name = name
        self.zarobotok = 0

    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name
    def get_zarobotok(self):
        return self.zarobotok
    
    def add (self, zarobotok, summa):
        self.zarobotok += (zarobotok + summa)

    