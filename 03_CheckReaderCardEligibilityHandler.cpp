#include "example/library_membership/domain/librarycarddomain/sk_librarycarddomain_server.h"
#include "example/errorcode/ec_module_librarycarddomain.h"
#include "example/errorcode/ec_module_host.h"
#include "example/library_membership/domain/librarycarddomain/sk_librarycarddomain_entity_library.h"

#include <cstdint>
#include <memory>
#include <string>

using namespace librarycarddomain;

namespace {

constexpr uint32_t kAccountStatusClosed = 2;
constexpr uint32_t kProfileComplete = 1;
constexpr uint32_t kReviewAllowed = 1;
constexpr uint32_t kRemovedFlagActive = 0;
constexpr uint32_t kEligible = 1;
constexpr char kDocumentTypeStandard[] = "1";
constexpr char kDocumentTypePassport[] = "2";
constexpr char kDocumentTypeOther[] = "3";

}  // namespace

class LibraryCardDomainCheckReaderCardEligibilityHandler {
 public:
  LibraryCardDomainCheckReaderCardEligibilityHandler(
      LibraryCardDomainContext& context,
      const librarycarddomain::CheckReaderCardEligibilityReq& request)
      : context_(context),
        request_(request) {}

  librarycarddomain::CheckReaderCardEligibilityResp Process() {
    // 步骤1: 校验入口参数
    check_request_constraints();

    // 步骤2: 查询读者账户
    auto reader_account = query_reader_account();

    // 步骤3: 统计未删除的办证记录数量
    uint32_t open_count = count_active_card_openings();

    // 步骤4: 如果读者证件类型不是常用证件
    uint32_t review_allowed = 0;
    if (request_.document_type() != kDocumentTypeStandard) {
      // 步骤5: 查询非常用证件的复核资格
      review_allowed = query_alternate_document_review();
    }

    // 步骤6: 判断是否可以新办借书证
    decide_card_eligibility(reader_account.get(), open_count, review_allowed);

    // 步骤7: 返回办理结果
    return build_response();
  }

 private:
  //
  // 函数说明：
  // 按入口契约检查必填参数和概念约束，不满足时返回参数错误
  // 入参说明：
  // 无（字段从成员变量 request_ 获取）
  // 返回值说明：
  // 无
  //
  auto check_request_constraints() -> void {
    bool document_type_allowed = request_.document_type() == kDocumentTypeStandard ||
                                 request_.document_type() == kDocumentTypePassport ||
                                 request_.document_type() == kDocumentTypeOther;
    bool constraints_satisfied = request_.reader_id() >= 1 &&
                                 request_.home_branch().size() >= 4 &&
                                 request_.home_branch().size() <= 16 &&
                                 document_type_allowed &&
                                 request_.profile_complete() <= 1 &&
                                 request_.max_open_cards() >= 1 &&
                                 request_.max_open_cards() <= 5;
    // 入口参数检查_规则0: 必填参数未传入或不满足取值约束
    if (!constraints_satisfied) {
      UCLI_ERROR << "参数不符合契约约束"
                 << librarycarddomain::errorcode::INVALID_PARAM;
    }
  }

  //
  // 函数说明：
  // 按读者编号查询读者账户。查不到则继续；账户已关闭则返回对应错误码
  // 入参说明：
  // 无（reader_id 从成员变量 request_ 获取）
  // 返回值说明：
  // std::unique_ptr<entity_library::ReaderAccount> 读者账户；查不到时为空
  //
  auto query_reader_account() -> std::unique_ptr<entity_library::ReaderAccount> {
    entity_library::ReaderAccountRepo account_repo;
    entity_library::ReaderAccountPoRouteKey route_key;
    route_key.set_reader_id(request_.reader_id());

    auto outcome = uclient::MakeOutcome([&]() {
      return account_repo.GetByPrimaryKey(route_key, request_.reader_id());
    });

    // 读者账户查询结果判断_规则0: 查询不到读者账户，继续执行下一步
    if (auto exception = outcome.TryTakeException(hostcomm::errorcode::DAO_GET_EMPTY_RECORD);
        exception) {
      return nullptr;
    }

    auto reader_account = outcome.TakeResult();
    // 读者账户查询结果判断_规则1: 读者账户状态为已关闭
    if (reader_account.account_status() == kAccountStatusClosed) {
      UCLI_ERROR << fmt::format("读者账户已关闭, reader_id[{}]", request_.reader_id())
                 << librarycarddomain::errorcode::ACCOUNT_CLOSED;
    }
    return std::make_unique<entity_library::ReaderAccount>(std::move(reader_account));
  }

