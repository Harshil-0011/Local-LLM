#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <set>
#include <map>
#include <cmath>

namespace py = pybind11;

class TextProcessor {
public:
    static std::vector<std::string> tokenize(const std::string& text) {
        std::vector<std::string> tokens;
        std::string token;
        std::stringstream ss(text);
        while (ss >> token) {
            std::transform(token.begin(), token.end(), token.begin(), ::tolower);
            token.erase(std::remove_if(token.begin(), token.end(), [](char c) {
                return ispunct(c) || isdigit(c);
            }), token.end());
            if (token.length() > 2) {
                tokens.push_back(token);
            }
        }
        return tokens;
    }

    static double calculate_score(const std::string& query, const std::string& content) {
        auto q_tokens = tokenize(query);
        auto c_tokens = tokenize(content);
        if (q_tokens.empty() || c_tokens.empty()) return 0.0;

        std::set<std::string> q_set(q_tokens.begin(), q_tokens.end());
        std::map<std::string, int> freq;
        for (const auto& t : c_tokens) freq[t]++;

        double score = 0;
        for (const auto& t : q_set) {
            if (freq.count(t)) {
                score += (1.0 + log(freq[t]));
            }
        }
        return score / log(1.0 + c_tokens.size());
    }
};

class ResearchEngine {
public:
    struct Source {
        std::string title;
        std::string url;
        std::string content;
        double relevance;
    };

    std::vector<Source> rank_sources(const std::string& query, std::vector<std::map<std::string, std::string>> raw_sources) {
        std::vector<Source> ranked;
        for (const auto& raw : raw_sources) {
            std::string content = raw.at("content");
            double score = TextProcessor::calculate_score(query, content);
            ranked.push_back({raw.at("title"), raw.at("url"), content, score});
        }
        std::sort(ranked.begin(), ranked.end(), [](const Source& a, const Source& b) {
            return a.relevance > b.relevance;
        });
        return ranked;
    }
};

PYBIND11_MODULE(local_perplex_core, m) {
    py::class_<ResearchEngine::Source>(m, "Source")
        .def_readwrite("title", &ResearchEngine::Source::title)
        .def_readwrite("url", &ResearchEngine::Source::url)
        .def_readwrite("content", &ResearchEngine::Source::content)
        .def_readwrite("relevance", &ResearchEngine::Source::relevance);

    py::class_<ResearchEngine>(m, "ResearchEngine")
        .def(py::init<>())
        .def("rank_sources", &ResearchEngine::rank_sources);

    m.def("calculate_score", &TextProcessor::calculate_score);
    m.def("tokenize", &TextProcessor::tokenize);
}
