from .analysis_compare_gui import Analysis_Compare_GUI

class Analysis_Charts_GUI(Analysis_Compare_GUI):
    def __init__(self, parent, symbols):
        super().__init__(parent, symbols)

        self.title('Charts Compare')

    def symbols_changed(self, symbols):
        print(symbols)
