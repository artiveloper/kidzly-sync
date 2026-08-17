package kr.kidzly.sync.application.port

import arrow.core.Either
import kr.kidzly.sync.application.model.LegalDongCodePage
import kr.kidzly.sync.domain.error.DomainError

interface LegalDongCodeApiPort {
    /**
     * 법정동코드 전체 조회 (odcloud.kr) — 페이지 단위.
     * @param page 1부터 시작
     * @param perPage 페이지당 건수 (최대 2000 확인됨)
     */
    fun fetchLegalDongCodes(page: Int, perPage: Int): Either<DomainError, LegalDongCodePage>
}
