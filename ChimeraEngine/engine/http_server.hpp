#pragma once
#include <winsock2.h>
#include <ws2tcpip.h>
#include <thread>
#include <atomic>
#include <functional>
#include <mutex>
#include <string>

// Minimal embedded HTTP server using Winsock2.
// The worker owns and closes the listener and accepted sockets. stop() only
// publishes cancellation and joins that worker, so it never closes a socket
// concurrently with a Winsock call made by the worker.
class HttpServer {
public:
    ~HttpServer();

    bool start(int port, std::function<void(const std::string& method, const std::string& path,
                                             const std::string& req_body, std::string& resp_body,
                                             std::string& content_type)> handler);
    void stop();
    int port() const { return port_; }

private:
    std::mutex lifecycle_;
    std::atomic<bool> listen_{false};
    SOCKET sock_ = INVALID_SOCKET;
    std::thread thread_;
    int port_ = 8080;
    std::function<void(const std::string&, const std::string&, const std::string&, std::string&, std::string&)> handler_;
    bool wsa_started_ = false;
};
