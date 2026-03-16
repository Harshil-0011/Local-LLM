#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <cctype>
#include <cmath>
#include <map>
#include <iostream>

namespace py = pybind11;

class TextProcessor {
public:
    static std::vector<std::string> tokenize(const std::string& text) {
        std::vector<std::string> tokens;
        std::string token;
        std::stringstream ss(text);
        while (ss >> token) {
            std::string clean;
            for (unsigned char c : token) {
                if (std::isalnum(c)) clean += (char)std::tolower(c);
            }
            if (clean.length() > 2) tokens.push_back(clean);
        }
        return tokens;
    }

    static double calculate_relevance(const std::string& query, const std::string& content) {
        auto q_tokens = tokenize(query);
        auto c_tokens = tokenize(content);
        if (q_tokens.empty() || c_tokens.empty()) return 0.0;

        std::map<std::string, int> c_freq;
        for (const auto& t : c_tokens) c_freq[t]++;

        double score = 0;
        for (const auto& qt : q_tokens) {
            if (c_freq.count(qt)) {
                score += (1.0 + std::log(c_freq[qt]));
            }
        }
        return score / std::log(1.0 + (double)c_tokens.size());
    }
};

struct SourceItem {
    std::string title;
    std::string url;
    std::string content;
    double relevance;
};

class ResearchEngine {
public:
    ResearchEngine() {}

    std::vector<SourceItem> rank_sources(const std::string& query, py::list raw_sources) {
        std::vector<SourceItem> ranked;
        for (auto item : raw_sources) {
            py::dict d = item.cast<py::dict>();
            std::string title = d.contains("title") ? d["title"].cast<std::string>() : "";
            std::string url = d.contains("url") ? d["url"].cast<std::string>() : "";
            std::string content = d.contains("content") ? d["content"].cast<std::string>() : "";

            double score = TextProcessor::calculate_relevance(query, content);
            ranked.push_back({title, url, content, score});
        }

        std::sort(ranked.begin(), ranked.end(), [](const SourceItem& a, const SourceItem& b) {
            return a.relevance > b.relevance;
        });

        return ranked;
    }
};

PYBIND11_MODULE(local_perplex_core, m) {
    py::class_<SourceItem>(m, "Source")
        .def_readwrite("title", &SourceItem::title)
        .def_readwrite("url", &SourceItem::url)
        .def_readwrite("content", &SourceItem::content)
        .def_readwrite("relevance", &SourceItem::relevance);

    py::class_<ResearchEngine>(m, "ResearchEngine")
        .def(py::init<>())
        .def("rank_sources", &ResearchEngine::rank_sources);

    m.def("calculate_score", &TextProcessor::calculate_relevance);
    m.def("tokenize", &TextProcessor::tokenize);
}
