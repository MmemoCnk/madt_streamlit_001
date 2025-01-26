import streamlit as st
import random
 
st.title('Test Streamlit')
st.write('Hello World!')
 
if st.button('Generate Random Number'):
    random_number = random.randint(1, 100)
    st.write(f'Random Number: {random_number}')