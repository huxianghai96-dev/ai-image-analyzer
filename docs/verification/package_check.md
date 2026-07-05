# 打包清洁检查

## 背景

早期 Flet 构建产物 `build/flutter/app/app.zip` 曾包含 `.git/`、`test_samples/`、`test_samples_personal/` 等非交付内容，导致 APK 体积异常，也可能泄露测试或个人素材。

## 修复

`build_apk.py` 在 `flet build apk` 时通过 `--exclude` 排除非交付内容：

- 移除 `.git/`
- 移除 `.pytest_cache/`
- 移除 `build/`
- 移除 `docs/`
- 移除 `tests/`
- 移除 `test_samples/`
- 移除 `test_samples_personal/`
- 移除临时日志文件

构建完成后，脚本会检查 `build/flutter/app/app.zip` 和本次生成 APK 内的 `assets/flutter_assets/app/app.zip`。若发现上述路径，构建脚本会直接失败。

## 当前验证

执行命令：

```bash
python build_apk.py
```

预期结果摘要：

```text
Step 1: Running flet build apk...
flet build completed successfully.
Step 2: Validating generated APK package contents...
package check: clean
```

提交 APK 前请重新执行：

```bash
python build_apk.py
```
