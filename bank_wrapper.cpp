#include <pybind11/pybind11.h>
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
        .def("request_loan", &BankManager::request_loan);
}