package kr.kidzly.sync.application.port

import arrow.core.Either
import kr.kidzly.sync.application.model.PlaygroundPage
import kr.kidzly.sync.domain.error.DomainError

interface SafemapApiPort {
    /**
     * 어린이놀이시설정보 조회 (IF_0007) — 페이지 단위.
     * @param pageNo 1부터 시작
     * @param numOfRows 페이지당 건수
     */
    fun fetchPlaygrounds(pageNo: Int, numOfRows: Int): Either<DomainError, PlaygroundPage>
}
