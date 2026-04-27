#include "bank_logic.hpp"
#include <stdexcept>

void BankManager::execute_query(const std::string& sql) {
    char* errMsg = nullptr;
    if (sqlite3_exec(db, sql.c_str(), nullptr, nullptr, &errMsg) != SQLITE_OK) {
        std::string error = errMsg;
        sqlite3_free(errMsg);
        throw std::runtime_error("Lỗi SQL: " + error);
    }
}

BankManager::BankManager() {
    if (sqlite3_open("bank_data.db", &db) != SQLITE_OK) {
        throw std::runtime_error("Không thể mở Database!");
    }
    std::string create_table_sql = 
        "CREATE TABLE IF NOT EXISTS Accounts ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL, "
        "balance REAL NOT NULL,"
        "password TEXT NOT NULL);";
    execute_query(create_table_sql);
}

BankManager::~BankManager() {
    sqlite3_close(db);
}

int BankManager::create_account(const std::string& name, double initial_balance, const std::string& password) {
    if (initial_balance < 0) return -1;
    std::string sql = "INSERT INTO Accounts (name, balance, password) VALUES ('" 
                      + name + "', " + std::to_string(initial_balance) + ", '" + password + "');";
    execute_query(sql);
    return sqlite3_last_insert_rowid(db); 
}

bool BankManager::authenticate(int account_id, const std::string& password) {
    std::string sql = "SELECT password FROM Accounts WHERE id = " + std::to_string(account_id) + ";";
    sqlite3_stmt* stmt;
    std::string stored_password = "";

    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            stored_password = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        }
    }
    sqlite3_finalize(stmt);
    
    return (stored_password == password);
}

double BankManager::get_balance(int account_id) {
    std::string sql = "SELECT balance FROM Accounts WHERE id = " + std::to_string(account_id) + ";";
    sqlite3_stmt* stmt;
    double balance = -1.0;

    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            balance = sqlite3_column_double(stmt, 0);
        }
    }
    sqlite3_finalize(stmt);

    if (balance < 0) throw std::invalid_argument("Tài khoản không tồn tại!");
    return balance;
}

bool BankManager::deposit(int account_id, double amount) {
    if (amount <= 0) return false;
    try {
        get_balance(account_id); 
        std::string sql = "UPDATE Accounts SET balance = balance + " + std::to_string(amount) + " WHERE id = " + std::to_string(account_id) + ";";
        execute_query(sql);
        return true;
    } catch (...) { return false; }
}

bool BankManager::withdraw(int account_id, double amount) {
    if (amount <= 0) return false;
    try {
        double current_balance = get_balance(account_id);
        if (current_balance < amount) return false; 
        std::string sql = "UPDATE Accounts SET balance = balance - " + std::to_string(amount) + " WHERE id = " + std::to_string(account_id) + ";";
        execute_query(sql);
        return true;
    } catch (...) { return false; }
}
bool BankManager::transfer(int from_id, int to_id, double amount) {
    if (amount <= 0 || from_id == to_id) return false;
    
    try {
        double from_balance = get_balance(from_id);
        get_balance(to_id);
        
        if (from_balance < amount) return false;
        std::string sql_tru = "UPDATE Accounts SET balance = balance - " + std::to_string(amount) + " WHERE id = " + std::to_string(from_id) + ";";
        std::string sql_cong = "UPDATE Accounts SET balance = balance + " + std::to_string(amount) + " WHERE id = " + std::to_string(to_id) + ";";
        
        execute_query(sql_tru);
        execute_query(sql_cong);
        return true;
    } catch (...) {
        return false;
    }
}
bool BankManager::request_loan(int account_id, double amount) {
    if (amount <= 0) return false;
    
    try {
        double current_balance = get_balance(account_id);
        if (current_balance > 5000000.0) {
            std::string sql = "UPDATE Accounts SET balance = balance + " + std::to_string(amount) + " WHERE id = " + std::to_string(account_id) + ";";
            execute_query(sql);
            return true;
        }
        return false;
    } catch (...) {
        return false;
    }
}
