# modules/ui_components.py

import streamlit as st
import base64
import textwrap
from streamlit_tailwind import st_tw
import calendar
from datetime import datetime
from utils.constants import MEAT_TYPES
from modules.config import LOGOS_DIR

def render_sidebar():
    """
    Renderiza la barra lateral de configuración y cálculo de macronutrientes
    
    :return: Diccionario con preferencias del usuario
    """
    st.sidebar.header("Configuración Nutricional")
    
    # Información personal
    weight = st.sidebar.number_input("Tu peso (kg)", value=75.0, min_value=40.0, max_value=200.0, step=0.1)
    
    # Factores de macronutrientes
    st.sidebar.subheader("Factores de Macronutrientes")
    protein_factor = st.sidebar.number_input("Gramos de proteína por kg", value=2.7, min_value=1.6, max_value=4.0, step=0.1)
    carbs_factor = st.sidebar.number_input("Gramos de carbohidratos por kg", value=7.0, min_value=4.0, max_value=10.0, step=0.1)
    fats_factor = st.sidebar.number_input("Gramos de grasas por kg", value=1.2, min_value=0.5, max_value=3.0, step=0.1)
    
    # Cálculos diarios
    daily_protein = weight * protein_factor
    daily_carbs = weight * carbs_factor
    daily_fat = weight * fats_factor
    
    # Selector de mes
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_names = list(calendar.month_name)[1:]
    
    selected_month_index = st.sidebar.selectbox(
        "Selecciona el mes", 
        range(len(month_names)), 
        index=current_month - 1,
        format_func=lambda x: month_names[x]
    )
    selected_month = month_names[selected_month_index]
    
    # Días del mes seleccionado
    _, days_in_month = calendar.monthrange(current_year, selected_month_index + 1)
    
    # Mostrar resumen de macronutrientes
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Resumen Diario")
    st.sidebar.markdown(f"**Proteína:** {daily_protein:.1f}g")
    st.sidebar.markdown(f"**Carbohidratos:** {daily_carbs:.1f}g")
    st.sidebar.markdown(f"**Grasas:** {daily_fat:.1f}g")
    
    return {
        "weight": weight,
        "protein_factor": protein_factor,
        "carbs_factor": carbs_factor,
        "fats_factor": fats_factor,
        "daily_protein": daily_protein,
        "daily_carbs": daily_carbs,
        "daily_fat": daily_fat,
        "month": selected_month,
        "days_in_month": days_in_month
    }

