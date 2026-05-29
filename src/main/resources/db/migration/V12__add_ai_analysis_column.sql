ALTER TABLE daycares
    ADD COLUMN IF NOT EXISTS ai_analysis JSONB;

COMMENT ON COLUMN daycares.ai_analysis IS 'AI 요약 분석 결과 (summary, strengths, considerations, tags)';
