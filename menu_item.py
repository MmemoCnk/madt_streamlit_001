from typing import Optional, List
from psycopg2.extras import DictCursor
from db_utils import get_db_connection

class MenuItem:
    def __init__(self, id: int, name: str, price: float, category: str, allergens: List[str] = None):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
        self.allergens = allergens or []  # List of potential allergens in this item
    
    def add_allergen(self, allergen: str):
        """Add an allergen to this menu item"""
        if allergen not in self.allergens:
            self.allergens.append(allergen)
            self._save_allergens_to_db()
    
    def remove_allergen(self, allergen: str):
        """Remove an allergen from this menu item"""
        if allergen in self.allergens:
            self.allergens.remove(allergen)
            self._save_allergens_to_db()
    
    def _save_allergens_to_db(self):
        """Save menu item allergens to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First delete existing allergens
        cursor.execute(
            "DELETE FROM menu_allergens WHERE menu_item_id = %s",
            (self.id,)
        )
        
        # Then insert current allergens
        for allergen in self.allergens:
            cursor.execute(
                "INSERT INTO menu_allergens (menu_item_id, allergen) VALUES (%s, %s)",
                (self.id, allergen)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def load_from_db(menu_id: int) -> Optional['MenuItem']:
        """Load a menu item from the database"""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute(
            "SELECT * FROM menu_items WHERE id = %s",
            (menu_id,)
        )
        item = cursor.fetchone()
        
        if not item:
            cursor.close()
            conn.close()
            return None
        
        menu_item = MenuItem(
            id=item['id'],
            name=item['name'],
            price=float(item['price']),
            category=item['category']
        )
        
        # Get allergens
        cursor.execute(
            "SELECT allergen FROM menu_allergens WHERE menu_item_id = %s",
            (menu_id,)
        )
        allergen_data = cursor.fetchall()
        
        menu_item.allergens = [data['allergen'] for data in allergen_data]
        
        cursor.close()
        conn.close()
        
        return menu_item
    
    def save_to_db(self):
        """Save menu item to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO menu_items (id, name, price, category) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET name = %s, price = %s, category = %s",
            (self.id, self.name, self.price, self.category, self.name, self.price, self.category)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Save allergens
        self._save_allergens_to_db()