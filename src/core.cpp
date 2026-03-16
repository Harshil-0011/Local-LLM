#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <set>

namespace py = pybind11;

std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> tokens;
    std::string token;
    std::stringstream ss(text);
    while (ss >> token) {
        std::transform(token.begin(), token.end(), token.begin(), ::tolower);
        // Remove punctuation (simple version)
        token.erase(std::remove_if(token.begin(), token.end(), [](char c) { return ispunct(c); }), token.end());
        if (!token.empty()) {
            tokens.push_back(token);
        }
    }
    return tokens;
}

double calculate_relevance(const std::string& query, const std::string& content) {
    auto query_tokens = tokenize(query);
    auto content_tokens = tokenize(content);

    std::set<std::string> query_set(query_tokens.begin(), query_tokens.end());
    if (query_set.empty()) return 0.0;

    int matches = 0;
    for (const auto& token : content_tokens) {
        if (query_set.count(token)) {
            matches++;
        }
    }

    return static_cast<double>(matches) / (content_tokens.size() + 1);
}

PYBIND11_MODULE(local_perplex_core, m) {
    m.doc() = "Local Perplex C++ Core for high-performance text processing";
    m.def("calculate_relevance", &calculate_relevance, "Calculate relevance score between query and content");
    m.def("tokenize", &tokenize, "Tokenize text into lowercase words");
}
