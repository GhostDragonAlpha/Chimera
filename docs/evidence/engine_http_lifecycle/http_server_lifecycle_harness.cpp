#include <atomic>
#include <chrono>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
#include <iostream>
#include <cstdlib>

#include "ChimeraEngine/engine/http_server.hpp"

#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

namespace {

SOCKET connect_loopback(int port) {
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == INVALID_SOCKET) return INVALID_SOCKET;
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(static_cast<u_short>(port));
    if (connect(s, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) == SOCKET_ERROR) {
        closesocket(s);
        return INVALID_SOCKET;
    }
    return s;
}

bool send_request(int port, const std::string& method, const std::string& path, const std::string& body = "") {
    SOCKET s = connect_loopback(port);
    if (s == INVALID_SOCKET) return false;
    int timeout = 500;
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, reinterpret_cast<const char*>(&timeout), sizeof(timeout));
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&timeout), sizeof(timeout));

    std::string req = method + " " + path + " HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n";
    if (!body.empty()) req += "Content-Length: " + std::to_string(body.size()) + "\r\n";
    req += "\r\n";
    req += body;
    if (send(s, req.c_str(), static_cast<int>(req.size()), 0) == SOCKET_ERROR) {
        closesocket(s);
        return false;
    }
    char buf[2048];
    std::string resp;
    while (true) {
        int n = recv(s, buf, sizeof(buf), 0);
        if (n <= 0) break;
        resp.append(buf, n);
    }
    closesocket(s);
    return resp.rfind("HTTP/1.1 200", 0) == 0;
}

bool stop_with_watchdog(HttpServer& server, int timeout_ms, const std::string&) {
    std::atomic<bool> done{false};
    std::thread t([&] { server.stop(); done.store(true); });
    const int step_ms = 25;
    int waited = 0;
    while (waited < timeout_ms) {
        if (done.load()) break;
        std::this_thread::sleep_for(std::chrono::milliseconds(step_ms));
        waited += step_ms;
    }
    if (!done.load()) {
        std::cerr << "[FAIL] timeout waiting for stop_" << std::endl;
        std::_Exit(124);
    }
    t.join();
    return true;
}

bool test_quiet_stop() {
    HttpServer server;
    if (!server.start(9011, [](auto, auto, auto, std::string& out, std::string& ct){
        ct = "text/plain";
        out = "ok";
    })) return false;
    return stop_with_watchdog(server, 1500, "quiet_stop");
}

bool test_partial_request_stop() {
    HttpServer server;
    if (!server.start(9012, [](auto, auto, auto, std::string& out, std::string& ct){
        ct = "text/plain";
        out = "ok";
    })) return false;

    SOCKET c = connect_loopback(9012);
    if (c == INVALID_SOCKET) {
        server.stop();
        return false;
    }
    const char* partial = "POST /x HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 1024\r\n";
    if (send(c, partial, static_cast<int>(std::strlen(partial)), 0) == SOCKET_ERROR) {
        closesocket(c);
        server.stop();
        return false;
    }

    bool ok = stop_with_watchdog(server, 1500, "partial_stop");
    closesocket(c);
    return ok;
}

bool test_repeated_cycles() {
    for (int i = 0; i < 3; ++i) {
        HttpServer server;
        if (!server.start(9013 + i, [](auto, auto, auto, std::string& out, std::string& ct){
            ct = "text/plain";
            out = "ok";
        })) return false;
        if (!send_request(9013 + i, "GET", "/")) return false;
        if (!stop_with_watchdog(server, 1500, "cycle_stop")) return false;
    }
    return true;
}

bool test_start_failure_occupied_port() {
    // Hold an ephemeral loopback port with a raw listener and ensure start() returns false.
    SOCKET blocker = socket(AF_INET, SOCK_STREAM, 0);
    if (blocker == INVALID_SOCKET) return false;
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;
    int one = 1;
    setsockopt(blocker, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, reinterpret_cast<const char*>(&one), sizeof(one));
    if (bind(blocker, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) == SOCKET_ERROR) {
        closesocket(blocker);
        return false;
    }
    int addr_len = sizeof(addr);
    if (getsockname(blocker, reinterpret_cast<sockaddr*>(&addr), &addr_len) == SOCKET_ERROR) {
        closesocket(blocker);
        return false;
    }
    int port = ntohs(addr.sin_port);
    if (listen(blocker, 8) == SOCKET_ERROR) {
        closesocket(blocker);
        return false;
    }
    HttpServer server;
    bool ok = !server.start(port, [](auto, auto, auto, std::string& out, std::string& ct){
        ct = "text/plain";
        out = "ok";
    });
    closesocket(blocker);
    return ok;
}

} // namespace

int main() {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) return 3;

    std::vector<std::pair<std::string, bool(*)()>> cases{
        {"quiet_stop", test_quiet_stop},
        {"partial_request_stop", test_partial_request_stop},
        {"repeated_cycles", test_repeated_cycles},
        {"start_failure_occupied_port", test_start_failure_occupied_port},
    };
    int failed = 0;
    for (auto& c : cases) {
        bool pass = c.second();
        std::cout << c.first << "=" << (pass ? "PASS" : "FAIL") << std::endl;
        if (!pass) ++failed;
    }
    WSACleanup();
    return failed == 0 ? 0 : 1;
}
