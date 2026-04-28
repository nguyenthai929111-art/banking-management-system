#include "bank_logic.hpp"
#include <stdexcept>
#include <iomanip>
#include <sstream>

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
        "balance REAL NOT NULL, "
        "password TEXT NOT NULL,"
        "failed_attempts INTEGER DEFAULT 0, "     
        "is_locked INTEGER DEFAULT 0, "      
        "alert_threshold REAL DEFAULT 0.0);";
    execute_query(create_table_sql);
    std::string create_trans_sql = 
        "CREATE TABLE IF NOT EXISTS Transactions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "from_id INTEGER, "
        "to_id INTEGER, "
        "amount REAL, "
        "next_run_date DATE);";
    execute_query(create_trans_sql);
}
BankManager::~BankManager() {
    sqlite3_close(db);
}

int BankManager::create_account(const std::string& name, double initial_balance, const std::string& password) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    std::string hashed_pwd = hash_password(password);
    std::string sql = "INSERT INTO Accounts (name, balance, password) VALUES ('" 
                      + name + "', " + std::to_string(initial_balance) + ", '" + hashed_pwd + "');";
    execute_query(sql);
    int new_id = 0;
    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db, "SELECT seq FROM sqlite_sequence WHERE name='Accounts'", -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            new_id = sqlite3_column_int(stmt, 0);
        }
    }
    sqlite3_finalize(stmt);
    if (initial_balance > 0) {
        log_transaction(0, new_id, "DEPOSIT", initial_balance);
    }
    return new_id;
}

int BankManager::authenticate(int account_id, const std::string& password) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    std::string sql = "SELECT password, is_locked, failed_attempts FROM Accounts WHERE id = " + std::to_string(account_id) + ";";
    sqlite3_stmt* stmt;
    int status = -2;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            std::string db_password = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
            int is_locked = sqlite3_column_int(stmt, 1);
            int failed_attempts = sqlite3_column_int(stmt, 2);
            if (is_locked == 1) {
                status = -1;
            } else {
                std::string hashed_input = hash_password(password);
                if (db_password == hashed_input) {
                    execute_query("UPDATE Accounts SET failed_attempts = 0 WHERE id = " + std::to_string(account_id) + ";");
                    status = 1;
                } else {
                    failed_attempts++;
                    if (failed_attempts >= 5) {
                        execute_query("UPDATE Accounts SET failed_attempts = " + std::to_string(failed_attempts) + ", is_locked = 1 WHERE id = " + std::to_string(account_id) + ";");
                        status = -1;
                    } else {
                        execute_query("UPDATE Accounts SET failed_attempts = " + std::to_string(failed_attempts) + " WHERE id = " + std::to_string(account_id) + ";");
                        status = 0;
                    }
                }
            }
        }
    }
    sqlite3_finalize(stmt);
    return status;
}

double BankManager::get_balance(int account_id) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
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
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    if (amount <= 0) return false;
    try {
        get_balance(account_id); 
        std::string sql = "UPDATE Accounts SET balance = balance + " + std::to_string(amount) + " WHERE id = " + std::to_string(account_id) + ";";
        execute_query(sql);
        log_transaction(0, account_id, "DEPOSIT", amount);
        return true;
    } catch (...) { return false; }
}

bool BankManager::withdraw(int account_id, double amount) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    if (amount <= 0) return false;
    try {
        double current_balance = get_balance(account_id);
        if (current_balance < amount) return false; 
        std::string sql = "UPDATE Accounts SET balance = balance - " + std::to_string(amount) + " WHERE id = " + std::to_string(account_id) + ";";
        execute_query(sql);
        log_transaction(account_id, 0, "WITHDRAW", amount);
        return true;
    } catch (...) { return false; }
}
bool BankManager::transfer(int from_id, int to_id, double amount) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    if (amount <= 0 || from_id == to_id) return false;
    
    try {
        double from_balance = get_balance(from_id);
        get_balance(to_id);
        
        if (from_balance < amount) return false;
        std::string sql_tru = "UPDATE Accounts SET balance = balance - " + std::to_string(amount) + " WHERE id = " + std::to_string(from_id) + ";";
        std::string sql_cong = "UPDATE Accounts SET balance = balance + " + std::to_string(amount) + " WHERE id = " + std::to_string(to_id) + ";";
        
        execute_query(sql_tru);
        execute_query(sql_cong);
        log_transaction(from_id, to_id, "TRANSFER", amount);
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
            log_transaction(0, account_id, "LOAN", amount);
            return true;
        }
        return false;
    } catch (...) {
        return false;
    }
}
void BankManager::log_transaction(int from_id, int to_id, const std::string& type, double amount) {
    std::string sql = "INSERT INTO Transactions (from_id, to_id, type, amount) VALUES (" +
                      std::to_string(from_id) + ", " + std::to_string(to_id) + ", '" + 
                      type + "', " + std::to_string(amount) + ");";
    execute_query(sql);
}

