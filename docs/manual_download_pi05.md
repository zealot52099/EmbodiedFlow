# 手动下载 Pi 0.5 权重说明

当前数据集已经下载完成，训练阻塞在 Pi 0.5 base checkpoint。

请从 Hugging Face 手动下载：

```text
https://huggingface.co/lerobot/pi05_libero_base/tree/main
```

放到本工程目录：

```text
E:\projects\robot\models\pi05_libero_base
```

必须包含：

```text
E:\projects\robot\models\pi05_libero_base\config.json
E:\projects\robot\models\pi05_libero_base\model.safetensors
E:\projects\robot\models\pi05_libero_base\policy_preprocessor.json
E:\projects\robot\models\pi05_libero_base\policy_postprocessor.json
```

`model.safetensors` 预期大小：

```text
14,467,165,872 bytes
```

如果当前自动下载还在跑，可以用下面命令观察进度：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch_pi05_download.ps1
```

可选但建议保留：

```text
E:\projects\robot\models\pi05_libero_base\README.md
E:\projects\robot\models\pi05_libero_base\.gitattributes
```

下载后运行完整性检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_pi05_task.ps1
```

检查通过后跑 1-step smoke train：

```powershell
conda run -p E:\Project\lerobot_experiment\envs\lerobot312 powershell -ExecutionPolicy Bypass -File .\scripts\run_smoke_train_pi05.ps1
```

再跑正式训练：

```powershell
conda run -p E:\Project\lerobot_experiment\envs\lerobot312 powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_4090.ps1
```

如果训练时报 `google/paligemma-3b-pt-224` tokenizer 下载失败，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_local_paligemma_tokenizer.ps1
```
