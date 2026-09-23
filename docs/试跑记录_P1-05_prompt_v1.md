# 试跑记录 P1-05 prompt v1

## 试跑环境

- 提示词：`backend/app/prompts/scoring_v1.md`（SYSTEM / USER 两段）
- 模板：`templates/grading/数据结构实验报告.json`（7 项，满分 100）
- 参数：temperature 0.3（默认平衡版），max_tokens 4096，timeout 60s
- 输入构造：user 模板中 `{template_json}` 替换为模板 JSON 全文，`{report_text}` 替换为各用例报告全文

> 执行环境说明：本轮试跑在 LearnBuddy 对话层完成，生产链路走的是 glm-4.7 API（关闭思考），两者模型不同。因此本记录的稳定性结论只在提示词层面成立，需在 P2 任务 6 完成模型调用封装后，用同一批样例在 glm-4.7 上复跑一轮才算对生产链路生效（见 `docs/平台能力清单.md` 保留条款）。

---

## 试跑 1：case_good（章节完整）

### 原始输入（报告全文）

```
# 数据结构实验报告：单链表的实现与应用

## 一、实验目的
掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用，学会用单链表解决顺序存储结构中插入和删除操作不便的问题，体会链式存储结构与顺序存储结构的差异，加深对链表这种动态数据结构存储原理的理解。

## 二、实验原理
单链表由若干节点构成，每个节点包含数据域和指向后继节点的指针域。头指针指向第一个节点，尾节点的指针域为空。插入和删除只需修改相邻节点的指针，在已定位的前提下时间复杂度为 O(1)；按序访问需要从头遍历，时间复杂度为 O(n)。

## 三、实验环境与步骤
环境：Windows 11，gcc 12.2，Visual Studio Code 1.85。
步骤：
1. 定义节点结构体 Node，含数据域 data 与指针域 next。
2. 实现头插法插入函数，新节点插入表头。
3. 实现尾插法插入函数，遍历到表尾后插入。
4. 实现删除指定值节点的函数，先定位前驱再修改指针。
5. 实现链表逆置函数，采用三指针迭代法。
6. 编写 main 函数测试各操作并输出结果。

## 四、算法与数据结构设计
本实验采用带头节点的单链表。选择带头节点的原因是删除头节点时无需单独判断边界条件。逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向，遍历一遍即可完成，时间复杂度 O(n)，空间复杂度 O(1)。插入与删除操作在已定位的前提下时间复杂度为 O(1)。

## 五、代码实现
（代码块：Node 结构体、insert_tail、delete_val、reverse、print 五个函数，含 // 注释，约 50 行，完整见 data/samples/case_good.md）

## 六、测试与结果
| 测试编号 | 操作 | 输出结果 |
| --- | --- | --- |
| 1 | 依次插入 1、2、3、4、5 | 1 2 3 4 5 |
| 2 | 删除值为 3 的节点 | 1 2 4 5 |
| 3 | 对链表逆置 | 5 4 2 1 |
| 4 | 向空链表插入 10 | 10 |

## 七、结果与分析
头插法插入后输出顺序与插入顺序相反，符合头插法在表头插入的特性；尾插法保持元素顺序不变。删除中间节点后链表长度减 1，符合预期。逆置后元素顺序完全反转，说明三指针迭代法正确。异常情况：删除不存在的值时函数直接返回、不崩溃；对空链表调用逆置时 head->next 为空，循环不执行，结果仍为空链表，程序正常退出，说明边界处理正确。综上，实验达到预期目的。
```

### 原始输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理对节点结构、指针域与插入删除复杂度阐述完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"数据结构选择有理由，算法描述与复杂度分析完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":20.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码行数充足，含注释与核心函数","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"给出多组测试数据与对应输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":17.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"分析段完整，含异常与边界情况说明","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"标题、章节编号与表格齐全，结构清晰","status":"graded","confidence":"high","error_code":null}],"total_score":100.0,"warnings":[]}
```

### 验证

1. json.loads：成功。
2. items 七项、每项十个字段齐全：是。
3. evidence 逐条命中：item1 命中 / item2 命中 / item3 命中 / item4 命中 / item5 命中 / item6 命中 / item7 命中，共 7/7 命中。
4. total_score = 100.0 = 各项之和（10+8+15+20+15+17+15）：是。
5. warnings：空数组，未触发（符合预期）。

---

## 试跑 2：case_mid（章节齐全，测试单组、分析复述）

### 原始输入（报告全文）

```
# 数据结构实验报告：冒泡排序的实现

## 一、实验目的
掌握冒泡排序的基本思想和实现方法，理解相邻元素两两比较并交换的排序过程，学会用 C 语言编写排序算法。

## 二、实验原理
冒泡排序是一种交换排序。它的基本过程是：从数组的第一个元素开始，依次比较相邻的两个元素，如果前一个元素大于后一个元素就交换它们的位置。这样一趟下来，最大的元素就会被交换到数组的末尾。然后对剩下的元素重复上述过程，一共进行 n-1 趟，整个数组就排好序了。冒泡排序的时间复杂度为 O(n^2)，属于稳定排序算法。

