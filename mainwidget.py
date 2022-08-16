from kivy.uix.boxlayout import BoxLayout
from popups import ModbusPopup, ScanPopup, ControlePopup, DataGraphPopup
from pyModbusTCP.client import ModbusClient
from kivy.core.window import Window
from threading import Thread
from time import sleep
from datetime import datetime
import random
from timeseriesgraph import TimeSeriesGraph


class MainWidget(BoxLayout):
    """
    widget principal da aplicação
    """
    _updateThread = None
    _updateWidgets = True
    _tags ={}
    _max_points = 20
    
    
    def __init__(self, **kwargs):
        """
        Construtor do widget principal
        """
        super().__init__()
        self._scan_time = kwargs.get('scan_time')
        self._serverIP = kwargs.get('server_ip')
        self._serverPort = kwargs.get('server_port') 
              
        self._modbusPopup = ModbusPopup(self._serverIP,self._serverPort)
        self._scanPopup = ScanPopup(scantime = self._scan_time)
        self._controlePopup = ControlePopup()
        self._modbusClient = ModbusClient(host = self._serverIP,port = self._serverPort)
        self._meas = {} # Esse atributo irá possuir as medições atuais (Dicionário)
        self._meas['timestamp'] = None # Irá possuir um campo chamado 'timestamp'
        self._meas['values'] = {} # Irá possuir um campo chamado 'values', os valores das várias tags do sistema

        for key,value in kwargs.get('modbus_addrs').items(): # Fazemos uma leitura no dicionário 'modbus_addrs'
            if key == 'nivel': # Se a tag for 'estado_mot', faça...
                plot_color = (0,0,1,1)
            else:
                plot_color = (random.random(),random.random(),random.random(),1)
            self._tags[key] = {'type': value['type'], 'addr': value['addr'], 'multiplicador': value['multiplicador'], 'color':plot_color} 

        self._graph = DataGraphPopup(self._max_points, self._tags['nivel']['color'])
    def stardDataRead(self, ip, port):
        """
        Método utilizado para a configuração do IP e Porta do servidor MODBUS e 
        inicializar uma thread para a leitura dos dados e atualização da interface 
        gráfica
        """
        self._serverIP = ip
        self._serverPort = port
        self._modbusClient.host = self._serverIP
        self._modbusClient.port = self._serverPort
        try:
            Window.set_system_cursor("wait")
            self._modbusClient.open()
            Window.set_system_cursor("arrow")
            
            if self._modbusClient.is_open:
                self._updateThread = Thread(target=self.updater)
                self._updateThread.start()
                self.ids.img_con.source = "imgs/conectado.png"
                self._controlePopup.ids.switch_motor.disabled = False
                self._controlePopup.ids.sol_1.disabled = False
                self._controlePopup.ids.sol_2.disabled = False
                self._controlePopup.ids.sol_3.disabled = False
                
                self._modbusPopup.dismiss()
            else:
                self._modbusPopup.setInfo("Falha na conexão com o servidor")
        except Exception as e:
            print("Erro: ", e.args)
            
    def updater(self):
        """
        Método que invoca as rotinas de leitura dos dados, atualização da interface e 
        inserção dos dados no Banco de dados
        """
        try:
            while(self._updateWidgets):
                #escrever no modbus_addrs
                #self.writeData('coil', 800, 1)
                # ler os dados MODBUS
                self.readData()
                # atualizar a interface
                self.updateGUI()
                # inserir os dados no banco de dados
                sleep(self._scan_time/1000)     
        except Exception as e:
            self._modbusClient.close()
            print("Erro: ", e.args)       

    def readData(self): # Ideia do readData é atualizar o atributo meas
        """
        Método para a leitura dos dados por meio do protocolo MODBUS
        """
        self._meas['timestamp'] = datetime.now() # o campo 'timestamp' recebe exatamente o horário corrente do sistema operacional

        for key,value in self._tags.items():
            if value['type'] == 'input_r':
                self._meas['values'][key] = self._modbusClient.read_input_registers(value['addr'],1)[0] # Leitura de um Input Register (Aula de Modbus)
                #print(key, self._meas['values'][key])

            elif value['type'] == 'holding':  
                self._meas['values'][key] = self._modbusClient.read_holding_registers(value['addr'],1)[0] # Leitura de um Holding Register (Aula de Modbus)
                #print(key, self._meas['values'][key])

            elif value['type'] == 'coil':
                self._meas['values'][key] = self._modbusClient.read_coils(value['addr'],1)[0] # Leitura de um Coil
                print(key, self._meas['values'][key])

            else:
                self._meas['values'][key] = self._modbusClient.read_discrete_inputs(value['addr'],1)[0] # Leitura de um Discrete Inputs
                #print(key, self._meas['values'][key])
    def writeData(self, type, addr, value):
        """
        Método para escrita de dados  por meio do protocolo MODBUS
        """

        if type == 'coil':
            return self._modbusClient.write_single_coil(addr, value)
          
    def updateGUI(self):
        """
        Método para atualização da interface gráfica a partir dos dados lidos 
        """
        #Atualização dos labels das variaveis
        lista_plot_unidades = {'pot_entrada' : ' W', 'vz_entrada':' L/s' , 'nivel': ' L' , 'rotacao': ' rpm', 'freq_mot': ' Hz', 'temp_estator': ' ºC'}
        for key,value in self._tags.items():
            if key in lista_plot_unidades:
                self.ids[key].text = str((self._meas['values'][key])/self._tags[key]['multiplicador']) + lista_plot_unidades[key]

        #Atualização do nível do reservatorio
        self.ids.lb_reservatorio.size = (self.ids.lb_reservatorio.size[0],(self._meas['values']['nivel']/self._tags['nivel']['multiplicador'])*199/1000)
        
        #Atualização do gráfico
        self._graph.ids.graph.updateGraph((self._meas['timestamp'],self._meas['values']['nivel']/self._tags['nivel']['multiplicador']),0)
        #self._graph.ids.graph.updateGraph((self._meas['timestamp'],self._meas['values']['vz_entrada']/self._tags['vz_entrada']['multiplicador']),0) 
        
        # Atualização da imagem do estado do botão
        self.check_motor_state(self._meas['values']['estado_mot'])   
    def stopRefresh(self):
        self._updateWidgets = False

    def switch_click(self, switchObject, switchValue, type, addr):
        if(switchValue):
            self.writeData(type, addr, 1)
        
        else:
            self.writeData(type, addr, 0)

    def toggle_click(self,state, type, addr):
        print(state)
        if(state=='down'):
            self.writeData(type, addr, 1)
        
        else:
            self.writeData(type, addr, 0)    

    def check_motor_state(self, motor_state):
        if not(motor_state):
            self.ids.tb_motor.state = 'normal'
            