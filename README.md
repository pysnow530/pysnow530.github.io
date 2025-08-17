# 自述文件

项目基于 `hexo`, 需要安装 `hexo` 环境.

## 分支说明

`master`: 用于存放编译后的文件, 禁止手动修改.
`develop`: 用于存放源文件, 新的博客在该分支下编辑, 编译后存放到 master 分支.

## 发布说明

新文章在 `develop` 分支的 `sources/_posts/` 下创建, 格式为 `2025-08-17-article-title.md`

`develop` 分支下:

```sh
# 环境初始化
npm install

# 在线运行
hexo server
open http://localhost:4000

# 发布
hexo generate
copy public/* to master/*
```
