class Broker:

    def __init__(self, name):
        self.name = name
        self.accounts = []
        self.read_accounts()

    def get_accounts(self):
        print(self.name)
    
    def read_accounts(self):
        print('base')
