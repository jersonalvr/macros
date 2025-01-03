# modules/scraper.py

import re
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote
from datetime import datetime
import logging
from zenrows import ZenRowsClient
from bs4 import BeautifulSoup
import unicodedata

class Scraper:
    def __init__(self, chrome_options=None, zenrows_api_key=st.secrets["zenrows"]["key"]):
        """
        Inicializa el scraper con opciones de Chrome
        
        :param chrome_options: Diccionario de opciones para configurar Chrome
        """
        options = Options()
        
        if chrome_options:
            for opt, value in chrome_options.items():
                if value:  # Solo añade la opción si su valor es True
                    options.add_argument(f'--{opt}')
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.zenrows_client = ZenRowsClient(zenrows_api_key)
        self.logger = logging.getLogger(__name__)
        
    def _search_fitia(self, name, product_type=None):
        """
        Busca el producto en Fitia usando ZenRows

        :param name: Nombre del producto
        :param product_type: Tipo de producto (opcional)
        :return: URL de Fitia si se encuentra
        """
        try:
            search_terms = re.sub(r'\s+', '+', name.lower())
            if product_type:
                search_terms += f"+{product_type}"

            search_url = f"https://fitia.app/es/buscar/alimentos-y-recetas/?search={search_terms}&country=pe"

            response = self.zenrows_client.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            first_result = soup.select_one('li.group a')
            if first_result:
                fitia_product_url = first_result.get('href')
                if not fitia_product_url.startswith("https://fitia.app"):
                    fitia_product_url = f"https://fitia.app{fitia_product_url}"
                return f"{fitia_product_url}?serving=gramos-100-g"

            return None
        except Exception as e:
            self.logger.warning(f"Error buscando en Fitia: {e}")
            return None

    def remove_accents(self, input_str):
        """
        Elimina los acentos de una cadena de texto.

        :param input_str: Cadena de texto con posibles acentos
        :return: Cadena de texto sin acentos
        """
        if not input_str:
            return ""
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    def _get_fitia_nutrition(self, fitia_url):
        """
        Obtiene información nutricional desde Fitia usando ZenRows

        :param fitia_url: URL de Fitia para el producto
        :return: Diccionario con información nutricional
        """
        if not fitia_url:
            self.logger.warning("URL de Fitia no proporcionada.")
            return None

        try:
            response = self.zenrows_client.get(fitia_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            nutrients_section = soup.find('div', class_='mt-8')
            if not nutrients_section:
                self.logger.warning("Sección de nutrientes no encontrada.")
                return None

            nutrients = {}
            # Encuentra todos los divs que contienen la información nutricional
            nutrient_divs = nutrients_section.find_all('div', class_='flex flex-col items-center space-y-1 rounded-xl p-3 shadow-uniform')
            if not nutrient_divs:
                self.logger.warning("No se encontraron contenedores de nutrientes.")
                return None

            for div in nutrient_divs:
                value_span = div.find('span', class_='title-3 font-bold')
                label_span = div.find('span', class_='subtitle-3')

                if value_span and label_span:
                    value_text = value_span.get_text(strip=True)
                    label_text = label_span.get_text(strip=True).lower()

                    # Eliminar acentos del label_text
                    label_text = self.remove_accents(label_text)

                    # Extraer el valor numérico, permitiendo decimales
                    match = re.match(r'([\d\.]+)', value_text)
                    if match:
                        try:
                            value = float(match.group(1))
                        except ValueError:
                            self.logger.warning(f"Valor no válido para '{label_text}': {value_text}")
                            continue
                    else:
                        self.logger.warning(f"No se pudo extraer el valor de '{value_text}' para '{label_text}'")
                        continue

                    # Mapear el valor al nutriente correspondiente
                    if 'calorias' in label_text:
                        nutrients['calories'] = value
                    elif 'grasas' in label_text:
                        nutrients['fat'] = value
                    elif 'carbohidratos' in label_text:
                        nutrients['carbs'] = value
                    elif 'proteinas' in label_text:
                        nutrients['protein'] = value

            if not nutrients:
                self.logger.warning("No se extrajo información nutricional.")
                return None

            return nutrients

        except Exception as e:
            self.logger.warning(f"Error obteniendo nutrición de Fitia: {e}")
            return None
        
    def get_product_info(self, url_data):
        """
        Obtiene información completa de un producto
        
        :param url_data: Diccionario con información de la URL
        :return: Diccionario con información del producto
        """
        url = url_data['url']
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 3)

            # Nombre del producto - Modificación para extraer correctamente
            try:
                # Primero intentar con el selector específico
                name_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//h1[@class='ProductCard__name']//div[contains(@class, 'productName')]")
                ))
                name = name_element.text.strip()
            except:
                try:
                    # Alternativa con selector más genérico
                    name_element = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "h1.ProductCard__name .productName")
                    ))
                    name = name_element.text.strip()
                except:
                    # Último recurso: extraer de la URL
                    name = self._extract_name_from_url(url)

            # Verificar si el nombre está vacío
            if not name:
                name = self._extract_name_from_url(url)

            # URL de imagen
            img_element = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".slick-slide.slick-active.slick-current img")
            ))
            image_url = img_element.get_attribute('src')

            # Información de precio
            price_info = self._extract_price_info()

            # Peso del producto
            weight_gr = self._extract_weight(url, name, url_data)

            # Búsqueda y datos nutricionales en Fitia
            fitia_url = self._search_fitia(name, url_data.get('type'))
            nutrition = self._get_fitia_nutrition(fitia_url) if fitia_url else None

            return {
                'name': name,
                'image_url': image_url,
                'price': price_info,
                'weight_gr': weight_gr,
                'type': url_data.get('type'),
                'fitia_url': fitia_url,
                'nutrition': nutrition,
                'url': url,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scraping product {url}: {e}")
            return None

    def _extract_name_from_url(self, url):
        """
        Extrae un nombre legible desde la URL
        
        :param url: URL del producto
        :return: Nombre extraído de la URL
        """
        # Eliminar el dominio y la parte final de la URL
        name_from_url = url.split('/')[-2]
        
        # Reemplazar guiones con espacios y capitalizar
        name = name_from_url.replace('-', ' ').title()
        
        # Eliminar palabras comunes
        words_to_remove = ['makro', 'plazavea', 'com', 'pe', 'p']
        name = ' '.join([word for word in name.split() if word.lower() not in words_to_remove])
        
        return name.strip()

    def _extract_price_info(self):
        """
        Extrae información de precios, incluyendo promociones
        
        :return: Diccionario con información de precios
        """
        try:
            # Precio regular
            regular_price_elem = self.driver.find_element(
                By.CSS_SELECTOR, ".MakroPrice_Regular .pricebox span")
            regular_price_text = regular_price_elem.text.replace('S/', '').replace(',', '.')
            regular_price = float(regular_price_text)

            # Verificar si hay promoción
            promotion = None
            try:
                promo_elem = self.driver.find_element(
                    By.CSS_SELECTOR, ".MakroPrice_BiPriceMakro")
                promo_units_elem = promo_elem.find_element(By.CSS_SELECTOR, ".units span")
                promo_price_elem = promo_elem.find_element(By.CSS_SELECTOR, ".pricebox span")
                
                promo_units = int(re.search(r'\d+', promo_units_elem.text).group())
                promo_price_text = promo_price_elem.text.replace('S/', '').replace(',', '.')
                promo_price = float(promo_price_text)
                
                promotion = {
                    'units': promo_units,
                    'price': promo_price
                }
            except:
                pass

            return {
                'regular_price': regular_price,
                'promotion': promotion
            }
        except Exception as e:
            self.logger.warning(f"No se pudo extraer precio: {e}")
            return {'regular_price': None, 'promotion': None}

    def _extract_weight(self, url, name, url_data):
        """
        Extrae el peso del producto de manera más robusta
        
        :param url: URL del producto
        :param name: Nombre del producto
        :param url_data: Datos adicionales de la URL
        :return: Peso en gramos
        """
        # Verificar si ya viene con peso en los datos
        if url_data.get('weight_gr'):
            return url_data['weight_gr']

        # Patrones de búsqueda de peso
        weight_patterns = [
            r'(\d+)\s*(?:kg|g)\b',  # Números seguidos de kg o g
            r'x\s*(\d+)\s*(?:kg|g)',  # x seguido de números y kg/g
            r'bolsa\s*(\d+)\s*(?:kg|g)',  # bolsa seguida de números y kg/g
        ]

        # Buscar en URL
        for pattern in weight_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                weight = float(match.group(1))
                return weight * 1000 if 'kg' in match.group(0).lower() else weight

        # Buscar en nombre
        for pattern in weight_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                weight = float(match.group(1))
                return weight * 1000 if 'kg' in match.group(0).lower() else weight

        # Valor por defecto
        return 1000  # 1 kg por defecto

    # def _search_fitia(self, name, product_type=None):
    #     """
    #     Busca el producto en Fitia usando Selenium
        
    #     :param name: Nombre del producto
    #     :param product_type: Tipo de producto (opcional)
    #     :return: URL de Fitia si se encuentra
    #     """
    #     try:
    #         # Limpiar y preparar términos de búsqueda
    #         search_terms = re.sub(r'\s+', '+', name.lower())
            
    #         # Agregar tipo de producto si está disponible
    #         if product_type:
    #             search_terms += f"+{product_type}"

    #         search_url = f"https://fitia.app/es/buscar/alimentos-y-recetas/?search={search_terms}&country=pe"
            
    #         # Realizar búsqueda en Fitia
    #         self.driver.get(search_url)
    #         wait = WebDriverWait(self.driver, 3)

    #         # Esperar a que se carguen los resultados
    #         try:
    #             first_result = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.group a')))
    #             if first_result:
    #                 fitia_product_url = first_result.get_attribute('href')
    #                 # Asegurarse de que la URL esté bien formada
    #                 if not fitia_product_url.startswith("https://fitia.app"):
    #                     fitia_product_url = f"https://fitia.app{fitia_product_url}"
    #                 return f"{fitia_product_url}?serving=gramos-100-g"
    #         except Exception as e:
    #             # Manejo de CAPTCHA
    #             if "CAPTCHA" in str(e):
    #                 print("Se encontró un CAPTCHA. Por favor, resuélvelo manualmente.")
    #                 input("Presiona Enter después de resolver el CAPTCHA...")
    #                 return self._search_fitia(name, product_type)  # Reintentar la búsqueda

    #         return None
    #     except Exception as e:
    #         self.logger.warning(f"Error buscando en Fitia: {e}")
    #         return None

    # def _get_fitia_nutrition(self, fitia_url):
    #     """
    #     Obtiene información nutricional desde Fitia usando Selenium
        
    #     :param fitia_url: URL de Fitia para el producto
    #     :return: Diccionario con información nutricional
    #     """
    #     if not fitia_url:
    #         return None

    #     try:
    #         self.driver.get(fitia_url)
    #         wait = WebDriverWait(self.driver, 10)

    #         # Esperar a que se cargue la sección de nutrición
    #         nutrients_section = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'mt-8')))
            
    #         # Extraer valores nutricionales
    #         calories_elem = nutrients_section.find_elements(By.XPATH, ".//span[contains(@class, 'title-3') and contains(text(), 'kcal')]")[0]
    #         fat_elem = nutrients_section.find_elements(By.XPATH, ".//span[contains(@class, 'title-3') and contains(text(), 'grasas')]")[0]
    #         carbs_elem = nutrients_section.find_elements(By.XPATH, ".//span[contains(@class, 'title-3') and contains(text(), 'carbohidratos')]")[0]
    #         protein_elem = nutrients_section.find_elements(By.XPATH, ".//span[contains(@class, 'title-3') and contains(text(), 'proteínas')]")[0]

    #         def extract_value(element):
    #             """Extrae valor numérico de un elemento, eliminando caracteres no numéricos"""
    #             text = element.text
    #             print(f"Texto extraído: {text}")  # Mensaje de depuración
    #             # Eliminar caracteres no numéricos (incluyendo emojis y unidades)
    #             numeric_value = ''.join(filter(str.isdigit, text.split()[0]))  # Solo el primer valor
    #             return float(numeric_value) if numeric_value else None

    #         return {
    #             'calories': extract_value(calories_elem),
    #             'fat': extract_value(fat_elem),
    #             'carbs': extract_value(carbs_elem),
    #             'protein': extract_value(protein_elem)
    #         }
    #     except Exception as e:
    #         self.logger.warning(f"Error obteniendo nutrición de Fitia: {e}")
    #         return None
    
    def close(self):
        """
        Cierra el navegador WebDriver
        """
        if self.driver:
            self.driver.quit()

    def __del__(self):
        """
        Asegura que el navegador se cierre al destruir la instancia
        """
        self.close()

def validate_makro_url(url):
    """
    Valida si la URL es de Makro Plaza Vea
    
    :param url: URL a validar
    :return: Booleano indicando si es válida
    """
    return (
        url.startswith("https://www.makro.plazavea.com.pe/") and 
        url.endswith("/p")
    )

def extract_url_metadata(url, name=None):
    """
    Extrae metadatos adicionales de una URL de producto
    
    :param url: URL del producto
    :param name: Nombre del producto (opcional)
    :return: Diccionario con metadatos
    """
    metadata = {
        'url': url
    }

    # Extraer peso
    weight_match = re.search(r'(\d+)\s*(?:kg|g)\b', url, re.IGNORECASE)
    if weight_match:
        weight = float(weight_match.group(1))
        metadata['weight_gr'] = weight * 1000 if 'kg' in weight_match.group(0).lower() else weight

    # Extraer tipo de producto
    meat_keywords = {
        'pollo': ['pollo', 'pechuga', 'pierna', 'encuentro'],
        'pavo': ['pavo'],
        'res': ['res', 'carne', 'bistec', 'lomo'],
        'cerdo': ['cerdo', 'chuleta']
    }

    for meat_type, keywords in meat_keywords.items():
        if any(keyword in url.lower() or (name and keyword in name.lower()) for keyword in keywords):
            metadata['type'] = meat_type
            break

    return metadata

def bulk_validate_urls(urls):
    """
    Valida múltiples URLs
    
    :param urls: Lista de URLs
    :return: Lista de URLs válidas
    """
    return [url for url in urls if validate_makro_url(url)]

def preprocess_product_name(name):
    """
    Preprocesa el nombre del producto para búsquedas
    
    :param name: Nombre original del producto
    :return: Nombre preprocesado
    """
    # Eliminar marcas comerciales, unidades, etc.
    name = re.sub(r'\b(Bolsa|Paquete|x\d+|Congelado|Fresco)\b', '', name, flags=re.IGNORECASE)
    # Eliminar espacios extra
    name = ' '.join(name.split())
    return name