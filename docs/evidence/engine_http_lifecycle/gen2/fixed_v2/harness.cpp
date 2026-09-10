#include "http_server.hpp"
#include <winsock2.h>
#include <windows.h>
#include <atomic>
#include <chrono>
#include <cstring>
#include <functional>
#include <iostream>
#include <string>
#include <thread>

static constexpr int kPort = 49175;
using Handler = std::function<void(const std::string&, const std::string&, const std::string&, std::string&, std::string&)>;

static bool connect_local(SOCKET& out) {
    out = socket(AF_INET, SOCK_STREAM, 0);
    if (out == INVALID_SOCKET) return false;
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(static_cast<u_short>(kPort));
    if (connect(out, reinterpret_cast<sockaddr*>(&address), sizeof(address)) == SOCKET_ERROR) {
        closesocket(out);
        out = INVALID_SOCKET;
        return false;
    }
    return true;
}

static bool wait_flag(const std::atomic<bool>& flag, int ms = 1000) {
    for (int elapsed = 0; elapsed < ms; elapsed += 5) {
        if (flag.load(std::memory_order_acquire)) return true;
        Sleep(5);
    }
    return flag.load(std::memory_order_acquire);
}

static std::string request(const char* method, const char* path, const std::string& body) {
    SOCKET client = INVALID_SOCKET;
    if (!connect_local(client)) return "CONNECT_FAILED";
    std::string req = std::string(method) + " " + path + " HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n";
    if (!body.empty()) req += "Content-Length: " + std::to_string(body.size()) + "\r\n";
    req += "\r\n" + body;
    send(client, req.data(), static_cast<int>(req.size()), 0);
    std::string response;
    char buffer[4096];
    for (;;) {
        int received = recv(client, buffer, sizeof(buffer), 0);
        if (received <= 0) break;
        response.append(buffer, received);
    }
    closesocket(client);
    return response;
}

static Handler make_handler() {
    return [](const std::string& method, const std::string& path,
              const std::string& body, std::string& output, std::string& type) {
        type = "text/plain";
        output = method + " " + path + " body=" + body;
    };
}

static int quiet_stop() {
    HttpServer server;
    if (!server.start(kPort, make_handler())) { std::cout << "START_FAILED\n"; return 2; }
    SOCKET warm = INVALID_SOCKET;
    if (!connect_local(warm)) { std::cout << "WARM_CONNECT_FAILED\n"; return 3; }
    closesocket(warm);
    Sleep(100); // scheduling witness: accept has had time to enter its receive path
    std::cout << "BEFORE_STOP quiet pid=" << GetCurrentProcessId() << std::endl;
    auto started = std::chrono::steady_clock::now();
    server.stop();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    std::cout << "STOP_RETURN quiet ms=" << elapsed << std::endl;
    return 0;
}

static int partial_header_stop() {
    HttpServer server;
    if (!server.start(kPort, make_handler())) return 2;
    SOCKET client = INVALID_SOCKET;
    if (!connect_local(client)) return 3;
    const char* partial = "GET /partial-header HTTP/1.1\r\nHost: localhost\r\n";
    send(client, partial, static_cast<int>(strlen(partial)), 0);
    Sleep(150);
    std::cout << "BEFORE_STOP partial_header pid=" << GetCurrentProcessId() << std::endl;
    auto started = std::chrono::steady_clock::now();
    server.stop();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    closesocket(client);
    std::cout << "STOP_RETURN partial_header ms=" << elapsed << std::endl;
    return 0;
}

static int partial_body_stop() {
    HttpServer server;
    if (!server.start(kPort, make_handler())) return 2;
    SOCKET client = INVALID_SOCKET;
    if (!connect_local(client)) return 3;
    const char* partial = "POST /partial-body HTTP/1.1\r\nHost: localhost\r\nContent-Length: 32768\r\n\r\nabc";
    send(client, partial, static_cast<int>(strlen(partial)), 0);
    Sleep(150);
    std::cout << "BEFORE_STOP partial_body pid=" << GetCurrentProcessId() << std::endl;
    auto started = std::chrono::steady_clock::now();
    server.stop();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    closesocket(client);
    std::cout << "STOP_RETURN partial_body ms=" << elapsed << std::endl;
    return 0;
}

