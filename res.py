import streamlit as st
import pandas as pd
from datetime import datetime
import random
from PIL import Image
import io
import base64

# Import the existing database classes
from restaurant import Restaurant
from customer import Member, Customer
from menu_item import MenuItem
from order import Order
from allergic import Allergy
from db_utils import get_db_connection, initialize_database

# Initialize the restaurant
restaurant = Restaurant("Flavorithm Restaurant")

# Setting page config
st.set_page_config(page_title="Flavorithm Restaurant", layout="wide")

# Custom CSS to match the style from the HTML
st.markdown("""
<style>
    /* Global Styles */
    .stButton button {
        background-color: #f0f0f0;
        color: #333;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 5px 15px;
    }
    .stButton button:hover {
        background-color: #e0e0e0;
    }
    .active-button {
        background-color: #c2ffc2 !important;
    }
    
    /* Header */
    .header {
        background-color: #eef3ff;
        padding: 15px;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    /* Sections */
    .section {
        background-color: #eef3ff;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    /* List Items */
    .menu-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    
    /* Main Menu Items */
    .main-menu-item {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Section Titles */
    .section-title {
        font-size: 1.5rem;
        margin-bottom: 15px;
        color: #444;
    }
    
    /* Form inputs */
    div[data-baseweb="input"] {
        background-color: #f9f9f9;
    }
    
    /* Color for active meal button */
    .meal-button-active {
        background-color: #c2ffc2 !important;
    }
    
    /* Counter controls */
    .counter-container {
        display: flex;
        align-items: center;
    }
    .counter-btn {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: white;
        border: 1px solid #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
    .counter-display {
        margin: 0 10px;
    }
    
    /* Arrow icon style */
    .arrow-icon {
        margin-right: 8px;
        color: #aaa;
    }

    /* Sidebar styles */
    [data-testid="stSidebar"] {
        background-color: white;
        padding: 20px;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'member' not in st.session_state:
    st.session_state.member = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'meal_time' not in st.session_state:
    st.session_state.meal_time = "Lunch"
if 'people_count' not in st.session_state:
    st.session_state.people_count = 5
if 'children_count' not in st.session_state:
    st.session_state.children_count = 2
if 'older_count' not in st.session_state:
    st.session_state.older_count = 1

# Mock data for demonstration - we'll use this instead of actual DB data 
# in case the DB connection fails
menu_items = {
    1: {"name": "Tom Yum Kung", "price": 120, "category": "Soup", "popularity": 120},
    2: {"name": "Pad Thai", "price": 100, "category": "Noodle", "popularity": 100},
    3: {"name": "Rice", "price": 93, "category": "Side", "popularity": 93},
    4: {"name": "Fresh Water", "price": 90, "category": "Drink", "popularity": 90},
    5: {"name": "Stir fried Thai basil", "price": 110, "category": "Main", "popularity": 85},
    6: {"name": "Green Curry", "price": 130, "category": "Main", "popularity": 75},
    7: {"name": "Omelette", "price": 100, "category": "Main", "popularity": 100},
    8: {"name": "Fries Pork with Garlic", "price": 99, "category": "Main", "popularity": 99},
    9: {"name": "Som Tam", "price": 80, "category": "Salad", "popularity": 80},
    10: {"name": "Satay", "price": 130, "category": "Appetizer", "popularity": 130}
}

allergies = [
    {"id": 1, "name": "แพ้อาหารทะเล", "description": "Seafood Allergy"},
    {"id": 2, "name": "ไม่ทานเผ็ด", "description": "No Spicy Food"},
    {"id": 3, "name": "แพ้ถั่ว", "description": "Nut Allergy"},
    {"id": 4, "name": "ไม่ทานผัก", "description": "No Vegetables"}
]

# Function to increment counter
def increment_counter(counter_name):
    st.session_state[counter_name] += 1

# Function to decrement counter
def decrement_counter(counter_name):
    if st.session_state[counter_name] > 0:
        st.session_state[counter_name] -= 1

# Function to add item to cart
def add_to_cart(item_id):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id] += 1
    else:
        st.session_state.cart[item_id] = 1

# Function to remove item from cart
def remove_from_cart(item_id):
    if item_id in st.session_state.cart:
        if st.session_state.cart[item_id] > 1:
            st.session_state.cart[item_id] -= 1
        else:
            del st.session_state.cart[item_id]

def get_top_items(items_dict, sort_key="popularity", limit=4):
    """Get top items sorted by a key"""
    sorted_items = sorted(items_dict.items(), key=lambda x: x[1][sort_key], reverse=True)
    return {k: v for k, v in sorted_items[:limit]}

def render_counter(label, counter_name, col):
    """Render a counter with +/- buttons"""
    col.write(label)
    counter_col1, counter_col2, counter_col3 = col.columns([1,1,1])
    
    counter_col1.button("-", key=f"dec_{counter_name}", on_click=decrement_counter, args=(counter_name,))
    counter_col2.write(f"<div style='text-align: center;'>{st.session_state[counter_name]}</div>", unsafe_allow_html=True)
    counter_col3.button("+", key=f"inc_{counter_name}", on_click=increment_counter, args=(counter_name,))

# Set up sidebar
with st.sidebar:
    st.title("Flavorithm Restaurant")
    
    # Check if user is already logged in
    if not st.session_state.member:
        st.write("Please Input Customer ID")
        
        # Member input fields
        member_id = st.text_input("Member ID", key="member_id")
        tel_number = st.text_input("Tel number", key="tel_number")
        
        if st.button("Enter", key="login_button"):
            # Process login - in a real app, this would validate against the database
            if member_id:
                # For demo purposes, automatically log the user in
                st.session_state.member = {
                    "member_id": member_id,
                    "name": "Atisak",
                    "surname": "Tongdeepuṭ",
                    "phone": tel_number or "099-999-9999",
                    "points": 150
                }
                # Force a rerun to update the UI immediately
                st.rerun()
    
    # If member is logged in, show customer info
    if st.session_state.member:
        st.write("Customer Information")
        st.text_input("Name", value=st.session_state.member["name"], disabled=True)
        st.text_input("Surname", value=st.session_state.member["surname"], disabled=True)
        
        st.write(f"Date & Time : {datetime.now().strftime('%A, %B %d, %Y, %H:%M')}")
        
        # Meal time selection
        meal_cols = st.columns(3)
        
        if meal_cols[0].button("Breakfast", 
                             key="breakfast_btn", 
                             help="Select Breakfast",
                             type="secondary" if st.session_state.meal_time != "Breakfast" else "primary"):
            st.session_state.meal_time = "Breakfast"
            
        if meal_cols[1].button("Lunch", 
                             key="lunch_btn", 
                             help="Select Lunch",
                             type="secondary" if st.session_state.meal_time != "Lunch" else "primary"):
            st.session_state.meal_time = "Lunch"
            
        if meal_cols[2].button("Dinner", 
                             key="dinner_btn", 
                             help="Select Dinner",
                             type="secondary" if st.session_state.meal_time != "Dinner" else "primary"):
            st.session_state.meal_time = "Dinner"
        
        # People counter
        render_counter("People in table", "people_count", st)
        
        # Children and Older counters
        col1, col2 = st.columns(2)
        render_counter("Children", "children_count", col1)
        render_counter("Older", "older_count", col2)
        
        if st.button("Enter", key="update_button"):
            st.success("Information updated!")

# Main content
if st.session_state.member:
    # Header with welcome message
    st.markdown(f"""
    <div class="header">
        <h2>Welcome Khun {st.session_state.member["name"]} {st.session_state.member["surname"]}</h2>
        <div style="font-size: 1.5rem;">🛒 {sum(st.session_state.cart.values()) if st.session_state.cart else 0}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content columns
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        # Favorite Dishes Section
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Favorite Dishes</h3>', unsafe_allow_html=True)
        
        favorite_items = get_top_items(menu_items, "popularity", 4)
        for item_id, item in favorite_items.items():
            st.markdown(f"""
            <div class="menu-item">
                <div class="item-name">
                    <span class="arrow-icon">➤</span>
                    <span>{item["name"]}</span>
                </div>
                <span>{item["popularity"]}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recommendation Section
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Recommendation</h3>', unsafe_allow_html=True)
        
        recommended_items = {
            7: menu_items[7],  # Omelette
            8: menu_items[8],  # Fries Pork with Garlic
            9: menu_items[9],  # Som Tam
            10: menu_items[10]  # Satay
        }
        
        for item_id, item in recommended_items.items():
            st.markdown(f"""
            <div class="menu-item">
                <div class="item-name">
                    <span class="arrow-icon">➤</span>
                    <span>{item["name"]}</span>
                </div>
                <span>{item["price"]}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Allergic Food Section
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Allergic Food</h3>', unsafe_allow_html=True)
        
        for allergy in allergies:
            st.markdown(f"""
            <div class="menu-item">
                <div class="item-name">
                    <span class="arrow-icon">➤</span>
                    <span>{allergy["name"]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        # Main Menu Section
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Main Menu</h3>', unsafe_allow_html=True)
        
        for item_id, item in menu_items.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            col1.write(f"**{item['name']}**")
            
            # Get current item count from cart
            item_count = st.session_state.cart.get(item_id, 0)
            
            col2.button("-", key=f"dec_item_{item_id}", on_click=remove_from_cart, args=(item_id,), disabled=item_count == 0)
            col3.write(f"{item_count}")
            col3.button("+", key=f"inc_item_{item_id}", on_click=add_to_cart, args=(item_id,))
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a total amount section
        total_amount = sum(menu_items[item_id]["price"] * qty for item_id, qty in st.session_state.cart.items())
        
        st.markdown(f"""
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>Total: ฿{total_amount}</h3>
            <div style="margin-top: 10px;">
                {sum(st.session_state.cart.values())} items in cart
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Place Order", type="primary"):
            st.success("Order placed successfully!")
            # Here you would create a real order in the database
            # For demo, we'll just clear the cart
            st.session_state.cart = {}
            st.rerun()

# If no member is logged in, show a simple login form in the main area
else:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>Flavorithm Restaurant</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Please Input Customer ID</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            member_id = st.text_input("Member ID")
            tel_number = st.text_input("Tel number")
            
            # Center the submit button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("Enter")
            
            if submitted and member_id:
                st.session_state.member = {
                    "member_id": member_id,
                    "name": "Atisak",
                    "surname": "Tongdeepuṭ",
                    "phone": tel_number or "099-999-9999",
                    "points": 150
                }
                st.rerun()
