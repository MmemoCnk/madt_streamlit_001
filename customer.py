from typing import List, Dict, Optional
from psycopg2.extras import DictCursor
from db_utils import get_db_connection
from allergic import Allergy

class Customer:
    def __init__(self, name: str, phone: str):
        self.name = name
        self.phone = phone
        self.order_history: List['Order'] = []

class Member(Customer):
    def __init__(self, name: str, phone: str, member_id: str, points: int = 0):
        super().__init__(name, phone)
        self.member_id = member_id
        self.points = points
        self.favorite_items: Dict[int, int] = {}  # menu_id: order_count
        self.allergies: List[Allergy] = []  # List of allergies
    
    def add_points(self, points: int):
        self.points += points
        self._save_to_db()
    
    def use_points(self, points: int) -> bool:
        if self.points >= points:
            self.points -= points
            self._save_to_db()
            return True
        return False
    
    def update_favorites(self, menu_item_id: int):
        if menu_item_id in self.favorite_items:
            self.favorite_items[menu_item_id] += 1
        else:
            self.favorite_items[menu_item_id] = 1
        self._update_favorite_in_db(menu_item_id, self.favorite_items[menu_item_id])
    
    def add_allergy(self, allergen: str, severity: str = "Moderate") -> Allergy:
        """Add an allergy for the member"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get next allergy ID
        cursor.execute("SELECT MAX(allergy_id) FROM member_allergies")
        result = cursor.fetchone()
        next_id = 1 if result[0] is None else result[0] + 1
        
        # Create and save new allergy
        allergy = Allergy(next_id, self.member_id, allergen, severity)
        allergy.save_to_db()
        
        conn.close()
        
        # Add to member's allergies list
        self.allergies.append(allergy)
        return allergy
    
    def remove_allergy(self, allergy_id: int) -> bool:
        """Remove an allergy for the member"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM member_allergies WHERE allergy_id = %s AND member_id = %s",
            (allergy_id, self.member_id)
        )
        
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Remove from member's allergies list if found
        self.allergies = [a for a in self.allergies if a.allergy_id != allergy_id]
        
        return rows_deleted > 0
    
    def get_allergies(self) -> List[Allergy]:
        """Get all allergies for the member"""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute(
            "SELECT * FROM member_allergies WHERE member_id = %s",
            (self.member_id,)
        )
        allergy_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Update member's allergies list
        self.allergies = [
            Allergy(
                allergy_id=data['allergy_id'],
                member_id=data['member_id'],
                allergen=data['allergen'],
                severity=data['severity']
            )
            for data in allergy_data
        ]
        
        return self.allergies
    
    def _save_to_db(self):
        """Update member data in the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE members SET points = %s WHERE member_id = %s",
            (self.points, self.member_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def _update_favorite_in_db(self, menu_item_id: int, count: int):
        """Update favorite item in the database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO favorite_items (member_id, menu_item_id, count) VALUES (%s, %s, %s) "
            "ON CONFLICT (member_id, menu_item_id) DO UPDATE SET count = %s",
            (self.member_id, menu_item_id, count, count)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @classmethod
    def load_from_db(cls, member_id: str) -> Optional['Member']:
        """Load a member from the database"""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Get member info
        cursor.execute(
            "SELECT * FROM members WHERE member_id = %s",
            (member_id,)
        )
        member_data = cursor.fetchone()
        
        if not member_data:
            cursor.close()
            conn.close()
            return None
        
        member = cls(
            member_data['name'],
            member_data['phone'],
            member_data['member_id'],
            member_data['points']
        )
        
        # Get favorite items
        cursor.execute(
            "SELECT menu_item_id, count FROM favorite_items WHERE member_id = %s",
            (member_id,)
        )
        favorite_items = cursor.fetchall()
        
        for item in favorite_items:
            member.favorite_items[item['menu_item_id']] = item['count']
        
        # Get member allergies
        cursor.execute(
            "SELECT * FROM member_allergies WHERE member_id = %s",
            (member_id,)
        )
        allergy_data = cursor.fetchall()
        
        for data in allergy_data:
            member.allergies.append(
                Allergy(
                    allergy_id=data['allergy_id'],
                    member_id=data['member_id'],
                    allergen=data['allergen'],
                    severity=data['severity']
                )
            )
        
        cursor.close()
        conn.close()
        
        return member