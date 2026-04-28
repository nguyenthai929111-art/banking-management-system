import streamlit as st

def display_savings_plan(plan, principal):
    rates = {1: 0.004, 3: 0.015, 6: 0.035, 12: 0.08}
    current_money = principal
    
    st.markdown("### 📋 Lộ trình Đầu tư Tối ưu:")
    
    for step, months in enumerate(reversed(plan)):
        interest_rate = rates.get(months, 0)
        gained = current_money * interest_rate
        
        st.info(f"**Giai đoạn {step + 1}:** Gửi gói **{months} tháng** ➔ Lãi nhận được: **${gained:,.2f}**")
        
        current_money += gained
        
    st.markdown("---")
    profit = current_money - principal
    st.metric("Tổng tiền nhận được dự kiến", f"${current_money:,.2f}", f"+${profit:,.2f} (Lợi nhuận)")
