#include <pybind11/pybind11.h>
#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>

#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>
#include <iomanip>

namespace py = pybind11;
using namespace rapidjson;
using namespace std;

string invert(const char* json) {
    Document inverted_abstract;
    inverted_abstract.Parse(json);

    Value& ind_len_ptr = inverted_abstract["IndexLength"];
    const int ind_len = ind_len_ptr.GetInt();
    const Value& tokens = inverted_abstract["InvertedIndex"];
    string abstract_arr[ind_len];

//    printf("IndexLength: %d\n", ind_len);

    for (Value::ConstMemberIterator iter = tokens.MemberBegin(); iter != tokens.MemberEnd(); ++iter){
        const char* token = iter->name.GetString();
        const Value& token_positions = tokens[token];

        for (SizeType i = 0; i < token_positions.Size(); i++) {
            abstract_arr[token_positions[i].GetInt()] = token;
        }
    }

    ostringstream abstract;
    for(const auto & i : abstract_arr) abstract << i << " ";

    return abstract.str();
}


int main() {
    const char* json = "{\"IndexLength\": 169, \"InvertedIndex\": {\"Lipid\": [0], \"metabolism\": [1, 157], \"plays\": [2], \"an\": [3, 129], \"important\": [4], \"role\": [5, 26, 142], \"in\": [6, 13, 34, 44, 67, 91, 113, 116, 147], \"the\": [7, 25, 28, 83, 119, 140, 144], \"occurrence\": [8], \"and\": [9, 81, 94, 101, 115, 150], \"development\": [10, 159], \"of\": [11, 27, 42, 53, 71, 143, 160], \"cancer,\": [12], \"particular,\": [14], \"digestive\": [15], \"system\": [16], \"tumors\": [17], \"such\": [18], \"as\": [19, 62, 64], \"colon\": [20], \"cancer.\": [21], \"Here,\": [22], \"we\": [23], \"investigated\": [24], \"fatty\": [29, 77], \"acid-binding\": [30], \"protein\": [31], \"5\": [32], \"(FABP5)\": [33], \"colorectal\": [35], \"cancer\": [36], \"(CRC).\": [37], \"We\": [38], \"observed\": [39], \"marked\": [40], \"down-regulation\": [41], \"FABP5\": [43, 54, 74, 126], \"CRC.\": [45], \"Data\": [46], \"from\": [47], \"functional\": [48], \"assays\": [49], \"revealed\": [50], \"inhibitory\": [51], \"effects\": [52, 111], \"on\": [55], \"cell\": [56, 103], \"proliferation,\": [57], \"colony\": [58], \"formation,\": [59], \"migration,\": [60], \"invasion\": [61], \"well\": [63], \"tumor\": [65, 148], \"growth\": [66], \"vivo.\": [68], \"In\": [69], \"terms\": [70], \"mechanistic\": [72], \"insights,\": [73], \"interacted\": [75], \"with\": [76], \"acid\": [78], \"synthase\": [79], \"(FASN)\": [80], \"activated\": [82], \"ubiquitin\": [84], \"proteasome\": [85], \"pathway,\": [86], \"leading\": [87], \"to\": [88, 158], \"a\": [89, 106, 152], \"decrease\": [90], \"FASN\": [92, 107], \"expression\": [93, 127], \"lipid\": [95, 156], \"accumulation,\": [96], \"moreover,\": [97], \"suppressing\": [98], \"mTOR\": [99], \"signaling\": [100], \"facilitating\": [102], \"autophagy.\": [104], \"Orlistat,\": [105], \"inhibitor,\": [108], \"exerted\": [109], \"anti-cancer\": [110], \"both\": [112], \"vivo\": [114], \"vitro.\": [117], \"Furthermore,\": [118], \"upstream\": [120], \"RNA\": [121], \"demethylase\": [122], \"ALKBH5\": [123], \"positively\": [124], \"regulated\": [125], \"via\": [128], \"m6A-independent\": [130], \"mechanism.\": [131], \"Overall,\": [132], \"our\": [133], \"collective\": [134], \"findings\": [135], \"offer\": [136], \"valuable\": [137], \"insights\": [138], \"into\": [139], \"critical\": [141], \"ALKBH5/FABP5/FASN/mTOR\": [145], \"axis\": [146], \"progression\": [149], \"uncover\": [151], \"potential\": [153], \"mechanism\": [154], \"linking\": [155], \"CRC,\": [161], \"providing\": [162], \"novel\": [163], \"therapeutic\": [164], \"targets\": [165], \"for\": [166], \"future\": [167], \"interventions.\": [168]}}";

    string abstract = invert(json);
    printf("%s\n", abstract.c_str());

     return 0;
}




PYBIND11_MODULE(test, m) {
    m.doc() = "OpenAlex abstract inverter";
    m.def("invert", &invert, "Convert OpenAlex abstract_inverted_index into proper abstract.", py::arg("abs_inv_ind"));
}