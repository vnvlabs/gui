#include "PythonInterface.h"


int main(int argc, char** argv) {

     VnV::Python::ReaderWrapper a(argv[1], "file", "{}", false);
     //a.join();
     //a.datachildren();
     a.gettree();

}
