# modules/recipe_generator.py
import streamlit as st
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class RecipeGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=st.secrets["GEMINIAPI"]["key"])
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_recipe(self, recipe_context):
        try:
            # Construcción de la lista de ingredientes
            ingredients = recipe_context.get('ingredients', {})
            if not ingredients:
                logger.warning("No se proporcionaron ingredientes para generar la receta.")
                return "No se proporcionaron ingredientes para generar la receta."

            ingredients_text = "\n".join([f"- {name}: {grams:.1f}g" for name, grams in ingredients.items()])
            meal_type = recipe_context.get('meal_type', 'cualquier comida')
            cuisine_type = recipe_context.get('cuisine_type', 'Peruana')
            dietary_restrictions = recipe_context.get('dietary_restrictions', [])

            if dietary_restrictions:
                dietary_text = ", ".join(dietary_restrictions)
                dietary_clause = f"teniendo en cuenta las siguientes restricciones dietéticas: {dietary_text}"
            else:
                dietary_clause = "sin restricciones dietéticas"

            # Construcción del prompt
            prompt = f"""Dame una receta {cuisine_type.lower()} para {meal_type.lower()} {dietary_clause} usando estos ingredientes:
{ingredients_text}

Por favor incluye:
- Nombre de cada plato
- Ingredientes con cantidades
- Pasos de preparación
- Valor nutricional aproximado"""

            logger.debug(f"Prompt para la API: {prompt}")

            # Generar contenido usando la API
            response = self.model.generate_content(prompt)
            if hasattr(response, 'text'):
                return response.text
            else:
                logger.error("La respuesta de la API no contiene el atributo 'text'.")
                return None

        except Exception as e:
            logger.error(f"Error generando receta: {e}")
            return None