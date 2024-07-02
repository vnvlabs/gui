
#include <functional>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "PythonInterface.h"
#include "INodes.h"

  VnV::Python::ReaderWrapper::ReaderWrapper(std::string filename, std::string reader, std::string config, bool async) {
      rootNode = VnV::Nodes::getEngineReader(filename, async, true);
  }

  VnV::Python::ReaderWrapper::~ReaderWrapper(){
    if (rootNode) {
      rootNode->kill();
    }
  }

  void VnV::Python::ReaderWrapper::datachildren() {
    std::cout << rootNode->getDataChildren(rootNode->getId(),2) << std::endl;
  }

  void VnV::Python::ReaderWrapper::gettree() {
    std::cout << rootNode->getTree(0) << std::endl;
  }


  void VnV::Python::ReaderWrapper::join() {
      rootNode->getThread()->join();
  }
