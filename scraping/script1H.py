import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import subprocess
import pandas as pd


#defenir banco
#banco_molecula = ['CCOCCNC', "CCOCCNCCC", "CCOCCNCCCOCC"]
#banco_molecula = ['CCOCCNC']

ABSOLUT_PATH = os.path.dirname(os.path.realpath(__file__))


class Scraping1H:
    def __init__(self,pathMolecules:str,startById:int=0) -> None:
        self.startID = startById
        self.path = pathMolecules
        self.df = self.__loadData()
        self.df = self.df.query('id >= @self.startID')
        self.__createTxtFile()

    def fit(self):
        smiles = list(self.df['smiles'].values)
        idx = list(self.df['id'].values)
        #print(smiles,idx)
        self._getNMRdata(smiles,idx)

    def _getNMRdata(self,molecules:list,idx:list):
        banco_molecula = zip(idx,molecules)
        #criar Daframe com dados finais
        #datadict = pd.DataFrame()
        for id_,molecula in banco_molecula:
        # URL da API com o parâmetro SMILES
            site = 'https://www.nmrdb.org/service.php?name=nmr-1h-prediction&smiles='+ molecula

            # Enviar uma solicitação para o URL original para obter o redirecionamento
            response = requests.get(site)
            final_url = response.url

            #print(f"URL final após o redirecionamento: {final_url}")

            # Configurar o WebDriver usando ChromeDriver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

            # Navegar para o site redirecionado
            driver.get(final_url)

            # Esperar até que o botão "I agree" esteja presente na página e clicar nele
            try:
                agree_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='I agree']"))
                )
                agree_button.click()
            except Exception as e:
                print("Erro ao clicar no botão 'I agree':", e)

            # Esperar até que a página esteja completamente carregada
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'class.slick-cell l0 r0'))  # Substitua 'tagname' e 'classname' pelos valores adequados
                )
            except Exception as e:
                print("Erro ao carregar a página:", e)

            # Obter o conteúdo da página
            page_content = driver.page_source

            # Analisar o conteúdo da página com BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')

            #print(soup.prettify())

            # Fechar o navegador
            driver.quit()

            # estrutura do datamining do scrap
            assi = soup.find_all('div',class_='slick-cell l0 r0')
            ppm = soup.find_all('div',class_='slick-cell l1 r1')
            n_atomos = soup.find_all('div',class_='slick-cell l2 r2')
            multi = soup.find_all('div',class_='slick-cell l3 r3')
            j = soup.find_all('div',class_='slick-cell l4 r4')

            all_data = zip(assi, ppm, n_atomos, multi, j)

            assi_amostra = []
            ppm_amostra = []
            n_atomos_amostra = []
            multi_amostra = []
            j_amostra = []

            for assi_, ppm_, n_atomos_, multi_, j_ in all_data:
                if assi_.get_text()!="":
                    assi_amostra.append(assi_.get_text())
                else:
                    assi_amostra.append(None)

                if ppm_.get_text()!="":
                    ppm_amostra.append(ppm_.get_text())
                else:
                    ppm_amostra.append(None)

                if n_atomos_.get_text()!="":
                    n_atomos_amostra.append(n_atomos_.get_text())
                else:
                    n_atomos_amostra.append(None)
                
                if multi_.get_text()!="":
                    multi_amostra.append(multi_.get_text())
                else:
                    multi_amostra.append(None)
                
                if j_.get_text()!="":
                    j_amostra.append(j_.get_text().strip())
                else:
                    j_amostra.append(None)

            #saida do dado do scrap
            # temp = {"assign":[assi_amostra],
            #             "ppm":[ppm_amostra],
            #             "n_atomos":[n_atomos_amostra],
            #             "multi":[multi_amostra],
            #             "J":[j_amostra]}

            self.__saveDataByIter(id_,
                                  assi_amostra,
                                  ppm_amostra,
                                  n_atomos_amostra,
                                  multi_amostra,
                                  j_amostra)

            # ajuste da saido do scrap para DataFrame para comcatenar no DataFrame com dados finais
            #data_temp = pd.DataFrame(temp)

            # adicionar o scarp no DataFrame com dados finais
            #datadict = pd.concat([datadict, data_temp], axis=0, ignore_index=True)
            #return 0

    def __saveDataByIter(self,*args):
        txt = f'"{args[0]};{args[1]};{args[2]};{args[3]};{args[4]};{args[5]}"'
        subprocess.run(f'echo {txt} >> {ABSOLUT_PATH}/Scraping1H.txt',shell=True)

    def __createTxtFile(self):
        if not os.path.exists('Scraping1H.txt'):
            with open(f'{ABSOLUT_PATH}/Scraping1H.txt', 'w') as file:
                file.write('id;assign;ppm;n_atomos;multi;J\n')

    def __loadData(self):
        df = pd.read_csv(self.path)
        return df

if __name__ == "__main__":
    s1h = Scraping1H(pathMolecules='/dados/GoogleDrive/rotinas_python/Scraping_NMRDB_Renan/molecules.csv',
                     startById=2)
    fulldata = s1h.fit()
