#app.py

import streamlit as st
from modules.config import *
from modules.data_manager import DataManager
from modules.scraper import Scraper
from modules.recipe_generator import RecipeGenerator
from modules.ui_components import render_sidebar, render_product_card
from utils.calculations import calculate_daily_consumption, calculate_optimal_purchase
from utils.constants import MEAT_TYPES
import logging
from datetime import datetime
import calendar

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
data_manager = DataManager(DATA_DIR)
scraper = Scraper(CHROME_OPTIONS)
recipe_generator = RecipeGenerator(st.secrets["GEMINIAPI"]["key"])

def validate_url(url):
    """Validate Makro URL"""
    return url.startswith("https://www.makro.plazavea.com.pe/") and url.endswith("/p")

def main():
    st.set_page_config(page_title="Calcula tus Macros", page_icon="💪", layout="wide")
    st.title("Macronutrientes para Aumento de Masa Muscular")
    # Get the current theme
    theme = st.get_option("theme.base")

    # Render sidebar and get user preferences
    user_prefs = render_sidebar()
    
    # Load product data
    products = data_manager.load_food_data()
    
    # Add new product section
    with st.expander("Agregar nuevo producto"):
        new_url = st.text_input("URL del producto (Makro)")
        weight_input = st.number_input("Peso en gramos (si no se especifica en la URL)", value=100)
        meat_type = st.selectbox("Tipo de carne", [''] + MEAT_TYPES)
        
        if st.button("Agregar producto"):
            if validate_url(new_url):
                url_data = {
                    'url': new_url,
                    'weight_gr': weight_input if weight_input > 0 else None,
                    'type': meat_type if meat_type else None
                }
                if data_manager.add_product_url(url_data):
                    st.success("Producto agregado exitosamente")
            else:
                st.error("URL inválida. Debe ser una URL de Makro Plaza Vea")
    
    # Update product information
    if st.button("Actualizar información"):
        update_time = datetime.now()
        with st.spinner("Actualizando información de productos..."):
            products_urls = data_manager.load_product_urls()
            updated_products = {}
            
            for product_url_data in products_urls:
                product_info = scraper.get_product_info(product_url_data)
                if product_info:
                    updated_products[product_url_data['url']] = product_info
            
            data_manager.update_product_data(updated_products)
            st.success(f"Información actualizada: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display products and calculations
    st.header("Productos disponibles")
    selected_products = st.multiselect(
        "Selecciona los productos",
        options=list(products.keys()),
        format_func=lambda x: products[x]['name']
    )
    
    if selected_products:

        # Calculate protein distribution
        total_protein_needed = user_prefs['daily_protein']
        protein_per_product = total_protein_needed / len(selected_products)
        
        for product_url in selected_products:
            product = products[product_url]
            st.subheader(product['name'])
            
            # Validar si el producto tiene información nutricional
            if not product.get('nutrition'):
                st.warning(f"No hay información nutricional para {product['name']}")
                continue
            
            # Safely handle price information
            regular_price = product.get('price', {}).get('regular_price')
            promo_price = None
            promo_units = None
            
            if product.get('price', {}).get('promotion'):
                promo_price = product['price']['promotion'].get('price')
                promo_units = product['price']['promotion'].get('units')
            
            consumption = calculate_daily_consumption(
                protein_needed=protein_per_product,
                protein_per_100g=product['nutrition']['protein'],
                weight_gr=product['weight_gr']
            )
            
            purchase = calculate_optimal_purchase(
                units_daily=consumption['units'],
                regular_price=regular_price,
                promo_price=promo_price,
                promo_units=promo_units,
                days=calendar.monthrange(datetime.now().year, 
                                      list(calendar.month_name).index(user_prefs['month']))[1]
            )
            
            render_product_card(product, theme)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    **Consumo diario:**
                    - Gramos: {consumption['grams']:.1f}g
                    - Unidades: {consumption['units']:.2f}
                """)
            
            with col2:
                st.markdown(f"""
                    **Compra mensual óptima:**
                    - Total unidades: {purchase['units']}
                    - Costo total: S/ {purchase.get('total_cost', 'N/A'):.2f}
                    - Costo diario: S/ {purchase.get('daily_cost', 'N/A'):.2f}
                """)
        
        # Generate recipe button
        if st.button("Generar receta"):
            ingredients = {
                products[url]['name']: calculate_daily_consumption(
                    user_prefs['daily_protein'] / len(selected_products),
                    products[url]['nutrition']['protein'],
                    products[url]['weight_gr']
                )['grams']
                for url in selected_products
            }
            
            recipe = recipe_generator.generate_recipe(ingredients)
            if recipe:
                st.markdown("### Receta sugerida")
                st.markdown(recipe)
            else:
                st.error("Error al generar la receta. Por favor intenta de nuevo.")

if __name__ == "__main__":
    main()