static int local_requests() {
    HttpServer server;
    if (!server.start(kPort, make_handler())) return 2;
    std::string get = request("GET", "/health", "");
    std::string post = request("POST", "/control", "probe=1");
    bool get_ok = get.find("HTTP/1.1 200 OK") != std::string::npos && get.find("GET /health body=") != std::string::npos;
    bool post_ok = post.find("HTTP/1.1 200 OK") != std::string::npos && post.find("POST /control body=probe=1") != std::string::npos;
    std::cout << "LOCAL_GET " << (get_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "LOCAL_POST " << (post_ok ? "PASS" : "FAIL") << "\n";
    server.stop();
    return (get_ok && post_ok) ? 0 : 4;
}

static int blocked_send_stop() {
    std::atomic<bool> entered{false};
    HttpServer server;
    Handler huge = [&entered](const std::string&, const std::string&, const std::string&, std::string& output, std::string& type) {
        entered.store(true, std::memory_order_release);
        type = "application/octet-stream";
        output.assign(64u * 1024u * 1024u, 'x');
    };
    if (!server.start(kPort, huge)) return 2;
    SOCKET client = INVALID_SOCKET;
    if (!connect_local(client)) return 3;
    int receive_buffer = 1024;
    setsockopt(client, SOL_SOCKET, SO_RCVBUF, reinterpret_cast<const char*>(&receive_buffer), sizeof(receive_buffer));
    const char* req = "GET /send-block HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
    send(client, req, static_cast<int>(strlen(req)), 0);
    if (!wait_flag(entered)) { closesocket(client); server.stop(); return 4; }
    Sleep(100); // let the nonblocking send reach a full peer window
    auto started = std::chrono::steady_clock::now();
    server.stop();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    closesocket(client);
    std::cout << "BLOCKED_SEND entered=" << (entered.load() ? "yes" : "no") << " stop_ms=" << elapsed << "\n";
    return entered.load() ? 0 : 5;
}

static int finite_callback_stop() {
    std::atomic<bool> entered{false};
    std::atomic<bool> release{false};
    HttpServer server;
    Handler finite = [&entered, &release](const std::string&, const std::string&, const std::string&, std::string& output, std::string& type) {
        entered.store(true, std::memory_order_release);
        while (!release.load(std::memory_order_acquire)) Sleep(5);
        type = "text/plain";
        output = "released";
    };
    if (!server.start(kPort, finite)) return 2;
    SOCKET client = INVALID_SOCKET;
    if (!connect_local(client)) return 3;
    const char* req = "GET /finite HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
    send(client, req, static_cast<int>(strlen(req)), 0);
    if (!wait_flag(entered)) { closesocket(client); server.stop(); return 4; }
    std::thread stopper([&server]() { server.stop(); });
    Sleep(100);
    bool drained_before_release = stopper.joinable();
    release.store(true, std::memory_order_release);
    stopper.join();
    closesocket(client);
    std::cout << "FINITE_CALLBACK entered=yes released=yes joined=yes before_release_joinable=" << (drained_before_release ? "yes" : "no") << "\n";
    return drained_before_release ? 0 : 5;
}

static int repeated_cycles() {
    for (int i = 0; i < 5; ++i) {
        HttpServer server;
        if (!server.start(kPort, make_handler())) { std::cout << "CYCLE_START_FAIL " << i << "\n"; return 2; }
        server.stop();
        std::cout << "CYCLE " << i << " PASS\n";
    }
    return 0;
}

static int start_failure() {
    HttpServer first;
    if (!first.start(kPort, make_handler())) return 2;
    HttpServer second;
    bool second_ok = second.start(kPort, make_handler());
    std::cout << "OCCUPIED_SECOND_START " << (second_ok ? "UNEXPECTED_SUCCESS" : "EXPECTED_FAILURE") << "\n";
    if (second_ok) second.stop();
    first.stop();
    HttpServer third;
    bool third_ok = third.start(kPort, make_handler());
    std::cout << "RESTART_AFTER_FAILURE " << (third_ok ? "PASS" : "FAIL") << "\n";
    if (third_ok) third.stop();
    return (!second_ok && third_ok) ? 0 : 5;
}

static int destructor_stop() {
    {
        HttpServer server;
        if (!server.start(kPort, make_handler())) return 2;
        SOCKET warm = INVALID_SOCKET;
        if (!connect_local(warm)) return 3;
        closesocket(warm);
        Sleep(100);
        std::cout << "BEFORE_DESTRUCTOR pid=" << GetCurrentProcessId() << std::endl;
    }
    std::cout << "DESTRUCTOR_RETURN PASS\n";
    return 0;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: harness quiet|partial_header|partial_body|local|blocked_send|finite_callback|cycles|start_failure|destructor\n";
        return 64;
    }
    WSADATA wsa{};
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 65;
    std::string mode = argv[1];
    int result = 64;
    if (mode == "quiet") result = quiet_stop();
    else if (mode == "partial_header") result = partial_header_stop();
    else if (mode == "partial_body") result = partial_body_stop();
    else if (mode == "local") result = local_requests();
    else if (mode == "blocked_send") result = blocked_send_stop();
    else if (mode == "finite_callback") result = finite_callback_stop();
    else if (mode == "cycles") result = repeated_cycles();
    else if (mode == "start_failure") result = start_failure();
    else if (mode == "destructor") result = destructor_stop();
    WSACleanup();
    return result;
}
