# 18A媒体证据与18B播放打断实验

对应[学习章18](../../advanced/18-multimodal-and-realtime-agents.md)与[Q108–Q110](../../docs/advanced/18-multimodal-and-realtime-agents.md)。默认只用Python标准库，读取JSONL事件并执行状态机；浏览器演示实际播放本仓库合成的WAV文件。两条路径的证据分别报告。

```bash
python3 examples/multimodal_lab/lab.py --scenario all --output .local/multimodal_lab/all-report.json
python3 examples/multimodal_lab/lab.py --scenario correction
python3 -m unittest discover -s tests -p 'test_multimodal_lab.py' -v
```

场景为`normal`、`interim`、`correction`、`uncertain`和`interruption`。离线状态机在整个会话内保存已见generation及其取消/历史状态，同ID不能重开；先忽略旧代次/已取消代次事件，再按当前代次时长校验播放位置。测试覆盖旧4秒代次切换到新2秒代次后，旧3.8秒进度不得污染新状态或误报新媒体越界。`trace.jsonl`保留输入，`result.json`显示最终条件、来源与播放状态，`grade.json`对照独立`expected.json`。测试额外更换城市、日期、工具返回及媒体区域，核查旧结果失效和边界。

## 素材来源与可证明范围

- `assets/receipt.svg`是本手册原创的虚构教学票据，无真实身份或交易。金额区域在640×360画布中的`[80,180,460,70]`，单位为SVG坐标。
- `assets/playback-tone.wav`由`create_assets.py`生成：单声道、16kHz、16bit PCM、4秒提示音。运行`python3 examples/multimodal_lab/create_assets.py`可重新生成。
- JSONL中的金额观察、转写、政策返回均为人工构造夹具。提示音**没有说出那些文字**；音频时间片只用于练习关联关系，不能当作转写准确性的证据。
- 未运行OCR、ASR（自动语音识别）、视觉模型、TTS（文本转语音）或实时模型。离线通过只证明证据定位校验、条件更新、旧工具结果过滤、播放状态处理。

原创建材随仓库许可使用，不引入第三方录音。接入真实模型后，应另保存源媒体、识别输出、时间/区域对齐和人工核对，分别评测识别质量与业务结果。

## 真实浏览器播放

直接打开[player.html](player.html)，或在仓库根目录运行下面的本地服务，再访问`http://127.0.0.1:8768/examples/multimodal_lab/player.html`：

```bash
python3 -m http.server 8768 --bind 127.0.0.1
```

此命令保持运行，完成后用Ctrl+C退出。演示页只依赖`assets/playback-tone.wav`与`assets/receipt.svg`，没有外部脚本或数据上传。

操作顺序：播放→在进度中途暂停→继续→点击“模拟用户打断”→尝试继续→重置。暂停保留继续资格；打断取消当前generation（输出代次），必须重置后开始新输出。页面显示真实`HTMLMediaElement.currentTime`，打断时将其写入`history_seconds`；下载按钮导出该次浏览器事件日志。

验收应看到播放进度增长、暂停期间不继续增长、打断后历史上限小于完整4秒、取消后继续被拒绝。媒体时钟近似表示播放位置，不证明人实际听见；浏览器日志也不证明网络首音时延或语音自然度。CLI不会代替浏览器操作，因此报告明确`browser_playback_tested_by_cli=false`。

参考：[LiveKit轮次与打断](https://docs.livekit.io/agents/logic/turns/) · [WHATWG媒体元素与currentTime](https://html.spec.whatwg.org/multipage/media.html#media-elements)。