# Función para renderizar una tarjeta de producto con Tailwind CSS
def render_product_card(product, theme):
    """
    Renderiza una tarjeta de producto con información detallada utilizando Tailwind CSS.
    Altura ajustada a 320px con espaciado optimizado.

    :param product: Diccionario con información del producto.
    :param theme: Tema actual de Streamlit ('light' o 'dark').
    """
    with open(f"{LOGOS_DIR}/fitia_logo.svg", "r") as f:
        fitia_logo_light = f.read()
    with open(f"{LOGOS_DIR}/fitia_logo_blank.svg", "r") as f:
        fitia_logo_dark = f.read()
    
    with open(f"{LOGOS_DIR}/makro_logo.svg", "r") as f:
        makro_logo_light = f.read()
    with open(f"{LOGOS_DIR}/makro_logo_blank.svg", "r") as f:
        makro_logo_dark = f.read()
    
    # Convertir a base64
    fitia_logo_light_b64 = base64.b64encode(fitia_logo_light.encode()).decode()
    fitia_logo_dark_b64 = base64.b64encode(fitia_logo_dark.encode()).decode()
    makro_logo_light_b64 = base64.b64encode(makro_logo_light.encode()).decode()
    makro_logo_dark_b64 = base64.b64encode(makro_logo_dark.encode()).decode()
    
    # Usar las versiones base64 en el HTML
    fitia_logo = f"data:image/svg+xml;base64,{fitia_logo_dark_b64}" if theme == 'dark' else f"data:image/svg+xml;base64,{fitia_logo_light_b64}"
    makro_logo = f"data:image/svg+xml;base64,{makro_logo_dark_b64}" if theme == 'dark' else f"data:image/svg+xml;base64,{makro_logo_light_b64}"
    
    # Configurar colores según el tema
    bg_color = "bg-gray-800" if theme == "dark" else "bg-white"
    text_color = "text-white" if theme == "dark" else "text-gray-800"
    
    # Construir el contenido HTML de la tarjeta
    card_html = f"""
    <div class="flex flex-col {bg_color} {text_color} p-4 rounded-lg shadow-lg h-80">
        <!-- Header con imagen y nombre - Aumentado el tamaño y espaciado -->
        <div class="flex items-start space-x-6 mb-6">
            <img src="{product['image_url']}" alt="{product['name']}" class="w-20 h-20 md:w-24 md:h-24 object-cover rounded-lg flex-shrink-0">
            <div class="min-w-0">
                <h3 class="text-xl md:text-2xl font-bold leading-tight mb-2">{product['name']}</h3>
                <p class="text-sm md:text-base">Tipo: {product.get('type', 'No especificado')}</p>
            </div>
        </div>
        
        <!-- Precio y Peso -->
        <div class="grid grid-cols-2 gap-3 mb-2">
            <div>
                <h4 class="text-sm font-semibold mb-0.5">Precio</h4>
                <p class="text-sm">Regular: S/ {product['price'].get('regular_price', 'N/A')}</p>
                {"<p class='text-sm'>Oferta: " + product['price']['promotion']['units'] + " x S/ " + str(product['price']['promotion']['price']) + "</p>" 
                 if product['price'].get('promotion') else ""}
            </div>
            
            <div>
                <h4 class="text-sm font-semibold mb-0.5">Peso</h4>
                <p class="text-sm">{product['weight_gr']} g</p>
            </div>
        </div>
        
        {"<div class='grid grid-cols-2 gap-3'>" +
            f"""
            <div>
                <h4 class="text-sm font-semibold mb-0.5">Información Nutricional</h4>
                <p class="text-sm">Calorías: {product['nutrition'].get('calories', 'N/A')} kcal</p>
                <p class="text-sm">Proteínas: {product['nutrition'].get('protein', 'N/A')} g</p>
                <p class="text-sm">Carbohidratos: {product['nutrition'].get('carbs', 'N/A')} g</p>
                <p class="text-sm">Grasas: {product['nutrition'].get('fat', 'N/A')} g</p>
            </div>
            <div class="flex flex-col justify-between">
                <div class="flex flex-col space-y-3">
                    <a href="{product['fitia_url']}" target="_blank" class="flex items-center">
                        <span class="text-sm mr-2">Ver en</span>
                        <img src="{fitia_logo}" alt="Fitia" class="h-5">
                    </a>
                    <a href="{product['url']}" target="_blank" class="flex items-center">
                        <span class="text-sm mr-2">Comprar en</span>
                        <img src="{makro_logo}" alt="Makro" class="h-5">
                    </a>
                </div>
            </div>
            """ +
        "</div>" if product.get('nutrition') else ""}
    </div>
    """
    
    # Renderizar la tarjeta utilizando streamlit_tailwind
    st_tw(
        text=card_html,
        height="320"
    )

def render_add_product_form(data_manager):
    """
    Renderiza un formulario para agregar nuevos productos
    
    :param data_manager: Instancia de DataManager
    :return: Booleano indicando si se agregó un producto
    """
    st.header("Agregar Nuevo Producto")
    
    # Formulario de URL
    url = st.text_input("URL del producto (Makro Plaza Vea)")
    
    # Campos opcionales
    col1, col2 = st.columns(2)
    
    with col1:
        weight = st.number_input("Peso (gramos)", min_value=1, value=1000)
    
    with col2:
        meat_type = st.selectbox("Tipo de Producto", [''] + MEAT_TYPES)
    
    # Botón de agregar
    if st.button("Agregar Producto"):
        if url:
            url_data = {
                'url': url,
                'weight_gr': weight,
                'type': meat_type if meat_type else None
            }
            try:
                if data_manager.add_product_url(url_data):
                    st.success(f"Producto agregado exitosamente: {url}")
                    return True
                else:
                    st.warning("No se pudo agregar el producto. Verifica la URL.")
            except Exception as e:
                st.error(f"Error al agregar producto: {e}")
        else:
            st.warning("Por favor ingresa una URL válida")
    
    return False

