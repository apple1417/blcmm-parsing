#include "blcmm.hpp"

#include <iostream>
#include <string>

static void put_xml_escaped(char c, std::ostream& stream) {
    switch (c) {
        case '"': stream << "&quot;"; break;
        case '\'': stream << "&apos;"; break;
        case '<': stream << "&lt;"; break;
        case '>': stream << "&gt;"; break;
        case '&': stream << "&amp;"; break;
        default: stream << c; break;
    }
}

void preprocess_blcmm_file(std::istream& blcmm_input, std::ostream& xml_output) {
    for (std::string line; std::getline(blcmm_input, line); ) {
        // Stop after the end of the blcmm section
        if (line.rfind("</BLCMM>", 0) == 0) {
            xml_output << line;
            break;
        }
        // Ignore the filtertool warning
        if (line.rfind("#<!!!", 0) == 0) {
            continue;
        }

        auto tag_start = line.find_first_of('<');
        if (tag_start == std::string::npos) {
            throw blcmm_parser_error("Failed to parse line (couldn't find inital tag): " + line);
        }

        auto tag_name_end = line.find_first_of("> ", tag_start);
        if (tag_name_end == std::string::npos) {
            throw blcmm_parser_error("Failed to parse line (inital tag doesn't close): " + line);
        }
        xml_output << line.substr(tag_start, tag_name_end - tag_start + 1);

        auto content_start = tag_name_end + 1;

        if (line[tag_name_end] != '>') {
            auto tag_body_section_start = content_start;
            while (true) {
                auto tag_body_section_end = line.find_first_of("\">", tag_body_section_start);
                if (tag_body_section_end == std::string::npos) {
                    throw blcmm_parser_error(
                        "Failed to parse line (inital tag doesn't close): " + line
                    );
                }
                xml_output << line.substr(
                    tag_body_section_start,
                    tag_body_section_end - tag_body_section_start + 1
                );
                if (line[tag_body_section_end] == '>') {
                    break;
                }

                auto attr_val_end = tag_body_section_end;
                do {
                    attr_val_end = line.find_first_of('"', attr_val_end + 1);
                    if (attr_val_end == std::string::npos) {
                        throw blcmm_parser_error(
                            "Failed to parse line (attribute value doesn't close): " + line
                        );
                    }
                } while (line[attr_val_end - 1] == '\\');

                for (size_t i = tag_body_section_end + 1; i < attr_val_end; i++) {
                    put_xml_escaped(line[i], xml_output);
                }
                xml_output << '"';

                tag_body_section_start = attr_val_end + 1;
            }

            content_start = tag_body_section_start + 1;
        }

        auto closing_tag_str = (
            "</" + line.substr(tag_start + 1, tag_name_end - tag_start - 1) + ">"
        );
        auto closing_tag_start = line.rfind(closing_tag_str);
        if (closing_tag_start != std::string::npos) {
            for (size_t i = content_start; i < closing_tag_start; i++) {
                put_xml_escaped(line[i], xml_output);
            }

            xml_output << closing_tag_str;
        }
    }

    if (blcmm_input.fail()) {
        if (blcmm_input.eof()) {
            throw blcmm_parser_error("IO Error while reading input (eof)");
        }
        throw blcmm_parser_error("IO Error while reading input");
    }

    if (xml_output.fail()) {
        throw blcmm_parser_error("IO Error while writing output");
    }
}

bool in_comma_seperated_list(const std::string& value, const std::string& list) {
    size_t entry_start = 0;
    while (entry_start < list.size()) {
        auto entry_end = list.find_first_of(',', entry_start);
        if (list.compare(entry_start, entry_end - entry_start, value) == 0) {
            return true;
        };
        if (entry_end == std::string::npos) {
            break;
        }
        entry_start = entry_end + 1;
    }
    return false;
}
