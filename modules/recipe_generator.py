# modules/recipe_generator.py
import streamlit as st
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class RecipeGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=st.secrets["GEMINIAPI"]["key"])
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_recipe(self, ingredients):
        try:
            ingredients_text = "\n".join([f"- {name}: {grams:.1f}g" for name, grams in ingredients.items()])
            prompt = f"""Dame una receta peruana para desayuno, almuerzo y cena usando estos ingredientes:
{ingredients_text}

Por favor incluye:
- Nombre de cada plato
- Ingredientes con cantidades
- Pasos de preparación
- Valor nutricional aproximado"""

            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generando receta: {e}")
            return None