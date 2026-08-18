#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include "http_server.hpp"
#include <string>
#include <sstream>
#include <cctype>
#include <algorithm>

#pragma comment(lib, "ws2_32.lib")

static bool send_all(SOCKET s, const char* data, int len) {
    int sent = 0;
    while (sent < len) {
        int r = send(s, data + sent, len - sent, 0);
        if (r <= 0) return false;
        sent += r;
    }
    return true;
}

static long long content_length(const std::string& headers) {
    std::string lower = headers;
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    std::string needle = "content-length:";
    size_t pos = lower.find(needle);
    if (pos == std::string::npos) return -1;
    size_t p = pos + needle.size();
    while (p < lower.size() && (lower[p] == ' ' || lower[p] == '\t')) ++p;
    size_t end = p;
    while (end < lower.size() && std::isdigit(static_cast<unsigned char>(lower[end]))) ++end;
    if (end == p) return -1;
    try { return std::stoll(lower.substr(p, end - p)); } catch (...) { return -1; }
}

bool HttpServer::start(int port, std::function<void(const std::string&, const std::string&, const std::string&, std::string&, std::string&)> handler) {
    port_ = port;
    handler_ = handler;

    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) return false;

    sock_ = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_ == INVALID_SOCKET) return false;

    sockaddr_in addr{};
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port        = htons(static_cast<u_short>(port));

    int opt = 1;
    setsockopt(sock_, SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char*>(&opt), sizeof(opt));

    if (bind(sock_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) == SOCKET_ERROR) {
        closesocket(sock_); sock_ = INVALID_SOCKET; return false;
    }
    if (listen(sock_, 8) == SOCKET_ERROR) {
        closesocket(sock_); sock_ = INVALID_SOCKET; return false;
    }

    listen_ = true;
    thread_ = std::thread([this]() {
        char buf[16384];
        while (listen_) {
            sockaddr_in client_addr{};
            int addr_len = sizeof(client_addr);
            SOCKET client = accept(sock_, reinterpret_cast<sockaddr*>(&client_addr), &addr_len);
            if (client == INVALID_SOCKET) break;

            // Read until the end of headers (blank line), up to a sane cap.
            std::string req;
            while (req.size() < (1u << 20) && req.find("\r\n\r\n") == std::string::npos) {
                int n = recv(client, buf, sizeof(buf) - 1, 0);
                if (n <= 0) break;
                req.append(buf, n);
            }

            size_t header_end = req.find("\r\n\r\n");
            if (header_end == std::string::npos) { closesocket(client); continue; }
            std::string headers = req.substr(0, header_end);
            std::string body = req.substr(header_end + 4);

            std::istringstream iss(headers);
            std::string method, path, proto;
            iss >> method >> path >> proto;

            // Read the rest of the body per Content-Length (large /membrane arrays exceed 64KB).
            long long cl = content_length(headers);
            if (cl > 0) {
                while (static_cast<long long>(body.size()) < cl) {
                    int n = recv(client, buf, sizeof(buf) - 1, 0);
                    if (n <= 0) break;
                    body.append(buf, n);
                    if (static_cast<long long>(body.size()) > cl + (1 << 20)) break;
                }
                if (static_cast<long long>(body.size()) > cl) body.resize(static_cast<size_t>(cl));
            }

            std::string out_body;
            std::string content_type = "text/plain";
            handler_(method, path, body, out_body, content_type);

            std::string resp = "HTTP/1.1 200 OK\r\n";
            resp += "Content-Type: " + content_type + "\r\n";
            resp += "Access-Control-Allow-Origin: *\r\n";
            resp += "Content-Length: " + std::to_string(out_body.size()) + "\r\n";
            resp += "Connection: close\r\n\r\n";
            resp += out_body;

            send_all(client, resp.c_str(), static_cast<int>(resp.size()));
            closesocket(client);
        }
    });
    return true;
}

void HttpServer::stop() {
    listen_ = false;
    if (thread_.joinable()) thread_.join();
    if (sock_ != INVALID_SOCKET) { closesocket(sock_); sock_ = INVALID_SOCKET; }
    WSACleanup();
}
