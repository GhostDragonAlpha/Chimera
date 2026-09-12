#include "http_server.hpp"
#include <windows.h>
#include <iostream>
#include <string>

int main() {
    constexpr int kPort = 49173;
    HttpServer server;
    auto handler = [](const std::string& method, const std::string& path,
                      const std::string& req_body, std::string& resp_body,
                      std::string& content_type) {
        content_type = "application/json";
        resp_body = std::string("{\"method\":\"") + method
                  + "\",\"path\":\"" + path
                  + "\",\"body\":\"" + req_body + "\"}";
    };
    if (!server.start(kPort, handler)) {
        std::cerr << "START_FAILED port=" << kPort << "\n";
        return 2;
    }
    std::cout << "READY pid=" << GetCurrentProcessId()
              << " port=" << server.port() << "\n" << std::flush;
    for (;;) Sleep(1000);
}
