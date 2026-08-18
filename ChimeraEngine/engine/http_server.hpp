#pragma once
#include <winsock2.h>
#include <ws2tcpip.h>
#include <thread>
#include <atomic>
#include <functional>
#include <string>

// Minimal embedded HTTP server using Winsock2.
// No external deps — httplib is header-only but we keep this self-contained
// for the first pass; swap to httplib later if needed.

class HttpServer {
public:
    bool start(int port, std::function<void(const std::string& method, const std::string& path,
                                             const std::string& req_body, std::string& resp_body,
                                             std::string& content_type)> handler);
    void stop();
    int  port() const { return port_; }

private:
    bool listen_ = false;
    SOCKET sock_ = INVALID_SOCKET;
    std::thread thread_;
    int port_ = 8080;
    std::function<void(const std::string&, const std::string&, const std::string&, std::string&, std::string&)> handler_;
};
