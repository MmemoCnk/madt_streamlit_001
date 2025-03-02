from typing import Dict, List, Optional
from psycopg2.extras import DictCursor
from db_utils import get_db_connection
from menu_item import MenuItem
from customer import Customer, Member
from order import Order
from recommendation_system import RecommendationSystem

class Restaurant:
    def __init__(self, name: str):
        self.name = name
        self.menu_items: Dict[int, MenuItem] = self._load_menu_items_from_db()
        self.members: Dict[str, Member] = self._load_members_from_db()
        self.orders: List[Order] = []
        self.recommendation_system = RecommendationSystem()
        
        # Initialize recommendation system with menu items
        for item in self.menu_items.values():
            self.recommendation_system.add_menu_item(item)
    
    def _load_menu_items_from_db(self) -> Dict[int, MenuItem]:
        """Load all menu items from database"""
        menu_items = {}
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute("SELECT * FROM menu_items")
        items = cursor.fetchall()
        
        for item in items:
            menu_item = MenuItem(
                id=item['id'],
                name=item['name'],
                price=float(item['price']),
                category=item['category']
            )
            
            # Load allergens for menu item
            cursor.execute(
                "SELECT allergen FROM menu_allergens WHERE menu_item_id = %s",
                (menu_item.id,)
            )
            allergen_data = cursor.fetchall()
            
            menu_item.allergens = [data['allergen'] for data in allergen_data]
            menu_items[menu_item.id] = menu_item
        
        cursor.close()
        conn.close()
        
        return menu_items
    
    def _load_members_from_db(self) -> Dict[str, Member]:
        """Load all members from database"""
        members = {}
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute("SELECT * FROM members")
        member_data = cursor.fetchall()
        
        for data in member_data:
            member = Member(
                name=data['name'],
                phone=data['phone'],
                member_id=data['member_id'],
                points=data['points']
            )
            
            # Get favorite items
            cursor.execute(
                "SELECT menu_item_id, count FROM favorite_items WHERE member_id = %s",
                (member.member_id,)
            )
            favorite_items = cursor.fetchall()
            
            for item in favorite_items:
                member.favorite_items[item['menu_item_id']] = item['count']
            
            # Get allergies
            cursor.execute(
                "SELECT * FROM member_allergies WHERE member_id = %s",
                (member.member_id,)
            )
            allergy_data = cursor.fetchall()
            
            from allergic import Allergy
            for allergy in allergy_data:
                member.allergies.append(
                    Allergy(
                        allergy_id=allergy['allergy_id'],
                        member_id=allergy['member_id'],
                        allergen=allergy['allergen'],
                        severity=allergy['severity']
                    )
                )
            
            members[member.member_id] = member
        
        cursor.close()
        conn.close()
        
        return members
    
    def add_menu_item(self, item: MenuItem):
        self.menu_items[item.id] = item
        self.recommendation_system.add_menu_item(item)
        item.save_to_db()
    
    def register_member(self, name: str, phone: str) -> Member:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get next member ID
        cursor.execute("SELECT COUNT(*) FROM members")
        count = cursor.fetchone()[0]
        member_id = f"M{count + 1:04d}"
        
        # Insert new member
        cursor.execute(
            "INSERT INTO members (member_id, name, phone, points) VALUES (%s, %s, %s, %s)",
            (member_id, name, phone, 0)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        member = Member(name, phone, member_id)
        self.members[member_id] = member
        return member
    
    def get_member(self, member_id: str) -> Optional[Member]:
        member = self.members.get(member_id)
        if not member:
            member = Member.load_from_db(member_id)
            if member:
                self.members[member_id] = member
        return member
    
    def create_order(self, customer: Customer) -> Order:
        order = Order(customer)
        self.orders.append(order)
        return order
    
    def get_recommendations(self, member: Member) -> List[MenuItem]:
        return self.recommendation_system.get_personal_recommendations(member)
    
    def check_menu_item_allergens(self, menu_item_id: int, member: Member) -> List[str]:
        """Check if a menu item contains allergens that a member is allergic to"""
        menu_item = self.menu_items.get(menu_item_id)
        if not menu_item or not member.allergies:
            return []
        
        warnings = []
        for allergy in member.allergies:
            if allergy.allergen in menu_item.allergens:
                warnings.append(f"{menu_item.name} contains {allergy.allergen} (Severity: {allergy.severity})")
        
        return warnings