import streamlit as st
import bank_core
import sqlite3
import pandas as pd
import math
import random
import plotly.express as px
from saving_ultis import display_savings_plan

st.set_page_config(page_title="VNU Secure Banking", page_icon="🏦", layout="wide")
if 'logged_in_id' not in st.session_state:
    st.session_state.logged_in_id = None
def calculate_credit_score(balance):
    """Sử dụng hàm Sigmoid để ánh xạ số dư thành điểm tín dụng FICO (300-850)"""
    if balance <= 0: return 300
    k = 0.000002 
    mu = 2000000 
    sigmoid_prob = 1 / (1 + math.exp(-k * (balance - mu)))
    score = 300 + int(550 * sigmoid_prob)
    return score
def evaluate_fraud_risk(amount, current_balance):
    """Đánh giá rủi ro giao dịch bất thường"""
    if amount >= 10000000 or (current_balance > 0 and (amount / current_balance) > 0.8):
        return "HIGH_RISK"
    elif amount >= 5000000 or (current_balance > 0 and (amount / current_balance) > 0.5):
        return "MEDIUM_RISK"
    return "SAFE"

def generate_virtual_card(user_id):
    random.seed(user_id)
    card_number = f"{random.randint(10000, 99999)} {random.randint(10000, 99999)}"

    cvv = random.randint(100, 999)
    expiry = "12/30"
    return card_number, cvv, expiry

def generate_amortization_schedule(principal, annual_rate, months):
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)

    schedule = []
    balance = principal
    for month in range(1, months + 1):
        interest = balance * monthly_rate
        principal_payment = emi - interest
        balance -= principal_payment
        if balance < 0: balance = 0
        schedule.append({
            "Tháng": month,
            "Tiền phải trả ($)": emi,
            "Trả gốc ($)": principal_payment,
            "Trả lãi ($)": interest,
            "Dư nợ còn lại ($)": balance
        })
    return pd.DataFrame(schedule)

@st.cache_resource
def get_bank_engine():
    return bank_core.BankManager()

bank = get_bank_engine()
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=100)
    if st.session_state.get('logged_in_id') is None:
        st.header("🔑 Đăng nhập")
        login_id = st.number_input("ID Tài khoản", min_value=1, step=1)
        login_pwd = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", type="primary"):
            auth_status = bank.authenticate(int(login_id), login_pwd)
            if auth_status == 1:
                bank.process_scheduled_transfers()
                st.session_state.logged_in_id = int(login_id)
                st.rerun()
            elif auth_status == -1:
