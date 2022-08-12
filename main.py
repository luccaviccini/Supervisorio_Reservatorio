from kivy.app import App ## clase base para criação de aplicativos
from mainwidget import MainWidget
from kivy.lang.builder import Builder
class MainApp(App):
    """
    Classe com o aplicativo
    """
    def build(self):
        """
        Método que gera o aplicativo com no widget principal
        """
        self._widget = MainWidget()
        return self._widget

if __name__ == '__main__':
    Builder.load_string(open("mainwidget.kv",encoding="utf-8").read(),rulesonly=True) # essa linha eh pois o mainwidget nao tem o nome de main.kv
    MainApp().run()