  //
  // 函数说明：
  // 统计该读者删除标记为 0 的办证记录数量
  // 入参说明：
  // 无（reader_id 从成员变量 request_ 获取）
  // 返回值说明：
  // uint32_t 未删除的办证记录数量
  //
  auto count_active_card_openings() -> uint32_t {
    entity_library::CardOpeningRecordRepo record_repo;
    entity_library::CardOpeningRecordPoRouteKey route_key;
    route_key.set_reader_id(request_.reader_id());

    auto outcome = uclient::MakeOutcome([&]() {
      return record_repo.Count(route_key, kRemovedFlagActive);
    });
    return outcome.TakeResult();
  }

  //
  // 函数说明：
  // 查询非常用证件是否已通过复核。查不到记录时按未通过继续
  // 入参说明：
  // 无（reader_id 从成员变量 request_ 获取）
  // 返回值说明：
  // uint32_t 复核结果，1 表示已通过，0 表示未通过
  //
  auto query_alternate_document_review() -> uint32_t {
    entity_library::AlternateDocumentReviewRepo review_repo;
    entity_library::AlternateDocumentReviewPoRouteKey route_key;
    route_key.set_reader_id(request_.reader_id());

    auto outcome = uclient::MakeOutcome([&]() {
      return review_repo.GetByPrimaryKey(route_key, request_.reader_id());
    });

    // 步骤5补充说明: 查询不到记录，则按未通过复核继续下一步
    if (auto exception = outcome.TryTakeException(hostcomm::errorcode::DAO_GET_EMPTY_RECORD);
        exception) {
      return 0;
    }
    return outcome.TakeResult().review_allowed();
  }

  //
  // 函数说明：
  // 按资格规则表判断是否可以新办借书证，命中拒绝规则时返回对应错误码
  // 入参说明：
  // reader_account - 步骤2查询到的读者账户，查不到时为空
  // open_count - 步骤3统计到的未删除办证记录数量
  // review_allowed - 步骤5的复核结果；未进入该分支时为 0
  // 返回值说明：
  // 无
  //
  auto decide_card_eligibility(const entity_library::ReaderAccount* reader_account,
                               uint32_t open_count,
                               uint32_t review_allowed) -> void {
    bool account_closed = reader_account != nullptr &&
                          reader_account->account_status() == kAccountStatusClosed;
    // 新办借书证资格判断_规则0: 读者账户未关闭为假
    if (account_closed) {
      UCLI_ERROR << fmt::format("读者账户已关闭, reader_id[{}]", request_.reader_id())
                 << librarycarddomain::errorcode::ACCOUNT_CLOSED;
    }

    // 新办借书证资格判断_规则1: 读者资料已填写完整为假
    if (request_.profile_complete() != kProfileComplete) {
      UCLI_ERROR << "读者资料未填写完整"
                 << librarycarddomain::errorcode::PROFILE_INCOMPLETE;
    }

    // 新办借书证资格判断_规则2: 未删除的办证记录数量小于办证上限为假
    if (open_count >= request_.max_open_cards()) {
      UCLI_ERROR << fmt::format("办证数量达到馆方上限, open_count[{}], max_open_cards[{}]",
                                open_count, request_.max_open_cards())
                 << librarycarddomain::errorcode::OPEN_CARD_LIMIT_REACHED;
    }

    bool document_accepted = request_.document_type() == kDocumentTypeStandard ||
                             review_allowed == kReviewAllowed;
    // 新办借书证资格判断_规则3: 常用证件或复核已通过为假
    if (!document_accepted) {
      UCLI_ERROR << "非常用证件需要先完成复核"
                 << librarycarddomain::errorcode::DOCUMENT_REVIEW_REQUIRED;
    }
  }

  //
  // 函数说明：
  // 构造允许新办的响应
  // 入参说明：
  // 无
  // 返回值说明：
  // CheckReaderCardEligibilityResp 办理结果
  //
  auto build_response() -> librarycarddomain::CheckReaderCardEligibilityResp {
    librarycarddomain::CheckReaderCardEligibilityResp response;
    response.set_eligible(kEligible);
    response.set_denial_reason("");
    return response;
  }

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
