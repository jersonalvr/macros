import math
from typing import Dict, Any

def calculate_daily_consumption(protein_needed: float, protein_per_100g: float, weight_gr: int) -> Dict[str, float]:
    """
    Calcula el consumo diario de un producto basado en los requerimientos de proteína
    
    :param protein_needed: Proteína diaria necesaria
    :param protein_per_100g: Proteína por 100g del producto
    :param weight_gr: Peso del producto en gramos
    :return: Diccionario con información de consumo
    """
    # Calcular gramos a consumir diariamente
    total_grams_needed = (protein_needed * 100) / protein_per_100g
    
    # Calcular número de unidades
    units_daily = total_grams_needed / weight_gr
    
    return {
        'grams': total_grams_needed,
        'units': units_daily,
        'protein_consumed': protein_needed,
        'protein_per_100g': protein_per_100g
    }

def calculate_optimal_purchase(
    units_daily: float, 
    regular_price: float, 
    promo_price: float = None, 
    promo_units: int = None, 
    days: int = 30
) -> Dict[str, Any]:
    """
    Calcula la compra óptima considerando precios regulares y promocionales
    
    :param units_daily: Unidades consumidas diariamente
    :param regular_price: Precio regular por unidad
    :param promo_price: Precio promocional
    :param promo_units: Número de unidades en promoción
    :param days: Días del mes
    :return: Diccionario con información de compra óptima
    """
    # Calcular unidades totales para el mes
    total_units_needed = units_daily * days
    total_units_rounded = math.ceil(total_units_needed)
    
    # Si no hay promoción, calcular compra normal
    if not promo_price or not promo_units:
        return {
            'units': total_units_rounded,
            'total_cost': total_units_rounded * regular_price,
            'daily_cost': (total_units_rounded * regular_price) / days,
            'strategy': 'regular'
        }
    
    # Calcular estrategia con promoción
    promo_sets = total_units_needed // promo_units
    remaining_units = total_units_needed % promo_units
    
    # Calcular costo total
    promo_cost = promo_sets * (promo_price * promo_units)
    regular_cost = math.ceil(remaining_units) * regular_price
    total_cost = promo_cost + regular_cost
    
    return {
        'units': total_units_rounded,
        'promo_sets': promo_sets,
        'promo_units': promo_units,
        'remaining_units': math.ceil(remaining_units),
        'total_cost': total_cost,
        'daily_cost': total_cost / days,
        'strategy': 'mixed',
        'savings_percentage': calculate_savings_percentage(
            total_units_rounded * regular_price, 
            total_cost
        )
    }

def calculate_savings_percentage(original_price: float, discounted_price: float) -> float:
    """
    Calcula el porcentaje de ahorro
    
    :param original_price: Precio original
    :param discounted_price: Precio con descuento
    :return: Porcentaje de ahorro
    """
    if original_price <= 0:
        return 0.0
    
    savings = original_price - discounted_price
    savings_percentage = (savings / original_price) * 100
    
    return round(savings_percentage, 2)

def calculate_macronutrient_balance(
    selected_products: Dict[str, Dict[str, Any]], 
    daily_goals: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calcula el balance de macronutrientes de los productos seleccionados
    
    :param selected_products: Diccionario de productos seleccionados
    :param daily_goals: Objetivos diarios de macronutrientes
    :return: Diccionario con balance de macronutrientes
    """
    total_macros = {
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'calories': 0.0
    }
    
    for product in selected_products.values():
        nutrition = product.get('nutrition', {})
        weight_factor = product.get('weight_gr', 1000) / 100
        
        total_macros['protein'] += (nutrition.get('protein', 0) * weight_factor)
        total_macros['carbs'] += (nutrition.get('carbs', 0) * weight_factor)
        total_macros['fat'] += (nutrition.get('fat', 0) * weight_factor)
        total_macros['calories'] += (nutrition.get('calories', 0) * weight_factor)
    
    # Calcular porcentajes
    balance = {
        'current': total_macros,
        'goals': daily_goals,
        'percentages': {
            'protein': (total_macros['protein'] / daily_goals['daily_protein']) * 100,
            'carbs': (total_macros['carbs'] / daily_goals['daily_carbs']) * 100,
            'fat': (total_macros['fat'] / daily_goals['daily_fat']) * 100
        },
        'status': {}
    }
    
    # Evaluar estado de cada macronutriente
    for macro in ['protein', 'carbs', 'fat']:
        if balance['percentages'][macro] < 80:
            balance['status'][macro] = 'low'
        elif balance['percentages'][macro] > 120:
            balance['status'][macro] = 'high'
        else:
            balance['status'][macro] = 'balanced'
    
    return balance