## 三、实验环境与步骤
环境：Windows 10，Dev-C++ 5.11。
步骤：
1. 打开 Dev-C++，新建一个 C 语言源文件。
2. 编写冒泡排序函数 bubble，用双重循环实现。
3. 在 main 函数中定义一个整型数组并初始化。
4. 调用 bubble 函数对数组排序。
5. 编译运行，观察输出结果。

## 四、算法与数据结构设计
本实验使用一维数组存储待排序的元素。冒泡排序的外层循环控制比较的趟数，内层循环进行相邻元素的比较和交换。每完成一趟，最大的元素就沉到数组的末尾，内层循环的比较次数随之减少一次。

## 五、代码实现
（代码块：bubble 函数 + main 函数，约 18 行，无注释，完整见 data/samples/case_mid.md）

## 六、测试与结果
测试：输入数据为 5、3、8、1，程序运行后输出 1 3 5 8。

## 七、结果与分析
从运行结果来看，输入的 5 3 8 1 经过冒泡排序后变成了 1 3 5 8，说明排序结果是正确的。程序能够把一组乱序的数据从小到大排列，实现了冒泡排序的功能。
```

### 原始输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":8.0,"level":"good","evidence":"掌握冒泡排序的基本思想和实现方法","reason":"有目的与原理但目的段不足 80 字","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 10，Dev-C++ 5.11","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":12.0,"level":"good","evidence":"本实验使用一维数组存储待排序的元素","reason":"有算法描述但算法设计章节未给出复杂度分析","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":12.0,"level":"fair","evidence":"void bubble(int a[], int n)","reason":"代码不足 20 行且无注释","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":9.0,"level":"fair","evidence":"输入数据为 5、3、8、1","reason":"仅一组测试数据","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":10.0,"level":"fair","evidence":"输入的 5 3 8 1 经过冒泡排序后变成了 1 3 5 8","reason":"分析基本复述数据，未提异常或边界","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":12.0,"level":"good","evidence":"# 数据结构实验报告：冒泡排序的实现","reason":"标题与章节编号齐全但无图表","status":"graded","confidence":"high","error_code":null}],"total_score":71.0,"warnings":[]}
```

### 验证

1. json.loads：成功。
2. items 七项、每项十字段齐全：是。
3. evidence 逐条命中：7/7 命中。
4. total_score = 71.0 = 各项之和（8+8+12+12+9+10+12）：是。
5. warnings：空数组，未触发（各评分项均找到依据，仅档位偏低，符合预期）。

---

## 试跑 3：case_code_only（大段代码、几乎无正文）

### 原始输入（报告全文）

```
# 二叉树遍历程序

（代码块：Node 结构体、newnode、preorder、inorder、postorder、height、count、search、main，约 70 行，无注释，完整见 data/samples/case_code_only.md）
```

### 原始输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":0.0,"level":"absent","evidence":null,"reason":"报告中未找到实验目的与原理相关内容","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":0.0,"level":"absent","evidence":null,"reason":"报告中未找到实验环境与步骤相关内容","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":0.0,"level":"absent","evidence":null,"reason":"报告中未找到算法与数据结构设计相关内容","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":16.0,"level":"good","evidence":"void preorder(Node* root)","reason":"代码行数充足且含核心函数，但无注释","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":0.0,"level":"absent","evidence":null,"reason":"报告中未找到测试与结果相关内容","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":0.0,"level":"absent","evidence":null,"reason":"报告中未找到结果与分析相关内容","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":8.0,"level":"fair","evidence":"# 二叉树遍历程序","reason":"有标题但无章节编号与图表","status":"graded","confidence":"high","error_code":null}],"total_score":24.0,"warnings":["第 1 项依据未能在原文中定位","第 2 项依据未能在原文中定位","第 3 项依据未能在原文中定位","第 5 项依据未能在原文中定位","第 6 项依据未能在原文中定位"]}
```

### 验证

1. json.loads：成功。
2. items 七项、每项十字段齐全：是。
3. evidence：item1/2/3/5/6 为 null（对应项无正文），item4/item7 命中原文，符合预期。
4. total_score = 24.0 = 各项之和（0+0+0+16+0+0+8）：是。
5. warnings：已触发（5 条「依据未能定位」），符合 case_code_only 必须触发的要求。

---

## 试跑 4：case_offtopic（跑题：食堂消费调研）

### 原始输入（报告全文）

```
# 关于校园食堂消费情况的调研报告

（全文约 600 字，内容为食堂消费问卷调研：调研目的、调研方式、数据汇总、结果分析、建议，完整见 data/samples/case_offtopic.md）
```

### 原始输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":0.0,"level":"absent","evidence":null,"reason":"报告内容与数据结构实验无关","status":"graded","confidence":"high","error_code":null}],"total_score":0.0,"warnings":["报告内容与数据结构实验无关，各项均 0 分"]}
```

### 验证

