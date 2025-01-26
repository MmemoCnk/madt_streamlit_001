import streamlit as st
import random
 
st.title('Test Streamlit')
# result1 = st.button('click me!')
# if result1:
#     st.write('you click 1')

# result2 = st.button('click me2!',type='tertiary')
# if result1 & result2:
#     st.write('you click both')

st.write('Hello World!')
 
if st.button('Generate Random Number'):
    random_number = random.randint(1, 100)
    st.write(f'Random Number: {random_number}')