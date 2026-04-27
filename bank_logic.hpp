#ifndef BANK_LOGIC_HPP
#define BANK_LOGIC_HPP

#include <string>
#include "sqlite3.h" // Dùng ngoặc kép để đọc file sqlite3.h cùng thư mục

class BankManager {
private:
    sqlite3* db;
    void execute_query(const std::string& sql);

public:
    BankManager();
    ~BankManager();
    int create_account(const std::string& name, double initial_balance, const std::string& password);
    bool authenticate(int account_id, const std::string& password);
    double get_balance(int account_id);
    bool deposit(int account_id, double amount);
    bool withdraw(int account_id, double amount);
    bool transfer(int from_id, int to_id, double amount);
    bool request_loan(int account_id, double amount);
};

#endif