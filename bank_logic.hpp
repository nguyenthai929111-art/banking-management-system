#ifndef BANK_LOGIC_HPP
#define BANK_LOGIC_HPP

#include <vector>
#include <string>
#include "sqlite3.h"

class BankManager {
private:
    sqlite3* db;
    void execute_query(const std::string& sql);
    void log_transaction(int from_id, int to_id, const std::string& type, double amount);
    std::string hash_password(const std::string& password);
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
    std::vector<std::vector<std::string>> get_history(int account_id);
};

#endif
