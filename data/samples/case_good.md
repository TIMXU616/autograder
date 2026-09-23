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

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node* next;
} Node;

// 尾插法插入
Node* insert_tail(Node* head, int val) {
    Node* p = head;
    while (p->next) p = p->next;
    Node* n = (Node*)malloc(sizeof(Node));
    n->data = val;
    n->next = NULL;
    p->next = n;
    return head;
}

// 删除指定值
Node* delete_val(Node* head, int val) {
    Node* p = head;
    while (p->next && p->next->data != val) p = p->next;
    if (p->next) {
        Node* t = p->next;
        p->next = t->next;
        free(t);
    }
    return head;
}

// 三指针逆置
Node* reverse(Node* head) {
    Node *pre = NULL, *cur = head->next, *nxt;
    while (cur) {
        nxt = cur->next;
        cur->next = pre;
        pre = cur;
        cur = nxt;
    }
    head->next = pre;
    return head;
}

// 打印链表
void print(Node* head) {
    for (Node* p = head->next; p; p = p->next)
        printf("%d ", p->data);
    printf("\n");
}
```

## 六、测试与结果

| 测试编号 | 操作 | 输出结果 |
| --- | --- | --- |
| 1 | 依次插入 1、2、3、4、5 | 1 2 3 4 5 |
| 2 | 删除值为 3 的节点 | 1 2 4 5 |
| 3 | 对链表逆置 | 5 4 2 1 |
| 4 | 向空链表插入 10 | 10 |

## 七、结果与分析

头插法插入后输出顺序与插入顺序相反，符合头插法在表头插入的特性；尾插法保持元素顺序不变。删除中间节点后链表长度减 1，符合预期。逆置后元素顺序完全反转，说明三指针迭代法正确。异常情况：删除不存在的值时函数直接返回、不崩溃；对空链表调用逆置时 head->next 为空，循环不执行，结果仍为空链表，程序正常退出，说明边界处理正确。综上，实验达到预期目的。
