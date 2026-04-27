import streamlit as st
import bank_core
import sqlite3
import pandas as pd
st.set_page_config(page_title="VNU Secure Banking", page_icon="🏦", layout="wide")
if 'logged_in_id' not in st.session_state:
    st.session_state.logged_in_id = None

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
    tab_info, tab_giao_dich, tab_chuyen_khoan, tab_vay, tab_admin = st.tabs([
        "📊 Thông tin", "💳 Nạp / Rút", "🔄 Chuyển khoản", "🏦 Vay VIP", "🛠️ Admin DB"
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
        st.subheader("Chuyển tiền nội bộ")
        target_id = st.number_input("ID Người nhận", min_value=1, step=1, key="target_id")
        amount_ck = st.number_input("Số tiền chuyển ($)", min_value=1.0, step=50.0, key="ck_amount")
        
        if st.button("Xác nhận chuyển", type="primary"):
            if target_id == my_id:
                st.warning("Không thể tự chuyển tiền cho chính mình.")
            elif bank.transfer(my_id, target_id, amount_ck):
                st.success(f"Đã chuyển ${amount_ck:,.2f} đến ID {target_id}!")
                st.balloons()
            else:
                st.error("Thất bại! Sai ID người nhận hoặc không đủ số dư.")
    with tab_vay:
        st.subheader("Hệ thống Giải ngân Tự động")
        st.warning("⚠️ **Điều kiện:** Số dư tài khoản phải trên **$5,000,000**.")
        loan_amount = st.number_input("Khoản tiền muốn vay ($)", min_value=1000.0, step=1000.0, key="loan_amount")
        
        if st.button("Gửi yêu cầu", type="primary"):
            if bank.request_loan(my_id, loan_amount):
                st.success(f"🎉 Duyệt thành công! Đã cộng ${loan_amount:,.2f} vào tài khoản.")
                st.balloons()
            else:
                st.error("❌ Từ chối hồ sơ: Bạn chưa đạt mức VIP.")
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
