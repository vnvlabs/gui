#include "PythonInterface.h"


int main(int argc, char** argv) {

     VnV::Python::ReaderWrapper a("/home/ben/injectionPoint/out", "file", "{}", true);
     a.join();
     a.datachildren();


}