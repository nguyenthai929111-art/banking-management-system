#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "bank_logic.hpp"

namespace py = pybind11;

PYBIND11_MODULE(bank_core, m) {
    py::class_<BankManager>(m, "BankManager")
        .def(py::init<>())
        .def("create_account", &BankManager::create_account)
        .def("authenticate", &BankManager::authenticate)
        .def("get_balance", &BankManager::get_balance)
        .def("deposit", &BankManager::deposit)
        .def("withdraw", &BankManager::withdraw)
        .def("transfer", &BankManager::transfer)
        .def("request_loan", &BankManager::request_loan)
        .def("get_history", &BankManager::get_history)
        .def("get_optimal_savings_plan", &BankManager::get_optimal_savings_plan)
        .def("change_password", &BankManager::change_password)
        .def("set_alert_threshold", &BankManager::set_alert_threshold)
        .def("get_alert_threshold", &BankManager::get_alert_threshold)
        .def("add_scheduled_transfer", &BankManager::add_scheduled_transfer)
        .def("process_scheduled_transfers", &BankManager::process_scheduled_transfers);
}
