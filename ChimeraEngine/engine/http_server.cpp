#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include "http_server.hpp"
#include <algorithm>
#include <cctype>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

namespace {

// The worker uses nonblocking sockets and select() polling so cancellation is
// observed without another thread closing a socket during recv/send/accept.
static bool set_nonblocking(SOCKET s) {
    u_long one = 1;
    return ioctlsocket(s, FIONBIO, &one) == 0;
}

static bool wait_for_io(SOCKET s, bool want_read, bool want_write,
                        const std::atomic<bool>& live) {
    while (live.load(std::memory_order_acquire)) {
        fd_set read_set;
        fd_set write_set;
        FD_ZERO(&read_set);
        FD_ZERO(&write_set);
        if (want_read) FD_SET(s, &read_set);
        if (want_write) FD_SET(s, &write_set);

        timeval timeout{};
        timeout.tv_usec = 50000; // bounded cancellation polling, not a socket timeout
        int ready = select(0, want_read ? &read_set : nullptr,
                           want_write ? &write_set : nullptr, nullptr, &timeout);
        if (ready > 0) return true;
        if (ready == 0) continue;
        if (!live.load(std::memory_order_acquire)) return false;
        const int error = WSAGetLastError();
        if (error == WSAEINTR) continue;
        return false;
    }
    return false;
}

static bool send_all(SOCKET s, const char* data, int len,
                     const std::atomic<bool>& live) {
    int sent = 0;
    while (sent < len && live.load(std::memory_order_acquire)) {
        if (!wait_for_io(s, false, true, live)) return false;
        int written = send(s, data + sent, len - sent, 0);
        if (written == SOCKET_ERROR) {
            const int error = WSAGetLastError();
            if (error == WSAEWOULDBLOCK || error == WSAEINTR) continue;
            return false;
        }
        if (written == 0) return false;
        sent += written;
    }
    return sent == len;
}

static long long content_length(const std::string& headers) {
    std::string lower = headers;
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    const std::string needle = "content-length:";
    const size_t pos = lower.find(needle);
    if (pos == std::string::npos) return -1;
    size_t p = pos + needle.size();
    while (p < lower.size() && (lower[p] == ' ' || lower[p] == '\t')) ++p;
    size_t end = p;
    while (end < lower.size() && std::isdigit(static_cast<unsigned char>(lower[end]))) ++end;
    if (end == p) return -1;
    try { return std::stoll(lower.substr(p, end - p)); } catch (...) { return -1; }
}

} // namespace

HttpServer::~HttpServer() {
    stop();
}

