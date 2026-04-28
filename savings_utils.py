import streamlit as st
def display_savings_plan(plan, principal):
    """
    Hàm xử lý logic hiển thị và tính toán lợi nhuận từ kế hoạch của C++
    """
    rates = {1: 0.004, 3: 0.015, 6: 0.035, 12: 0.08}
    current_money = principal
    
    st.markdown("### 📋 Lộ trình của bạn:")
    for step, months in enumerate(reversed(plan)):
        interest_rate = rates.get(months, 0)
        gained = current_money * interest_rate
        
        st.markdown(f"""
        **Giai đoạn {step + 1}:** - Gửi gói: **{months} tháng**
        - Lãi suất nhận được: **${gained:,.2f}**
        """)
        current_money += gained 
    st.markdown("---")
    profit = current_money - principal
    st.metric("Tổng tiền nhận được dự kiến", f"${current_money:,.2f}", f"+${profit:,.2f} (Lợi nhuận)")
    return current_money
    git rm --cached tên_file