def render_recipe_generator(recipe_generator, selected_products, user_prefs):
    """
    Renderiza la interfaz de generación de recetas
    
    :param recipe_generator: Instancia de RecipeGenerator
    :param selected_products: Productos seleccionados
    :param user_prefs: Preferencias del usuario
    """
    st.header("Generador de Recetas")
    
    # Validar que haya productos seleccionados
    if not selected_products:
        st.warning("Selecciona al menos un producto para generar una receta")
        return
    
    # Preparar ingredientes
    ingredients = {}
    total_protein = 0
    
    for product_url, product in selected_products.items():
        if not product.get('nutrition'):
            st.warning(f"El producto {product['name']} no tiene información nutricional")
            continue
        
        # Calcular consumo diario
        daily_protein_needed = user_prefs['daily_protein'] / len(selected_products)
        grams_to_consume = (daily_protein_needed * 100) / product['nutrition']['protein']
        
        ingredients[product['name']] = grams_to_consume
        total_protein += daily_protein_needed
    
    # Verificar balance de macronutrientes
    if total_protein > user_prefs['daily_protein']:
        st.warning(f"Atención: El consumo de proteína ({total_protein:.1f}g) supera lo recomendado ({user_prefs['daily_protein']:.1f}g)")
    
    # Opciones adicionales de la receta
    col1, col2 = st.columns(2)
    
    with col1:
        meal_type = st.selectbox("Tipo de Comida", [
            "Desayuno", 
            "Almuerzo", 
            "Cena", 
            "Snack/Merienda"
        ])
    
    with col2:
        cuisine_type = st.selectbox("Cocina", [
            "Peruana", 
            "Internacional", 
            "Saludable", 
            "Fitness"
        ])
    
    # Restricciones dietéticas
    dietary_restrictions = st.multiselect(
        "Restricciones Dietéticas", [
            "Sin Gluten", 
            "Vegetariano", 
            "Vegano", 
            "Sin Lácteos"
        ]
    )
    
    # Botón para generar receta
    if st.button("Generar Receta"):
        with st.spinner("Generando receta..."):
            # Preparar contexto de la receta
            recipe_context = {
                "ingredients": ingredients,
                "meal_type": meal_type,
                "cuisine_type": cuisine_type,
                "dietary_restrictions": dietary_restrictions,
                "daily_protein_goal": user_prefs['daily_protein'],
                "daily_carbs_goal": user_prefs['daily_carbs'],
                "daily_fat_goal": user_prefs['daily_fat']
            }
            
            # Generar receta
            try:
                recipe = recipe_generator.generate_recipe(recipe_context)
                
                if recipe:
                    # Mostrar receta
                    st.markdown("### Receta Generada")
                    st.markdown(recipe)
                    
                    # Analizar macronutrientes de la receta
                    # TODO: Implementar análisis de macronutrientes de la receta generada
                else:
                    st.error("No se pudo generar la receta. Intenta de nuevo.")
            
            except Exception as e:
                st.error(f"Error al generar la receta: {e}")

def render_nutrition_comparison(selected_products):
    """
    Renderiza una comparación nutricional de los productos seleccionados
    
    :param selected_products: Diccionario de productos seleccionados
    """
    st.header("Comparación Nutricional")
    
    if not selected_products:
        st.warning("Selecciona productos para comparar")
        return
    
    # Preparar datos para la comparación
    comparison_data = {
        'Producto': [],
        'Proteínas (100g)': [],
        'Carbohidratos (100g)': [],
        'Grasas (100g)': [],
        'Calorías (100g)': []
    }
    
    for product in selected_products.values():
        if product.get('nutrition'):
            nutrition = product['nutrition']
            comparison_data['Producto'].append(product['name'])
            comparison_data['Proteínas (100g)'].append(nutrition.get('protein', 0))
            comparison_data['Carbohidratos (100g)'].append(nutrition.get('carbs', 0))
            comparison_data['Grasas (100g)'].append(nutrition.get('fat', 0))
            comparison_data['Calorías (100g)'].append(nutrition.get('calories', 0))
    
    # Mostrar tabla de comparación
    st.dataframe(comparison_data)
    
    # Gráfico de barras comparativo
    try:
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame(comparison_data)
        
        # Gráfico de barras agrupadas
        fig = px.bar(
            df.melt(id_vars=['Producto'], var_name='Nutriente', value_name='Valor'), 
            x='Producto', 
            y='Valor', 
            color='Nutriente',
            barmode='group',
            title='Comparación Nutricional de Productos'
        )
        
        st.plotly_chart(fig)
    except ImportError:
        st.warning("Instala Plotly para visualizaciones más detalladas")
            