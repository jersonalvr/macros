import os
import json
from datetime import datetime
import logging
from typing import Dict, List, Any
from modules.scraper import validate_makro_url, extract_url_metadata, preprocess_product_name

class DataManager:
    def __init__(self, data_dir: str):
        """
        Inicializa el gestor de datos
        
        :param data_dir: Directorio donde se guardarán los archivos de datos
        """
        self.data_dir = data_dir
        self.products_urls_path = os.path.join(data_dir, 'products_urls.json')
        self.food_data_path = os.path.join(data_dir, 'food_data.json')
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Inicializar archivos si no existen
        self._initialize_files()
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)

    def _initialize_files(self):
        """
        Inicializa archivos de datos si no existen
        """
        # Inicializar products_urls.json
        if not os.path.exists(self.products_urls_path):
            with open(self.products_urls_path, 'w') as f:
                json.dump([], f, indent=4)
        
        # Inicializar food_data.json
        if not os.path.exists(self.food_data_path):
            with open(self.food_data_path, 'w') as f:
                json.dump({}, f, indent=4)

    def load_product_urls(self) -> List[Dict[str, Any]]:
        """
        Carga las URLs de productos
        
        :return: Lista de diccionarios con URLs de productos
        """
        try:
            with open(self.products_urls_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.error("Error al cargar URLs de productos")
            return []

    def load_food_data(self) -> Dict[str, Any]:
        """
        Carga los datos de alimentos
        
        :return: Diccionario de datos de alimentos
        """
        try:
            with open(self.food_data_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.error("Error al cargar datos de alimentos")
            return {}

    def add_product_url(self, url_data: Dict[str, Any]) -> bool:
        """
        Agrega una nueva URL de producto
        
        :param url_data: Diccionario con datos de la URL
        :return: Booleano indicando si se agregó correctamente
        """
        # Validar URL de Makro
        if not validate_makro_url(url_data['url']):
            self.logger.warning(f"URL inválida: {url_data['url']}")
            return False

        # Cargar URLs existentes
        product_urls = self.load_product_urls()

        # Verificar si la URL ya existe
        if any(existing['url'] == url_data['url'] for existing in product_urls):
            self.logger.info(f"URL ya existe: {url_data['url']}")
            return False

        # Extraer metadatos adicionales
        metadata = extract_url_metadata(url_data['url'])
        
        # Combinar metadatos
        final_url_data = {**metadata, **url_data}

        # Agregar nueva URL
        product_urls.append(final_url_data)

        # Guardar URLs actualizadas
        try:
            with open(self.products_urls_path, 'w') as f:
                json.dump(product_urls, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar URL: {e}")
            return False

    def update_product_data(self, updated_products: Dict[str, Dict[str, Any]]):
        """
        Actualiza los datos de productos
        
        :param updated_products: Diccionario de productos actualizados
        """
        # Cargar datos existentes
        current_products = self.load_food_data()

        # Actualizar o agregar productos
        for url, product_info in updated_products.items():
            current_products[url] = product_info

        # Guardar datos actualizados
        try:
            with open(self.food_data_path, 'w') as f:
                json.dump(current_products, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error al guardar datos de productos: {e}")

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca productos por nombre o tipo
        
        :param query: Término de búsqueda
        :return: Lista de productos que coinciden
        """
        products = self.load_food_data()
        query = query.lower()

        # Filtrar productos
        matching_products = [
            product for product in products.values()
            if (query in product['name'].lower() or 
                (product.get('type') and query in product['type'].lower()))
        ]

        return matching_products

    def get_product_by_url(self, url: str) -> Dict[str, Any]:
        """
        Obtiene un producto por su URL
        
        :param url: URL del producto
        :return: Diccionario con información del producto
        """
        products = self.load_food_data()
        return products.get(url)

    def delete_product_url(self, url: str) -> bool:
        """
        Elimina una URL de producto
        
        :param url: URL a eliminar
        :return: Booleano indicando si se eliminó correctamente
        """
        product_urls = self.load_product_urls()
        
        # Filtrar URLs
        updated_urls = [url_data for url_data in product_urls if url_data['url'] != url]

        # Verificar si se eliminó algo
        if len(updated_urls) < len(product_urls):
            try:
                with open(self.products_urls_path, 'w') as f:
                    json.dump(updated_urls, f, indent=4)
                return True
            except Exception as e:
                self.logger.error(f"Error al eliminar URL: {e}")
                return False
        
        return False

    def backup_data(self):
        """
        Realiza una copia de seguridad de los archivos de datos
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup products_urls.json
        backup_urls_path = os.path.join(
            self.data_dir, 
            f'products_urls_backup_{timestamp}.json'
        )
        
        # Backup food_data.json
        backup_food_path = os.path.join(
            self.data_dir, 
            f'food_data_backup_{timestamp}.json'
        )

        try:
            # Copiar archivos
            with open(self.products_urls_path, 'r') as src, open(backup_urls_path, 'w') as dst:
                dst.write(src.read())
            
            with open(self.food_data_path, 'r') as src, open(backup_food_path, 'w') as dst:
                dst.write(src.read())
            
            self.logger.info(f"Backup realizado: {backup_urls_path}, {backup_food_path}")
        except Exception as e:
            self.logger.error(f"Error al realizar backup: {e}")