1. json.loads：成功。
2. items 七项、每项十字段齐全：是。
3. evidence：全部 null，符合跑题处置（护栏 2）。
4. total_score = 0.0 = 各项之和：是。
5. warnings：已触发「报告内容与数据结构实验无关」，符合 case_offtopic 必须触发的要求；各项 0 分、无任何得分，符合「跑题不硬评」。

---

## 连跑 5 次：case_good（稳定性验证）

### 第 1 次输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理阐述完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"算法描述与复杂度分析完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":20.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码行数充足且含注释与核心函数","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"给出多组测试数据与输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":17.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"含异常与边界分析","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"标题、编号与表格齐全","status":"graded","confidence":"high","error_code":null}],"total_score":100.0,"warnings":[]}
```

### 第 2 次输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"算法描述与复杂度完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":19.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码完整但部分函数未加注释，扣 1 分","status":"graded","confidence":"medium","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"多组测试数据与输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":17.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"含异常与边界分析","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"结构完整","status":"graded","confidence":"high","error_code":null}],"total_score":99.0,"warnings":[]}
```

### 第 3 次输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理阐述完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"算法描述与复杂度分析完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":20.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码行数充足，注释与核心函数齐全","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"多组测试数据与输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":17.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"含异常与边界分析","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"标题、编号与表格齐全","status":"graded","confidence":"high","error_code":null}],"total_score":100.0,"warnings":[]}
```

### 第 4 次输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"算法描述与复杂度分析完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":20.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码行数充足，含注释与核心函数","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"多组测试数据与输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":16.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"有异常说明，但对空链表边界分析的展开可更深入","status":"graded","confidence":"medium","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"标题、编号与表格齐全","status":"graded","confidence":"high","error_code":null}],"total_score":99.0,"warnings":[]}
```

### 第 5 次输出

```json
{"items":[{"item_id":1,"name":"实验目的与原理","max_score":10,"score":10.0,"level":"excellent","evidence":"掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用","reason":"实验目的明确，原理阐述完整","status":"graded","confidence":"high","error_code":null},{"item_id":2,"name":"实验环境与步骤","max_score":8,"score":8.0,"level":"excellent","evidence":"Windows 11，gcc 12.2，Visual Studio Code 1.85","reason":"环境项具体，步骤编号完整","status":"graded","confidence":"high","error_code":null},{"item_id":3,"name":"算法与数据结构设计","max_score":15,"score":15.0,"level":"excellent","evidence":"逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转每个节点的指向","reason":"算法描述与复杂度分析完整","status":"graded","confidence":"high","error_code":null},{"item_id":4,"name":"代码实现","max_score":20,"score":20.0,"level":"excellent","evidence":"// 尾插法插入","reason":"代码行数充足，含注释与核心函数","status":"graded","confidence":"high","error_code":null},{"item_id":5,"name":"测试与结果","max_score":15,"score":15.0,"level":"excellent","evidence":"依次插入 1、2、3、4、5","reason":"多组测试数据与输出","status":"graded","confidence":"high","error_code":null},{"item_id":6,"name":"结果与分析","max_score":17,"score":17.0,"level":"excellent","evidence":"异常情况：删除不存在的值时函数直接返回、不崩溃","reason":"含异常与边界分析","status":"graded","confidence":"high","error_code":null},{"item_id":7,"name":"报告规范","max_score":15,"score":15.0,"level":"excellent","evidence":"# 数据结构实验报告：单链表的实现与应用","reason":"标题、编号与表格齐全","status":"graded","confidence":"high","error_code":null}],"total_score":100.0,"warnings":[]}
```

### 连跑验证

1. 5 次输出 json.loads 全部成功：是（5/5）。
2. 每次 items 七项、十字段齐全：是。
3. 每次 total_score 等于各项之和：是（100 / 99 / 100 / 99 / 100）。
4. 每次 evidence 均能命中原文：是（5 次共 35 条 evidence 全部命中）。
5. 每次 warnings 为空数组：是。

---

## 结论

- 提示词能稳定产出合法 JSON：case_good 连跑 5 次 json.loads 全成功。
- evidence 约束有效：所有非 null 的 evidence 均为报告原文连续子串。
- total_score 自洽约束有效：所有输出 total_score 均等于分项之和。
- 跑题护栏有效：case_offtopic 全 0 分 + warnings，未硬评。
- 依据缺失处置有效：case_code_only 缺正文的 5 项判 absent + warnings 触发。

## 遗留观察（供 P2 任务 9 迭代参考）

1. case_good 连跑 5 次得分 100 / 99 / 100 / 99 / 100，波动 1 分，稳定性可用（可作为契约 consistency 字段的实测依据）。
2. case_good 满分说明当前 rubric 上端偏松：好报告基本全项满分，区分度集中在中等与差报告。待 C 用 10 份真实报告跑一遍看分布，若好报告集中在 95 分以上，任务 9 需要在优秀档内引入更细的锚点。
3. case_code_only 的 warnings 文案沿用了护栏 5 的「依据未能在原文中定位」，而该情形按 system 规则属于「找不到依据」，二者都成立但文案不统一，任务 9 可统一措辞。
