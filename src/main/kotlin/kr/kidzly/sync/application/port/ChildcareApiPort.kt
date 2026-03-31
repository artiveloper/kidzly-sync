package kr.kidzly.sync.application.port

import arrow.core.Either
import kr.kidzly.sync.application.model.ClosedDaycareInfo
import kr.kidzly.sync.application.model.DaycareData
import kr.kidzly.sync.application.model.NewDaycareInfo
import kr.kidzly.sync.application.model.SigunguInfo
import kr.kidzly.sync.domain.error.DomainError

interface ChildcareApiPort {
    /** 시도명으로 시군구 목록 조회 (cpmsapi020) */
    fun fetchSigunguList(arname: String): Either<DomainError, List<SigunguInfo>>

    /** 시군구코드로 어린이집 상세 목록 조회 (cpmsapi030) */
    fun fetchDaycareDetails(arcode: String): Either<DomainError, List<DaycareData>>

    /** 월별 신규시설 목록 조회 (cpmsapi018) */
    fun fetchNewDaycares(yyyymm: String): Either<DomainError, List<NewDaycareInfo>>

    /** 월별 폐지시설 목록 조회 (cpmsapi019) */
    fun fetchClosedDaycares(yyyymm: String): Either<DomainError, List<ClosedDaycareInfo>>
}
