# 二叉树遍历程序

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node *l, *r;
} Node;

Node* newnode(int d) {
    Node* n = (Node*)malloc(sizeof(Node));
    n->data = d;
    n->l = n->r = NULL;
    return n;
}

void preorder(Node* root) {
    if (!root) return;
    printf("%d ", root->data);
    preorder(root->l);
    preorder(root->r);
}

void inorder(Node* root) {
    if (!root) return;
    inorder(root->l);
    printf("%d ", root->data);
    inorder(root->r);
}

void postorder(Node* root) {
    if (!root) return;
    postorder(root->l);
    postorder(root->r);
    printf("%d ", root->data);
}

int height(Node* root) {
    if (!root) return 0;
    int lh = height(root->l);
    int rh = height(root->r);
    return (lh > rh ? lh : rh) + 1;
}

int count(Node* root) {
    if (!root) return 0;
    return count(root->l) + count(root->r) + 1;
}

Node* search(Node* root, int key) {
    if (!root || root->data == key) return root;
    Node* left = search(root->l, key);
    if (left) return left;
    return search(root->r, key);
}

int main() {
    Node* root = newnode(1);
    root->l = newnode(2);
    root->r = newnode(3);
    root->l->l = newnode(4);
    root->l->r = newnode(5);
    root->r->l = newnode(6);
    root->r->r = newnode(7);

    printf("preorder: ");
    preorder(root);
    printf("\n");

    printf("inorder: ");
    inorder(root);
    printf("\n");

    printf("postorder: ");
    postorder(root);
    printf("\n");

    printf("height: %d\n", height(root));
    printf("count: %d\n", count(root));

    Node* p = search(root, 5);
    if (p) printf("found: %d\n", p->data);
    else printf("not found\n");

    return 0;
}
```
