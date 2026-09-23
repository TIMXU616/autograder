"""桩版数据：字段与 docs/接口契约.md 第 7.2 / 7.3 / 7.4 节的成功 JSON 示例逐字段一致。

仅用于阶段一桩版，阶段二真实现后本文件删除。
"""

STUB_UPLOAD = {
    "report_id": "rpt-2001",
    "template_id": "tpl-1001",
    "filename": "单链表实验报告.docx",
    "file_sha256": "a3f5c9d2e1b8f7a6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3",
    "status": "uploaded",
    "uploaded_at": "2026-09-21T01:15:00+08:00",
}

STUB_GRADING_ACCEPTED = {
    "report_id": "rpt-2001",
    "status": "parsing",
    "attempt_no": 1,
    "accepted_at": "2026-09-21T01:16:00+08:00",
}

STUB_RESULT_SUCCESS = {
    "report_id": "rpt-2001",
    "template_id": "tpl-1001",
    "filename": "单链表实验报告.docx",
    "student": "单链表实验报告",
    "status": "success",
    "attempt_no": 1,
    "model": "glm-4.7",
    "total_score": 58.0,
    "consistency": None,
    "comment": (
        "本报告章节完整，实验目的与原理阐述准确，给出了多组测试数据并做了结果分析，"
        "对空链表等边界情况有明确处理说明。主要优点是算法设计有复杂度分析、代码注释清晰；"
        "主要问题是部分函数未给出代码，测试数据量偏少。"
    ),
    "highlights": ["逆置采用三指针迭代法并给出复杂度分析", "测试覆盖了空链表等边界情况"],
    "suggestions": ["补充删除与逆置函数的完整代码", "增加一组大规模数据的性能测试"],
    "warnings": [],
    "error_code": None,
    "items": [
        {
            "item_id": 1,
            "name": "实验目的与原理阐述",
            "max_score": 20,
            "score": 20.0,
            "level": "excellent",
            "evidence": "掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用",
            "reason": "实验目的明确，原理对节点结构、指针域与复杂度阐述完整",
            "status": "graded",
            "confidence": "high",
            "error_code": None,
        },
        {
            "item_id": 2,
            "name": "算法与实现说明",
            "max_score": 20,
            "score": 18.0,
            "level": "good",
            "evidence": "链表逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转指向",
            "reason": "核心算法有文字说明与代码节选，但删除与逆置未附关键代码扣 2 分",
            "status": "graded",
            "confidence": "medium",
            "error_code": None,
        },
        {
            "item_id": 3,
            "name": "结果与分析",
            "max_score": 20,
            "score": 20.0,
            "level": "excellent",
            "evidence": "构造含 10 个元素的链表，头插法插入后遍历输出顺序与插入顺序相反，符合预期",
            "reason": "给出测试结果，并对效率、边界与异常分别做了分析",
            "status": "graded",
            "confidence": "high",
            "error_code": None,
        },
    ],
    "grading_started_at": "2026-09-21T01:16:02+08:00",
    "finished_at": "2026-09-21T01:16:11+08:00",
}
