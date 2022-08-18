import sqlite3
from threading import Lock

class DBHandler():
    """
    Classe para a manipulação do banco de dados
    """
    def __init__(self,dbpath, tags, tablename = 'dataTable'):
        """
        Construtor
        """
        self._dbpath = dbpath
        self._tablename = tablename # Nome da tabela
        self._con = sqlite3.connect(self._dbpath , check_same_thread=False) #Conexão, parâmetros(caminho, possibilitar que o banco de dados opere com Threads distintas)
        self._cursor = self._con.cursor() # Objeto para navegar/manipular os dados no BD
        self._col_names = tags.keys() # Nome das colunas
        self._lock = Lock() # Proteção dos recursos (inserção e busca simultâneas em threads diferentes)
        self.createTable()
        
    def __del__(self):
        self._con.close()
        
    def createTable(self):
        """
        Método que cria a tabela para armazenamento dos dados caso ela não exista
        """
        try:
            sql_str = f"""
            CREATE TABLE IF NOT EXISTS {self._tablename}(
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                """
            for n in self._col_names:
                sql_str += f'{n} REAL,'
                
            sql_str = sql_str[:-1] # Remoção da vírgula na ultima iteração acima
            sql_str += ');' # Finalizar a string, necessário devido a linguagem do SQLite
            self._lock.acquire() # Proteger a sessão crítica (Parecido com semáforo)
            self._cursor.execute(sql_str) # Realiza a operação
            self._con.commit() # Implementa no BD, inserção dos dados do BD
            self._lock.release() # Libera a sessão crítica
        except Exception as e:
            print("Erro: ", e.args)
            
    def insertData(self, data):
        """
        Método para inserção dos dados no BD
        """
        try:
            self._lock.acquire() # Proteção do recurso
            timestamp = str(data['timestamp']) # Conversão para string, pois precisa ser texto para inserção no BD
            
            ## Alteração
            str_cols = 'timestamp,' + ','.join(data['values'].keys()) # join separa os itens da lista com vírgula
            str_values = f"'{timestamp}'," + ','.join([str(data['values'][k]) for k in data['values'].keys()]) # Texto em aspas simples! ('texto')
            sql_str = f'INSERT INTO {self._tablename} ({str_cols}) VALUES ({str_values});'
            self._cursor.execute(sql_str)
            self._con.commit()
        except Exception as e:
            print("Erro: ",e.args)
        finally:
            self._lock.release()
            
    def selectData(self, cols, init_t, final_t):
        """
        Método que realiza a busca no BD entre 2 horários especificados
        """
        try:
            self._lock.acquire()
            sql_str = f"SELECT {','.join(cols)} FROM {self._tablename} WHERE timestamp BETWEEN '{init_t}' AND '{final_t}'"
            self._cursor.execute(sql_str)
            dados = dict((sensor,[]) for sensor in cols)
            for linha in self._cursor.fetchall(): #fetchall(recupera todas as linhas no conjunto de resultados de uma consulta e as retorna como lista de tuplas) 
                for d in range(0,len(linha)):
                    dados[cols[d]].append(linha[d])
            return dados
        except Exception as e:
            print("Erro: ",e.args)
        finally:
            self._lock.release()