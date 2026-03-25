#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <cctype>
#include <cmath>
#include <unordered_map>
#include <iostream>

namespace py = pybind11;

class TextProcessor {
public:
    static std::vector<std::string> tokenize(const std::string& text) {
        std::vector<std::string> tokens;
        if (text.empty()) return tokens;
        tokens.reserve(text.length() / 6);
        const char* start = text.c_str();
        const char* end = start + text.length();
        const char* p = start;

        while (p < end) {
            // Skip non-alnum
            while (p < end && !std::isalnum(static_cast<unsigned char>(*p))) p++;
            if (p == end) break;

            const char* word_start = p;
            while (p < end && std::isalnum(static_cast<unsigned char>(*p))) p++;

            if (p - word_start > 2) {
                std::string word(word_start, p - word_start);
                for (char &c : word) {
                    c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
                }
                tokens.push_back(std::move(word));
            }
        }
        return tokens;
    }

    static double calculate_relevance(const std::string& query, const std::string& content) {
        auto q_tokens = tokenize(query);
        auto c_tokens = tokenize(content);
        if (q_tokens.empty() || c_tokens.empty()) return 0.0;

        std::unordered_map<std::string, int> c_freq;
        c_freq.reserve(c_tokens.size());
        for (const auto& t : c_tokens) c_freq[t]++;

        double score = 0;
        for (const auto& qt : q_tokens) {
            auto it = c_freq.find(qt);
            if (it != c_freq.end()) {
                score += (1.0 + std::log(it->second));
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
    std::string category;
};

class ResearchEngine {
public:
    ResearchEngine() {}

    std::string classify_source(const std::string& url) {
        std::string low_url = url;
        std::transform(low_url.begin(), low_url.end(), low_url.begin(), ::tolower);
        if (low_url.find(".edu") != std::string::npos || low_url.find("arxiv") != std::string::npos) return "Academic";
        if (low_url.find("reuters") != std::string::npos || low_url.find("bbc") != std::string::npos || low_url.find("news") != std::string::npos) return "News";
        if (low_url.find("github") != std::string::npos || low_url.find("stackoverflow") != std::string::npos) return "Technical";
        if (low_url.find(".gov") != std::string::npos) return "Government";
        return "General";
    }

    std::vector<SourceItem> rank_sources(const std::string& query, py::list raw_sources) {
        std::vector<SourceItem> ranked;
        for (auto item : raw_sources) {
            py::dict d = item.cast<py::dict>();
            std::string title = d.contains("title") ? d["title"].cast<std::string>() : "";
            std::string url = d.contains("url") ? d["url"].cast<std::string>() : "";
            std::string content = d.contains("content") ? d["content"].cast<std::string>() : "";

            double score = TextProcessor::calculate_relevance(query, content);
            std::string category = classify_source(url);

            // Credibility boost
            if (category == "Academic") score *= 1.25;
            if (category == "Government") score *= 1.15;

            ranked.push_back({title, url, content, score, category});
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
        .def_readwrite("relevance", &SourceItem::relevance)
        .def_readwrite("category", &SourceItem::category);

    py::class_<ResearchEngine>(m, "ResearchEngine")
        .def(py::init<>())
        .def("rank_sources", &ResearchEngine::rank_sources);

    m.def("calculate_score", &TextProcessor::calculate_relevance);
    m.def("tokenize", &TextProcessor::tokenize);
}