@@ -204,169 +205,191 @@
                    st.warning("⚠️ Cảnh báo: Bạn đang chuyển đi một lượng tài sản lớn. Vui lòng kiểm tra kỹ ID người nhận.")
                    if bank.transfer(my_id, target_id, amount_ck):
                        st.success(f"Đã chuyển ${amount_ck:,.2f} đến ID {target_id} thành công.")
                        import time; time.sleep(1.5); st.rerun()
                else:
                    if bank.transfer(my_id, target_id, amount_ck):
                        st.success(f"Đã chuyển ${amount_ck:,.2f} đến ID {target_id} an toàn!")
                        import time; time.sleep(1.5); st.rerun()
                    else:
                        st.error("Thất bại! Sai ID hoặc không đủ số dư.")
        st.markdown("---") 
        with st.expander("⏱️ Cài đặt lệnh Chuyển khoản Định kỳ (Hàng tháng)"):
            st.write("Sử dụng để tự động thanh toán tiền nhà, tiền mạng, nợ định kỳ...")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                sched_to_id = st.number_input("ID Người nhận (Định kỳ)", min_value=1, step=1, key="sched_to")
                sched_amount = st.number_input("Số tiền mỗi tháng ($)", min_value=1.0, step=10.0, key="sched_amt")
            with col_s2:
                start_date = st.date_input("Ngày thực hiện lần đầu")
                
            if st.button("Lưu lệnh định kỳ", type="primary"):
                if sched_to_id == my_id:
                    st.error("Không thể tự chuyển tiền cho chính mình!")
                else:
                    if bank.add_scheduled_transfer(my_id, int(sched_to_id), sched_amount, str(start_date)):
                        st.success(f"Đã lưu thành công! Lần tự động trừ tiền đầu tiên sẽ diễn ra vào {start_date}")
                        st.balloons()
                    else:
                        st.error("Lỗi: Không thể lưu lệnh. Vui lòng kiểm tra lại thông tin.")
    with tab_vay:
        st.subheader("Hệ thống Giải ngân Tự động (AI Scoring)")
        current_bal = bank.get_balance(my_id)
        credit_score = calculate_credit_score(current_bal)
        st.metric("Điểm tín dụng (FICO Score)", f"{credit_score} / 850")
        max_loan = 0
        if credit_score < 500:
            st.error("Hồ sơ tín dụng Rủi ro cao. Bạn không đủ điều kiện vay vốn.")
        elif credit_score < 700:
            max_loan = current_bal * 0.5
            st.warning(f"Hồ sơ Trung bình. Hạn mức vay tối đa của bạn là: **${max_loan:,.2f}**")
        else:
            max_loan = current_bal * 2.0
            st.success(f"Hồ sơ Xuất sắc! Hạn mức vay tín chấp của bạn lên tới: **${max_loan:,.2f}**")
        if max_loan > 0:
            loan_amount = st.number_input("Khoản tiền muốn vay ($)", min_value=1.0, max_value=float(max_loan), step=1000.0, key="loan_amount")
            st.markdown("---")
            st.markdown("### 📅 Giả lập Lịch trả nợ")
            loan_term = st.slider("Thời hạn vay (tháng)", 6, 60, 12)
            interest_rate = 12.0    
            st.info(f"Lãi suất áp dụng: **{interest_rate}% / năm** (Dư nợ giảm dần)")
            df_schedule = generate_amortization_schedule(loan_amount, interest_rate, loan_term)
            st.dataframe(df_schedule.style.format("{:.2f}"), use_container_width=True, hide_index=True)
            st.markdown("---")
            if st.button("Gửi yêu cầu giải ngân", type="primary"):
                if bank.deposit(my_id, loan_amount): 
                    st.success(f"🎉 Hệ thống tự động duyệt! Đã cộng ${loan_amount:,.2f} vào tài khoản.")
                    st.balloons()
                    import time
                    time.sleep(1.5) 
                    st.rerun()
    with tab_tiet_kiem:
        st.subheader("🤖 Cố vấn Gửi tiết kiệm (AI DP)")
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            target_months = st.slider("Thời gian muốn gửi (Tháng)", 1, 60, 15)
        with col_input2:
            principal = st.number_input("Số tiền muốn gửi ($)", min_value=100.0, step=100.0, value=1000.0)
        if st.button("Tính toán Lộ trình Tối ưu", type="primary"):
            plan = bank.get_optimal_savings_plan(int(target_months))
            if not plan:
                st.error("Không thể tìm ra kế hoạch phù hợp.")
            else:
                st.success("Ting ting! Hệ thống đã tìm ra chiến lược lãi kép tốt nhất!")
                display_savings_plan(plan, principal)
    with tab_history:
        st.subheader("Lịch sử biến động số dư")
        conn = sqlite3.connect('bank_data.db')
        df = pd.read_sql_query(f"SELECT * FROM Transactions WHERE from_id={my_id} OR to_id={my_id}", conn)
        conn.close()

        if not df.empty:
            df['type_val'] = df.apply(lambda x: x['amount'] if x['to_id'] == my_id else -x['amount'], axis=1)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            import plotly.express as px
            fig = px.bar(df, x='timestamp', y='type_val', 
                         color='type_val', 
                         title="Biến động số dư theo thời gian",
                         labels={'type_val': 'Số tiền ($)', 'timestamp': 'Thời gian'},
                         color_continuous_scale=['red', 'green'])
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True)
        else:
            st.info("Bạn chưa có giao dịch nào.")
    if my_id == 1:
        with tab_admin:
            #Chức năng can thiệp data_bank
            st.subheader("Bảng điều khiển Server Database")
            st.warning("Khu vực này hiển thị dữ liệu thực tế đang chạy trên Server.")
            try:
                conn = sqlite3.connect('bank_data.db')
                df = pd.read_sql_query("SELECT id, name, balance, password FROM Accounts", conn)
                st.markdown("**1. Dữ liệu Bảng 'Accounts'**")
                st.dataframe(df, use_container_width=True, hide_index=True)
                total_assets = df['balance'].sum()
                st.metric("Tổng tài sản đang quản lý", f"${total_assets:,.2f}")
                conn.close()
                st.markdown("**2. Trích xuất Database**")
                with open("bank_data.db", "rb") as file:
                    st.download_button(
                        label="📥 Tải file bank_data.db của Server về máy",
                        data=file,
                        file_name="Cloud_bank_data.db",
                        mime="application/octet-stream",
                        type="primary"
                    )
            except Exception as e:
                st.error(f"Chưa có dữ liệu hoặc Lỗi kết nối: {e}")
            #Dashboard phân tích dữ liệu
            st.title("🛡️ Trung tâm Điều hành Ngân hàng")
            try:
                conn = sqlite3.connect('bank_data.db')
                df = pd.read_sql_query("SELECT id, name, balance FROM Accounts", conn)
                df_trans = pd.read_sql_query("SELECT * FROM Transactions", conn)
                conn.close()
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Tổng số khách hàng", len(df))
                with col_m2:
                    total_assets = df['balance'].sum()
                    st.metric("Tổng tài sản hệ thống", f"${total_assets:,.2f}")
                with col_m3:
                    avg_bal = df['balance'].mean()
                    st.metric("Số dư trung bình", f"${avg_bal:,.2f}")

                st.markdown("---")
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.subheader("📊 Phân bổ số dư tài khoản")
                    fig_hist = px.histogram(df, x="balance", nbins=20, 
                                            labels={'balance': 'Số dư ($)'},
                                            color_discrete_sequence=['#636EFA'])
                    st.plotly_chart(fig_hist, use_container_width=True)
                with col_chart2:
                    st.subheader("🍰 Tỷ trọng tài sản cá nhân")
                    fig_pie = px.pie(df, values='balance', names='name', hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                st.subheader("📈 Xu hướng dòng tiền (Transactions)")
                if not df_trans.empty:
                    df_trans['timestamp'] = pd.to_datetime(df_trans['timestamp'])
                    daily_trans = df_trans.groupby(df_trans['timestamp'].dt.date)['amount'].sum().reset_index()
                    fig_line = px.line(daily_trans, x='timestamp', y='amount',
                                       labels={'timestamp': 'Ngày', 'amount': 'Tổng lượng giao dịch ($)'},
                                       markers=True)
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu giao dịch để phân tích xu hướng.")
                st.markdown("---")
                with st.expander("🔍 Xem danh sách tài khoản chi tiết"):
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Lỗi phân tích dữ liệu: {e}")
            #Ép đổi mật khẩu
            st.markdown("---")
            st.markdown("**3. Quyền năng Admin: Khôi phục Mật khẩu**")
            st.info("Vì lý do bảo mật, Admin không thể xem mật khẩu gốc, nhưng có quyền Đặt lại mật khẩu của bất kỳ ID nào về mặc định là: '123456'")

            reset_id = st.number_input("Nhập ID Khách hàng cần Reset:", min_value=1, step=1)
            if st.button("🔥 Ép Đặt lại Mật khẩu", type="primary"):
                try:
                    conn = sqlite3.connect('bank_data.db')
                    cursor = conn.cursor()
                    def python_hash(pwd):
                        h = 5381
                        for char in pwd:
                            h = ((h << 5) + h) + ord(char)
                            h = h & 0xFFFFFFFF
                        return f"{h:08x}"

                    default_hashed = python_hash("123456")

                    cursor.execute("UPDATE Accounts SET password = ? WHERE id = ?", (default_hashed, reset_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        st.success(f"Đã reset thành công! Khách hàng ID {reset_id} giờ có thể đăng nhập bằng pass: 123456")
                        st.balloons()
                    else:
                        st.error("Không tìm thấy ID này trong hệ thống!")
                    conn.close()
                except Exception as e:
                    st.error(f"Lỗi: {e}")
