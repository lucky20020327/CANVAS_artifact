#include "example/library_membership/domain/librarycarddomain/sk_librarycarddomain_server.h"
#include "example/errorcode/ec_module_librarycarddomain.h"
#include "example/errorcode/ec_module_host.h"
#include "example/library_membership/domain/librarycarddomain/sk_librarycarddomain_entity_library.h"

using namespace librarycarddomain;

class LibraryCardDomainCheckReaderCardEligibilityHandler {
 public:
  LibraryCardDomainCheckReaderCardEligibilityHandler(
      LibraryCardDomainContext& context,
      const librarycarddomain::CheckReaderCardEligibilityReq& request)
      : context_(context),
        request_(request) {}

   librarycarddomain::CheckReaderCardEligibilityResp Process() {
      // 调用 Handler 类内的私有成员函数完成业务逻辑，以此对实际执行流程时节点的顺序进行合理组合与有效编排。
  }
private:

  // 成员变量
  LibraryCardDomainContext& context_;
  const librarycarddomain::CheckReaderCardEligibilityReq& request_;
};

librarycarddomain::CheckReaderCardEligibilityResp librarycarddomain::LibraryCardDomain_CheckReaderCardEligibility(  // 事件处理函数
    LibraryCardDomainContext& context,
    const librarycarddomain::CheckReaderCardEligibilityReq& request) {
  LibraryCardDomainCheckReaderCardEligibilityHandler handler{context, request};
  return handler.Process();
}
