import random
from typing import Dict, List
from menu_item import MenuItem
from customer import Member

class RecommendationSystem:
    def __init__(self):
        self.menu_items: Dict[int, MenuItem] = {}
    
    def add_menu_item(self, item: MenuItem):
        self.menu_items[item.id] = item
    
    def get_personal_recommendations(self, member: Member, num_recommendations: int = 3) -> List[MenuItem]:
        if not member.favorite_items:
            return self.get_random_recommendations(num_recommendations)
        
        sorted_favorites = sorted(
            member.favorite_items.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        recommendations = []
        for menu_id, _ in sorted_favorites[:num_recommendations]:
            if menu_id in self.menu_items:
                recommendations.append(self.menu_items[menu_id])
        
        while len(recommendations) < num_recommendations:
            random_item = self.get_random_recommendations(1)[0]
            if random_item not in recommendations:
                recommendations.append(random_item)
        
        return recommendations
    
    def get_random_recommendations(self, num_recommendations: int) -> List[MenuItem]:
        available_items = list(self.menu_items.values())
        return random.sample(
            available_items,
            min(num_recommendations, len(available_items))
        )
