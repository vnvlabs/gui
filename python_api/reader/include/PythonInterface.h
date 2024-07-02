#ifndef IOUTPUTREADER_H
#define IOUTPUTREADER_H

#include <functional>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace VnV {

namespace Nodes {
  class IRootNode;
}

namespace Python {




class ReaderWrapper {
 private:
  std::shared_ptr<Nodes::IRootNode> rootNode;
  long lowerId, upperId;

 public:

  

  ReaderWrapper(std::string filename, std::string reader, std::string config, bool async = true);

  Nodes::IRootNode* get() { return rootNode.get();}

  long getLowerId() { return lowerId; }
  long getUpperId() { return upperId; }

  void join();

  void datachildren();
  void gettree();

  virtual ~ReaderWrapper(); 
};


}  // namespace Python

}

#endif  // IOUTPUTREADER_H

