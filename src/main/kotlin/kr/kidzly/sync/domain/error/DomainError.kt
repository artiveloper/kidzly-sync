package kr.kidzly.sync.domain.error

sealed class DomainError {
    data class ApiCallError(val statusCode: Int, val code: String?, val message: String) : DomainError()
    data class ParseError(val message: String, val cause: Throwable? = null) : DomainError()
    data class NetworkError(val message: String, val cause: Throwable? = null) : DomainError()
    data object RateLimitExceeded : DomainError()
    data object Unauthorized : DomainError()
    data class Unknown(val message: String, val cause: Throwable? = null) : DomainError()
}
