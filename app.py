#app.py
import json
import streamlit as st
import streamlit_lottie as st_lottie
from modules.config import *
from modules.data_manager import DataManager
from modules.scraper import Scraper
from modules.recipe_generator import RecipeGenerator
from modules.ui_components import (
    render_sidebar, 
    render_product_card, 
    render_add_product_form, 
    render_recipe_generator, 
    render_nutrition_comparison,
    donation_footer
)
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

# Function to load the Lottie file
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# Load the Lottie animation
lottie_path = f"{LOGOS_DIR}/gemini_logo.json"
gemini_logo = load_lottie_file(lottie_path)

def validate_url(url):
    """Validate Makro URL"""
    return url.startswith("https://www.makro.plazavea.com.pe/") and url.endswith("/p")

def main():
    st.set_page_config(page_title="Calcula tus Macros", page_icon="💪", layout="wide")
    st.markdown("""
    <style>
    .custom-header {
        font-size: 1.75em; /* Ajusta el tamaño según tus necesidades */
        text-align: center;
        color: var(--text-color); /* Utiliza la variable de color del tema */
    }
    </style>
    <h3 class="custom-header">🍗 Macronutrientes para Aumento de Masa Muscular</h3>
    """,
    unsafe_allow_html=True
    )

    # Get the current theme
    theme = st.get_option("theme.base")

    # Cargar datos de productos ANTES de usarlos
    products = data_manager.load_food_data()
    
    # Obtener los tipos de productos disponibles
    product_types = list(set(product['type'] for product in products.values() if product.get('type') is not None))
    product_types.insert(0, 'Todos')  # Agregar opción para mostrar todos los productos

    # Renderizar sidebar y obtener preferencias del usuario
    user_prefs = render_sidebar()
    
    # Filtro por tipo de producto
    col1, col2 = st.columns([1, 4])
    with col1:
        selected_type = st.selectbox("Selecciona el tipo de producto", product_types)
    
    # Inicializar la lista de productos seleccionados en la sesión
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    # Filtrar productos según el tipo seleccionado
    if selected_type != 'Todos':
        filtered_products = {url: product for url, product in products.items() if product.get('type') == selected_type}
    else:
        filtered_products = products

    with col2:
        # Mostrar solo los productos filtrados en las opciones, pero mantener los seleccionados
        available_options = list(filtered_products.keys())
        
        # Asegurarse de que los productos ya seleccionados estén disponibles en las opciones
        all_options = list(set(available_options + st.session_state.selected_products))
        
        new_selections = st.multiselect(
            "Selecciona los productos",
            options=all_options,
            default=st.session_state.selected_products,
            format_func=lambda x: products[x]['name']
        )
        
        # Actualizar la sesión con las nuevas selecciones
        st.session_state.selected_products = new_selections

    # Usar st.session_state.selected_products para el resto de la lógica
    if st.session_state.selected_products:
        for product_url in st.session_state.selected_products:
            product = products[product_url]
            # Validar si el producto tiene información nutricional
            if not product.get('nutrition'):
                st.warning(f"No hay información nutricional para {product['name']}")
                continue

            # Manejar información de precios de forma segura
            regular_price = product.get('price', {}).get('regular_price')
            promo_price = None
            promo_units = None
            
            if product.get('price', {}).get('promotion'):
                promo_price = product['price']['promotion'].get('price')
                promo_units = product['price']['promotion'].get('units')
            
            consumption = calculate_daily_consumption(
                protein_needed=user_prefs['daily_protein'] / len(st.session_state.selected_products),
                protein_per_100g=product['nutrition']['protein'],
                weight_gr=product['weight_gr']
            )
            
            purchase = calculate_optimal_purchase(
                units_daily=consumption['units'],
                regular_price=regular_price,
                promo_price=promo_price,
                promo_units=promo_units,
                days=user_prefs['days_in_month']
            )
            
            # Renderizar tarjeta del producto
            render_product_card(product, theme)

            # Mostrar consumo diario y compra mensual óptima
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

        # Renderizar comparación nutricional
        render_nutrition_comparison({url: products[url] for url in st.session_state.selected_products})

        # Renderizar generador de recetas
        render_recipe_generator(recipe_generator, {url: products[url] for url in st.session_state.selected_products}, user_prefs)

    # Renderizar formulario para agregar nuevos productos
    with st.expander("Agregar nuevo producto"):
        producto_agregado = render_add_product_form(data_manager)
        if producto_agregado:
            st.rerun()  # Recargar la aplicación para mostrar el nuevo producto

    donation_footer(ASSETS_DIR)
    # Actualizar información de productos
    # if st.button("Actualizar información"):
    #     update_time = datetime.now()
    #     with st.spinner("Actualizando información de productos..."):
    #         products_urls = data_manager.load_product_urls()
    #         updated_products = {}
            
    #         for product_url_data in products_urls:
    #             product_info = scraper.get_product_info(product_url_data)
    #             if product_info:
    #                 updated_products[product_url_data['url']] = product_info
            
    #         data_manager.update_product_data(updated_products)
    #         st.success(f"Información actualizada: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()