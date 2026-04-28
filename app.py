import streamlit as st
import bank_core
import sqlite3
import pandas as pd
import math

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
@st.cache_resource
def get_bank_engine():
    return bank_core.BankManager()

bank = get_bank_engine()
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=100)
    if st.session_state.logged_in_id is None:
        st.header("🔑 Đăng nhập")
        login_id = st.number_input("ID Tài khoản", min_value=1, step=1)
        login_pwd = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", type="primary"):
            if bank.authenticate(login_id, login_pwd):
                st.session_state.logged_in_id = login_id
                st.rerun()
            else:
                st.error("Sai ID hoặc mật khẩu!")
    else:
        st.success(f"Đang đăng nhập ID: {st.session_state.logged_in_id}")
        if st.button("Đăng xuất"):
            st.session_state.logged_in_id = None
            st.rerun()
st.title("🏦 Hệ Thống Ngân Hàng VNU")

if st.session_state.logged_in_id is None:
    st.info("Vui lòng đăng nhập từ thanh bên trái để sử dụng dịch vụ hoặc tạo tài khoản mới bên dưới.")
    
    with st.expander("📝 Mở tài khoản mới", expanded=True):
        new_name = st.text_input("Họ và Tên")
        new_pwd = st.text_input("Thiết lập mật khẩu", type="password")
        init_bal = st.number_input("Nạp tiền ban đầu ($)", min_value=0.0, step=100.0)
        
        if st.button("Xác nhận đăng ký", type="primary"):
            if new_name.strip() and new_pwd.strip():
                res_id = bank.create_account(new_name, init_bal, new_pwd)
                st.success(f"Tạo thành công! Mã ID của bạn là **{res_id}**. Hãy dùng ID này để đăng nhập.")
                st.balloons()
            else:
                st.warning("Vui lòng điền đầy đủ Tên và Mật khẩu!")

else:
    my_id = st.session_state.logged_in_id
    if my_id == 1:
        tab_info, tab_giao_dich, tab_chuyen_khoan, tab_vay, tab_history, tab_admin = st.tabs([
            "📊 Thông tin", "💸 Giao dịch", "🔄 Chuyển khoản", "🏦 Vay VIP", "🧾 Sao kê", "🛠️ Admin DB"
        ])
    else:
        tab_info, tab_giao_dich, tab_chuyen_khoan, tab_vay, tab_history = st.tabs([
            "📊 Thông tin", "💸 Giao dịch", "🔄 Chuyển khoản", "🏦 Vay VIP", "🧾 Sao kê"
        ])
    
    with tab_info:
        st.subheader("Tài khoản của bạn")
        bal = bank.get_balance(my_id)
        st.metric("Số dư khả dụng", f"${bal:,.2f}")
    with tab_giao_dich:
        st.subheader("Giao dịch Nạp / Rút")
        amount_gd = st.number_input("Nhập số tiền ($)", min_value=1.0, step=50.0, key="gd_amount")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Nạp tiền", use_container_width=True, type="primary"):
                if bank.deposit(my_id, amount_gd):
                    st.success(f"Nạp thành công ${amount_gd:,.2f}!")
                else:
                    st.error("Giao dịch thất bại.")
        with col2:
            if st.button("Rút tiền", use_container_width=True):
                if bank.withdraw(my_id, amount_gd):
                    st.success(f"Rút thành công ${amount_gd:,.2f}!")
                else:
                    st.error("Thất bại! Không đủ số dư.")
    with tab_chuyen_khoan:
        st.subheader("Chuyển tiền & Quét rủi ro")
        target_id = st.number_input("ID Người nhận", min_value=1, step=1, key="target_id")
        amount_ck = st.number_input("Số tiền chuyển ($)", min_value=1.0, step=50.0, key="ck_amount")
        
        if st.button("Xác nhận chuyển", type="primary"):
            if target_id == my_id:
                st.warning("Không thể tự chuyển tiền cho chính mình.")
            else:
                current_bal = bank.get_balance(my_id)
                risk_level = evaluate_fraud_risk(amount_ck, current_bal)
                if risk_level == "HIGH_RISK":
                    st.error("🚨 CẢNH BÁO BẢO MẬT: Giao dịch có dấu hiệu bất thường (Số tiền quá lớn hoặc chiếm >80% tài sản). Hệ thống tạm khóa giao dịch này để bảo vệ tài sản của bạn!")
                elif risk_level == "MEDIUM_RISK":
                    st.warning("⚠️ Cảnh báo: Bạn đang chuyển đi một lượng tài sản lớn. Vui lòng kiểm tra kỹ ID người nhận.")
                    if bank.transfer(my_id, target_id, amount_ck):
                        st.success(f"Đã chuyển ${amount_ck:,.2f} đến ID {target_id} thành công.")
                else:
                    if bank.transfer(my_id, target_id, amount_ck):
                        st.success(f"Đã chuyển ${amount_ck:,.2f} đến ID {target_id} an toàn!")
                    else:
                        st.error("Thất bại! Sai ID hoặc không đủ số dư.")
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
            if st.button("Gửi yêu cầu giải ngân", type="primary"):
                if bank.request_loan(my_id, loan_amount):
                    st.success(f"🎉 Hệ thống tự động duyệt! Đã cộng ${loan_amount:,.2f} vào tài khoản.")
                    st.balloons()
    with tab_history:
        st.subheader("Lịch sử biến động số dư")
        raw_history = bank.get_history(int(my_id))
        
        if not raw_history:
            st.info("Bạn chưa thực hiện giao dịch nào.")
        else:
            df_history = pd.DataFrame(raw_history, columns=["Loại", "Từ ID", "Đến ID", "Số tiền ($)", "Thời gian"])
            df_history["Số tiền ($)"] = df_history["Số tiền ($)"].apply(lambda x: f"{float(x):,.2f}")
            
            st.dataframe(df_history, use_container_width=True, hide_index=True)
            csv = df_history.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Tải sao kê (.csv)", data=csv, file_name=f"saoke_{my_id}.csv", mime="text/csv")
    if my_id == 1:
        with tab_admin:
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
