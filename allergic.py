from typing import Optional
from psycopg2.extras import DictCursor
from db_utils import get_db_connection

class Allergy:
    """
    Class to represent a food allergy for a member
    """
    def __init__(self, allergy_id: int, member_id: str, allergen: str, severity: str):
        self.allergy_id = allergy_id
        self.member_id = member_id
        self.allergen = allergen
        self.severity = severity  # 'Mild', 'Moderate', 'Severe'
    
    def save_to_db(self):
        """Save allergy to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO member_allergies (allergy_id, member_id, allergen, severity) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (allergy_id) DO UPDATE SET allergen = %s, severity = %s",
            (self.allergy_id, self.member_id, self.allergen, self.severity, self.allergen, self.severity)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def load_from_db(allergy_id: int) -> Optional['Allergy']:
        """Load an allergy from the database"""
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        cursor.execute(
            "SELECT * FROM member_allergies WHERE allergy_id = %s",
            (allergy_id,)
        )
        allergy_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if allergy_data:
            return Allergy(
                allergy_id=allergy_data['allergy_id'],
                member_id=allergy_data['member_id'],
                allergen=allergy_data['allergen'],
                severity=allergy_data['severity']
            )
        return None