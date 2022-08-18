from kivy.uix.boxlayout import BoxLayout
from popups import ModbusPopup, ScanPopup, InfoPopup, DataGraphPopup, HistGraphPopup
from pyModbusTCP.client import ModbusClient
from kivy.core.window import Window
from threading import Thread
from time import sleep
from datetime import datetime
import random
from timeseriesgraph import TimeSeriesGraph
from bdhandler import DBHandler
from kivy_garden.graph import LinePlot


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
        self._infoPopup = InfoPopup()
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
        self._hgraph = HistGraphPopup(tags=self._tags)
        self._db = DBHandler(kwargs.get('db_path'), self._tags)
        
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
                self._db.insertData(self._meas)
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
                #print(key, self._meas['values'][key])

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
        #Atualização dos labels das infos
        lista_plot_popup = {'pot_entrada' : ' W','rotacao': ' rpm', 'freq_mot': ' Hz', 'temp_estator': ' ºC'}
        lista_plot_main = { 'vz_entrada':' L/s' , 'nivel': ' L'}
        for key,value in self._tags.items():
            if key in lista_plot_main:
                self.ids[key].text = str((self._meas['values'][key])/self._tags[key]['multiplicador']) + lista_plot_main[key]
            if key in lista_plot_popup:    
                self._infoPopup.ids[key].text = str((self._meas['values'][key])/self._tags[key]['multiplicador']) + lista_plot_popup[key]

        #Atualização do nível da agua
        self.ids.lb_reservatorio.size = (self.ids.lb_reservatorio.size[0],(self._meas['values']['nivel']/self._tags['nivel']['multiplicador'])*199/1000)
        
        #Atualização do gráfico
        self._graph.ids.graph.updateGraph((self._meas['timestamp'],self._meas['values']['nivel']/self._tags['nivel']['multiplicador']),0)
        #self._graph.ids.graph.updateGraph((self._meas['timestamp'],self._meas['values']['vz_entrada']/self._tags['vz_entrada']['multiplicador']),0) 

        self.check_motor_state(self._meas['values']['estado_mot'])   
    def stopRefresh(self):
        self._updateWidgets = False

    def switch_click(self, switchObject, switchValue, type, addr):
        if(switchValue):
            self.writeData(type, addr, 1)
        
        else:
            self.writeData(type, addr, 0)

    def toggle_click(self,state, type, addr):
        
        if(state=='down'):
            self.writeData(type, addr, 1)
        
        else:
            self.writeData(type, addr, 0)    

    # Adicionei aqui a parte de Banco de Dados
    def check_motor_state(self, motor_state):
        if not(motor_state):
            self.ids.tb_motor.state = 'normal'
          
    def getDataDB(self):
        """
        Método que coleta as informações da interface fornecidas pelo usuário
        e requisita a busca no BD
        """
        try:
            init_t = self.parseDTString(self._hgraph.ids.txt_init_time.text) # Transcrever para a maneira que o banco de dados aceita
            final_t = self.parseDTString(self._hgraph.ids.txt_final_time.text) # Transcrever para a maneira que o banco de dados aceita
            cols = []
            for sensor in self._hgraph.ids.sensores.children: # Varre todas os ids filhos do id pai "sensores"
                if sensor.ids.checkbox.active: # Se o check box estiver ativo
                    cols.append(sensor.id) #
                    
            if init_t is None or final_t is None or len(cols)==0:
                return
                
            cols.append('timestamp')
                
            dados = self._db.selectData(cols, init_t, final_t)
                
            if dados is None or len(dados['timestamp']) == 0:
                return

            self._hgraph.ids.graph.clearPlots()
                
            for key, value in dados.items():
                if key == 'timestamp':
                    continue
                p = LinePlot(line_width=1.5, color=self._tags[key]['color'])
                p.points = [(x, value[x]) for x in range(0,len(value))]
                self._hgraph.ids.graph.add_plot(p) # Adicionamos o gráfico
            self._hgraph.ids.graph.xmax = len(dados[cols[0]])
            self._hgraph.ids.graph.update_x_labels([datetime.strptime(x,"%Y-%m-%d %H:%M:%S.%f") for x in dados['timestamp']]) # Conversão para datetime, pois o método operado com parâmetros em datetime
        except Exception as e:
            print("Erro: ", e.args)
                
    def parseDTString(self,datetime_str):
        """
        Método que converte a string inserida pelo usuário para o formato utilizado na busca dos dados no BD
        """
        try:
            d = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
            return d.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print("Erro: ", e.args)