# 辅助函数模块

`botoy.contrib`模块封装了部分常用的操作函数

## `file_to_base64` 获取文件 base64 编码

## `get_cache_dir` 获取框架统一的缓存目录

## `RateLimit` 调用速率控制

```python
{!../docs_src/ratelimit.py!}
```

- 每个函数只能对应单独的`RateLimit`对象