std::vector<std::vector<std::string>> BankManager::get_history(int account_id) {
    std::vector<std::vector<std::string>> history;
    std::string sql = "SELECT type, from_id, to_id, amount, timestamp FROM Transactions "
                      "WHERE from_id = " + std::to_string(account_id) + 
                      " OR to_id = " + std::to_string(account_id) + " ORDER BY timestamp DESC;";
    
    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            std::vector<std::string> row;
            row.push_back(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)));
            row.push_back(std::to_string(sqlite3_column_int(stmt, 1)));                
            row.push_back(std::to_string(sqlite3_column_int(stmt, 2)));                
            row.push_back(std::to_string(sqlite3_column_double(stmt, 3)));
            row.push_back(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 4)));
            history.push_back(row);
        }
    }
    sqlite3_finalize(stmt);
    return history;
}
std::string BankManager::hash_password(const std::string& password) {
    unsigned long hash = 5381;
    for (char c : password) {
        hash = ((hash << 5) + hash) + c; 
    }
    std::stringstream ss;
    ss << std::hex << std::setw(8) << std::setfill('0') << hash;
    return ss.str();
}

std::vector<int> BankManager::get_optimal_savings_plan(int total_months) {
    std::vector<std::pair<int, double>> packages = {
        {1, 0.004},
        {3, 0.015},
        {6, 0.035},
        {12, 0.08}
    };
    
    std::vector<double> dp(total_months + 1, 0.0);
    std::vector<int> trace(total_months + 1, -1);
    
    dp[0] = 1.0;
    for (int i = 1; i <= total_months; ++i) {
        for (int j = 0; j < packages.size(); ++j) {
            int m = packages[j].first;
            double r = packages[j].second;
            
            if (i >= m && dp[i - m] > 0) {
                double new_val = dp[i - m] * (1.0 + r);
                if (new_val > dp[i]) {
                    dp[i] = new_val;
                    trace[i] = j; 
                }
            }
        }
    }
    std::vector<int> plan;
    int curr = total_months;
    while (curr > 0 && trace[curr] != -1) {
        int pkg_idx = trace[curr];
        plan.push_back(packages[pkg_idx].first);
        curr -= packages[pkg_idx].first;
    }
    
    return plan;
}

bool BankManager::change_password(int account_id, const std::string& old_password, const std::string& new_password) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    if (authenticate(account_id, old_password) == 1) { // Kiểm tra pass cũ
        std::string new_hashed = hash_password(new_password);
        execute_query("UPDATE Accounts SET password = '" + new_hashed + "' WHERE id = " + std::to_string(account_id) + ";");
        return true;
    }
    return false;
}

void BankManager::set_alert_threshold(int account_id, double threshold) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    execute_query("UPDATE Accounts SET alert_threshold = " + std::to_string(threshold) + " WHERE id = " + std::to_string(account_id) + ";");
}

double BankManager::get_alert_threshold(int account_id) {
    std::lock_guard<std::recursive_mutex> lock(db_mutex);
    double threshold = 0.0;
    std::string sql = "SELECT alert_threshold FROM Accounts WHERE id = " + std::to_string(account_id) + ";";
    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            threshold = sqlite3_column_double(stmt, 0);
        }
    }
    sqlite3_finalize(stmt);
    return threshold;
}