bool HttpServer::start(int port, std::function<void(const std::string&, const std::string&, const std::string&, std::string&, std::string&)> handler) {
    std::scoped_lock lock(lifecycle_);
    if (listen_.load(std::memory_order_acquire) || thread_.joinable()) return false;

    port_ = port;
    handler_ = std::move(handler);

    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return false;
    wsa_started_ = true;

    SOCKET listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener == INVALID_SOCKET) {
        WSACleanup();
        wsa_started_ = false;
        return false;
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(static_cast<u_short>(port));

    // Prevent a second process/server instance from binding the same endpoint
    // while this listener is alive.  SO_REUSEADDR would permit ambiguous
    // ownership on Windows and make the occupied-port failure meaningless.
    int exclusive = 1;
    setsockopt(listener, SOL_SOCKET, SO_EXCLUSIVEADDRUSE,
               reinterpret_cast<const char*>(&exclusive), sizeof(exclusive));
    if (bind(listener, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) == SOCKET_ERROR ||
        listen(listener, 8) == SOCKET_ERROR || !set_nonblocking(listener)) {
        closesocket(listener);
        WSACleanup();
        wsa_started_ = false;
        return false;
    }

    sock_ = listener;
    listen_.store(true, std::memory_order_release);
    try {
        thread_ = std::thread([this, listener]() {
            char buffer[16384];
            while (listen_.load(std::memory_order_acquire)) {
                if (!wait_for_io(listener, true, false, listen_)) break;

                sockaddr_in client_addr{};
                int addr_len = sizeof(client_addr);
                SOCKET client = accept(listener, reinterpret_cast<sockaddr*>(&client_addr), &addr_len);
                if (client == INVALID_SOCKET) {
                    if (!listen_.load(std::memory_order_acquire)) break;
                    const int error = WSAGetLastError();
                    if (error == WSAEWOULDBLOCK || error == WSAEINTR) continue;
                    continue;
                }
                if (!listen_.load(std::memory_order_acquire) || !set_nonblocking(client)) {
                    closesocket(client);
                    if (!listen_.load(std::memory_order_acquire)) break;
                    continue;
                }

                std::string request;
                bool complete = true;
                while (request.size() < (1u << 20) &&
                       request.find("\r\n\r\n") == std::string::npos) {
                    if (!wait_for_io(client, true, false, listen_)) { complete = false; break; }
                    int received = recv(client, buffer, sizeof(buffer), 0);
                    if (received > 0) request.append(buffer, received);
                    else if (received == SOCKET_ERROR) {
                        const int error = WSAGetLastError();
                        if (error == WSAEWOULDBLOCK || error == WSAEINTR) continue;
                        complete = false;
                        break;
                    }
                    else { complete = false; break; }
                }
                const size_t header_end = request.find("\r\n\r\n");
                if (!complete || header_end == std::string::npos) {
                    closesocket(client);
                    if (!listen_.load(std::memory_order_acquire)) break;
                    continue;
                }

                const std::string headers = request.substr(0, header_end);
                std::string body = request.substr(header_end + 4);
                std::istringstream request_line(headers);
                std::string method, path, protocol;
                request_line >> method >> path >> protocol;

                const long long expected = content_length(headers);
                if (expected > 0) {
                    while (static_cast<long long>(body.size()) < expected) {
                        if (!wait_for_io(client, true, false, listen_)) { complete = false; break; }
                        int received = recv(client, buffer, sizeof(buffer), 0);
                        if (received > 0) body.append(buffer, received);
                        else if (received == SOCKET_ERROR) {
                            const int error = WSAGetLastError();
                            if (error == WSAEWOULDBLOCK || error == WSAEINTR) continue;
                            complete = false;
                            break;
                        }
                        else { complete = false; break; }
                    }
                    if (static_cast<long long>(body.size()) > expected)
                        body.resize(static_cast<size_t>(expected));
                }
                if (!complete || !listen_.load(std::memory_order_acquire)) {
                    closesocket(client);
                    if (!listen_.load(std::memory_order_acquire)) break;
                    continue;
                }

                std::string output;
                std::string content_type = "text/plain";
                handler_(method, path, body, output, content_type);
                if (!listen_.load(std::memory_order_acquire)) {
                    closesocket(client);
                    break;
                }

                std::string response = "HTTP/1.1 200 OK\r\n";
                response += "Content-Type: " + content_type + "\r\n";
                response += "Access-Control-Allow-Origin: *\r\n";
                response += "Content-Length: " + std::to_string(output.size()) + "\r\n";
                response += "Connection: close\r\n\r\n";
                response += output;
                send_all(client, response.c_str(), static_cast<int>(response.size()), listen_);
                closesocket(client);
            }
            closesocket(listener);
        });
    } catch (...) {
        listen_.store(false, std::memory_order_release);
        closesocket(listener);
        sock_ = INVALID_SOCKET;
        WSACleanup();
        wsa_started_ = false;
        return false;
    }
    return true;
}

void HttpServer::stop() {
    std::scoped_lock lock(lifecycle_);
    listen_.store(false, std::memory_order_release);
    if (thread_.joinable()) thread_.join();
    sock_ = INVALID_SOCKET; // worker closed its local listener handle
    if (wsa_started_) {
        WSACleanup();
        wsa_started_ = false;
    }
}
