from kivy.app import App ## clase base para criação de aplicativos
from mainwidget import MainWidget
from kivy.lang import Builder

class MainApp(App):
    """
    Classe com aplicativo
    """
    def build(self):
        """
        Método que gera o aplicativo com o widget principal
        """
        self._widget = MainWidget(scan_time=1000, server_ip = '127.0.0.1', server_port = 502,
        modbus_addrs = {
            #Lembrar de colocar None no if, quando for implementar, para não dividor/multiplicar
            #LEMBRAR DOS MULTIPLICADORES (Só mechi aqui)
            'estado_mot'  : {'type': 'coil'     , 'addr': 800, 'multiplicador': None},
            'freq_des'    : {'type': 'holding'  , 'addr': 799, 'multiplicador': 1 },
            't_part'      : {'type': 'holding'  , 'addr': 798, 'multiplicador': 10 },
            'freq_mot'    : {'type': 'input_r'  , 'addr': 800, 'multiplicador': 10 },
            'tensao'      : {'type': 'input_r'  , 'addr': 801, 'multiplicador': 1 },
            'rotacao'     : {'type': 'input_r'  , 'addr': 803, 'multiplicador': 1 },
            'pot_entrada' : {'type': 'input_r'  , 'addr': 804, 'multiplicador': 10 },
            'corrente'    : {'type': 'input_r'  , 'addr': 805, 'multiplicador': 100 },
            'temp_estator': {'type': 'input_r'  , 'addr': 806, 'multiplicador': 10 },
            'vz_entrada'  : {'type': 'input_r'  , 'addr': 807, 'multiplicador': 100 },
            'nivel'       : {'type': 'input_r'  , 'addr': 808, 'multiplicador': 10 },
            'nivel_h'     : {'type': 'discrete' , 'addr': 809, 'multiplicador': None },
            'nivel_1'     : {'type': 'discrete' , 'addr': 810, 'multiplicador': None },
            'Solenoide_1' : {'type': 'coil'     , 'addr': 801, 'multiplicador': None },
            'Solenoide_2' : {'type': 'coil'     , 'addr': 802, 'multiplicador': None },
            'Solenoide_3' : {'type': 'coil'     , 'addr': 803, 'multiplicador': None }       
        }     
        
        )
        return self._widget

    def on_stop(self):
        """
        Método executado quando a aplicação é fechada
        """
        self._widget.stopRefresh() 

if __name__ == "__main__":
    Builder.load_string(open("mainwidget.kv", encoding = "utf-8").read(), rulesonly = True)
    Builder.load_string(open("popups.kv", encoding = "utf-8").read(), rulesonly = True)
    
    MainApp().run()    
