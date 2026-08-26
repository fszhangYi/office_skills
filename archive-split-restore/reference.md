# archive-split-restore 参考

## 与 autodl-tmp 旧脚本对照

| 脚本 | 行为 | 评价 |
|---|---|---|
| `splitter.py` | `open(..., 'rb')` 按字节切 `.gz`/`.tar` | ✅ 方向正确；整文件读入内存，大文件易 OOM |
| `gz_splitter.py` | `gzip.open` 解压后再切，块后缀 `.gzchunk` | ❌ 还原的「.gz」通常不是合法 gzip |
| `scripts/archive_split_restore.py` | 流式字节切分；多后缀；SHA256；兼容旧块名 | ✅ 推荐 |

## 元数据字段（v1）

```
original_name=...
original_filename=...
total_chunks=...
chunk_size_mb=...
total_size=...
original_extension=.tar.gz
chunk_ext=.archunk
sha256=...
format=raw-byte-split-v1
```

旧 `splitter.py` 可能还有 `file_type=gz|tar`；本工具 restore 时不依赖该字段，靠 `original_extension` 与块文件名。

## 旧块兼容

restore 按序查找：

1. `{name}.part{i:03d}{chunk_ext}`（metadata 中的 chunk_ext）  
2. `.gzchunk` / `.tarchunk` / `.archunk`  

## 为何不能「解压再切」

分片目标是**传输同一个归档文件**。若先解压，则：

- 体积往往更大  
- 合并结果不再是原 `.gz`/`.zip`  
- 对方无法用标准解压工具打开  

正确流程：`原归档 --split→ 分片 --restore→ 原归档 --(用户)→ tar/unzip`。
