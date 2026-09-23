"""业务异常体系。每条异常带契约错误码，供上层映射为 HTTP 响应或 failed 状态。"""


class GradingError(Exception):
    """基类：所有业务异常都带一个契约错误码。http_status 用于覆盖默认映射。"""

    def __init__(self, code, message, http_status=None):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class UnsupportedTypeError(GradingError):
    def __init__(self, message="仅支持 docx / pdf 格式"):
        super().__init__(4001, message)


class TooLargeError(GradingError):
    def __init__(self, message="文件超过 20MB 上限"):
        super().__init__(4002, message, http_status=413)


class InvalidParamError(GradingError):
    """查询参数非法，契约收窄后归 4002 + HTTP 400。"""

    def __init__(self, message="参数非法"):
        super().__init__(4002, message, http_status=400)


class NoTextLayerError(GradingError):
    def __init__(self, message="该 PDF 无文本层，无法解析"):
        super().__init__(4003, message)


class EmptyFileError(GradingError):
    def __init__(self, message="文件为空，请重新上传"):
        super().__init__(4004, message)


class EncryptedPdfError(GradingError):
    def __init__(self, message="PDF 已加密，无法解析"):
        super().__init__(4005, message)


class ModelUnavailableError(GradingError):
    def __init__(self, message="评分服务暂不可用，请稍后重试"):
        super().__init__(5001, message)


class ModelTimeoutError(GradingError):
    def __init__(self, message="评分超时，请重试"):
        super().__init__(5002, message)


class InvalidJsonError(GradingError):
    def __init__(self, message="评分结果异常，请重试"):
        super().__init__(5003, message)


class CreditsError(GradingError):
    def __init__(self, message="评分额度不足"):
        super().__init__(5004, message)


class QueueTimeoutError(GradingError):
    def __init__(self, message="排队超时，请稍后重试"):
        super().__init__(5005, message)


class TemplateNotFoundError(GradingError):
    def __init__(self, message="评分点模板不存在"):
        super().__init__(4041, message)


class ReportNotFoundError(GradingError):
    def __init__(self, message="报告不存在"):
        super().__init__(4042, message)


class DuplicateReportError(GradingError):
    def __init__(self, message="该报告已存在"):
        super().__init__(4091, message)
