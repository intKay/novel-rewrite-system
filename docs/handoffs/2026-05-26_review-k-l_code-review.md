# 代码审查交接记录：Review-K & Review-L

## 审查范围

- Review-K：风格分析服务（`src/novel_rewrite_system/analysis/service.py`）
- Review-L：初稿生成服务（`src/novel_rewrite_system/generation/service.py`）

## 审查结论

| 审查 | 结论 | 是否可作为后续依赖 |
|------|------|-------------------|
| Review-K | 通过 | 可以 |
| Review-L | 通过 | 可以 |

两项服务均符合接口边界、模型调用解耦、错误处理、保存逻辑、测试质量和范围控制的全部检查项。零阻塞问题。

## Review-K 非阻塞建议

| 编号 | 问题 | 位置 | 建议 |
|------|------|------|------|
| K-1 | `_save_report` 未处理文件系统异常 | `analysis/service.py:85-89` | 磁盘满/权限不足时冒泡原始 OSError；建议 try/except 转译为 ProjectError |
| K-2 | `source_count` 基于全部 chunks 而非实际分析切片 | `analysis/service.py:75` | 当指定 max_chunks 时 source_count 来自全量 chunks 而非截断后；语义上可改为 total_source_count |
| K-3 | `build_style_analysis_prompt` 抛 ValueError 而非 EmptyTextError | `analysis/prompts/style.py:90` | 与 Task E 错误类型体系不一致；Task K 服务已前置校验规避，但直接调用 prompt 构建器时行为不统一 |

## Review-L 非阻塞建议

| 编号 | 问题 | 位置 | 建议 |
|------|------|------|------|
| L-1 | `_save_draft` 未处理文件系统异常 | `generation/service.py:81-85` | 同 K-1，保存时可能抛出原始 OSError |
| L-2 | `build_draft_generation_prompt` 抛 ValueError 而非 EmptyTextError | `generation/prompts/draft.py:67` | 同 K-3，与错误类型体系不一致 |
| L-3 | `chapter_plan_section` 空段 | `generation/prompts/draft.py:127-138` | chapter_plan 和 chapter_count 均为 None 时 prompt 出现孤立 `## 章节计划` 标题；属 Task G 实现细节 |

## 批量修复提示词（后续统一处理 K-3 + L-2）

```
请统一 prompt 构建器中的异常类型，将 ValueError 改为 EmptyTextError：

1. src/novel_rewrite_system/analysis/prompts/style.py:90
   ValueError("chunks 不能为空") → EmptyTextError(message="chunks 不能为空")

2. src/novel_rewrite_system/generation/prompts/draft.py:67
   ValueError("style_report 不能为空") → EmptyTextError(message="style_report 不能为空")

3. 同步更新 tests/test_style_analysis_prompt.py 和 tests/test_draft_generation_prompt.py 中
   对应测试的 pytest.raises 异常类型断言（ValueError → EmptyTextError）。

注意：不修改 service.py 的任何文件，不修改其他模块。
```

## 修改范围

- 新增：`docs/handoffs/2026-05-26_review-k-l_code-review.md`（本文件）
- 未修改任何源代码
