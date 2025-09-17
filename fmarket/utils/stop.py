import os

class Stop():
    text_path = 'data/stop.txt'
    def __init__(self):
        if not os.path.exists(self.text_path): self.clear()
    
    @ property
    def is_set(self):
        with open(self.text_path, 'r') as f:
            if len(f.read()) > 0:
                return True
            return False
    
    @property
    def set(self):
        with open(self.text_path, 'w') as f:
            f.write('stop')
        # return self.is_set
    
    @property
    def clear(self):
        with open(self.text_path, 'w') as f:
            pass
        # return self.is_set
        