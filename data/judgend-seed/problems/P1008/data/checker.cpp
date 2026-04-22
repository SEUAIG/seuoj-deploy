#include "testlib.h"
#include <string>
#include <algorithm>
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);
    std::string input = inf.readWord();
    std::string output = ouf.readWord();
    std::string expected = ans.readWord();
    if (expected == "impossible") {
        if (output != "impossible")
            quitf(_wa, "Expected impossible, got '%s'", output.substr(0, 50).c_str());
        quitf(_ok, "");
    }
    std::string rev = output;
    std::reverse(rev.begin(), rev.end());
    if (output != rev)
        quitf(_wa, "Not a palindrome");
    std::string si = input, so = output;
    std::sort(si.begin(), si.end());
    std::sort(so.begin(), so.end());
    if (si != so)
        quitf(_wa, "Character frequencies don't match");
    quitf(_ok, "");
}
