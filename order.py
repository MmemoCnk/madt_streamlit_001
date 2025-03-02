from datetime import datetime
from typing import List
from db_utils import get_db_connection
from menu_item import MenuItem
from customer import Customer, Member

class Order:
    def __init__(self, customer: Customer):
        self.order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.customer = customer
        self.items: List[MenuItem] = []
        self.total_amount = 0
        self.status = "Pending"
        self.timestamp = datetime.now()
    
    def add_item(self, item: MenuItem):
        """Add an item to the order, with allergy checking for members"""
        self.items.append(item)
        self.total_amount += item.price
        
        # Check for allergies if customer is a member
        if isinstance(self.customer, Member) and self.customer.allergies:
            allergen_warnings = []
            for allergy in self.customer.allergies:
                if allergy.allergen in item.allergens:
                    allergen_warnings.append(f"{item.name} contains {allergy.allergen} (Severity: {allergy.severity})")
            
            if allergen_warnings:
                # In a real application, you might want to:
                # 1. Ask for confirmation before adding the item
                # 2. Log the warning
                # 3. Or simply return the warnings to be displayed
                return allergen_warnings
        
        return []  # No warnings
    
    def remove_item(self, item: MenuItem):
        if item in self.items:
            self.items.remove(item)
            self.total_amount -= item.price
    
    def complete_order(self):
        self.status = "Completed"
        if isinstance(self.customer, Member):
            points_earned = int(self.total_amount / 10)
            self.customer.add_points(points_earned)
            for item in self.items:
                self.customer.update_favorites(item.id)
        self._save_to_db()
    
    def _save_to_db(self):
        """Save order to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save order
        cursor.execute(
            "INSERT INTO orders (order_id, customer_id, total_amount, status, timestamp) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                self.order_id,
                self.customer.member_id if isinstance(self.customer, Member) else 'NON-MEMBER',
                self.total_amount,
                self.status,
                self.timestamp
            )
        )
        
        # Save order items
        for item in self.items:
            cursor.execute(
                "INSERT INTO order_items (order_id, menu_item_id) VALUES (%s, %s)",
                (self.order_id, item.id)
            )
        
        conn.commit()
        cursor.close()
        conn.close()