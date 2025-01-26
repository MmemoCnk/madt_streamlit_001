import streamlit as st
import random
import datetime 

st.set_page_config(layout='wide')
st.title('Test Streamlit')


result1 = st.button('click me1!')
if result1:
    st.write('you click on 1')

result2 = st.button('click me2!',type='tertiary')
if result1 and result2:
    st.write('you click both')

st.button("Reset",type='primary')

# st.write('Hello World!')
 
# if st.button('Generate Random Number'):
#     random_number = random.randint(1, 100)
#     st.write(f'Random Number: {random_number}')