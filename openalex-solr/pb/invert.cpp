#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>

#include <iostream>
#include <iterator>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>
#include <iomanip>

namespace json = rapidjson;

//using namespace std;

std::string invert(const char* json_str) {
    json::Document inverted_abstract;
    inverted_abstract.Parse(json_str);

    json::Value& ind_len_ptr = inverted_abstract["IndexLength"];
    const int ind_len = ind_len_ptr.GetInt();
    const json::Value& tokens = inverted_abstract["InvertedIndex"];
    std::string abstract_arr[ind_len];

//    printf("IndexLength: %d\n", ind_len);

    for (json::Value::ConstMemberIterator iter = tokens.MemberBegin(); iter != tokens.MemberEnd(); ++iter){
        const char* token = iter->name.GetString();
        const json::Value& token_positions = tokens[token];

        for (json::SizeType i = 0; i < token_positions.Size(); i++) {
            abstract_arr[token_positions[i].GetInt()] = token;
        }
    }

    std::stringstream abstract;
    for(const auto & i : abstract_arr) abstract << i << " ";

    return abstract.str();
}


int main() {
    std::ifstream in_file("../../data/part_001", std::ifstream::binary);
    std::string line;


    while (std::getline(in_file, line)) {
//        std::cout << "The size of str is " << line.length() << " bytes.\n";
        json::Document work;
        work.Parse(line.c_str());

        if(work["abstract_inverted_index"].IsString()) {
            invert(work["abstract_inverted_index"].GetString());
        }

//        printf("IndexLength: %s\n", work["title"].GetString());
    }

//    std::string abstract = invert(json);
//    printf("%s\n", abstract.c_str());

     return 0;
}
