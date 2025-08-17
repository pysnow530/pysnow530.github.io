# 自述文件

项目基于 `hexo`, 需要安装 `hexo` 环境.

## 分支说明

`master`: 用于存放编译后的文件, 禁止手动修改.
`develop`: 用于存放源文件, 新的博客在该分支下编辑, 编译后存放到 master 分支.

## 发布说明

`develop` 分支下:

```sh
# 环境初始化
npm install

# 在线运行
hexo server
open http://localhost:4000

# 编译文件
hexo generate
```
